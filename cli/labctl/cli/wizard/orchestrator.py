"""
Enhanced init wizard orchestrator (Phase 2).

New flow:
  1. Profile selection
  2. Core settings (domain + email)
  3. Category-by-category enable/disable — "Enable [Postgres / Redis / MongoDB]? (y/N)"
  4. For each enabled service: field-level prompts with defaults shown, secrets auto-generated
  5. Dual-write: non-secret config → config.yaml,  secrets → .env
  6. Summary: "Enabled: traefik, postgres, grafana. Disabled: 13 others."

Re-running is safe — existing values shown as defaults.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.table import Table

from ...core.services import (
    DependencyGraph,
    ServiceSchema,
    get_service_categories,
)
from .prompter import ask_field, display_field_summary, generate_password

console = Console()

# ── Helpers ───────────────────────────────────────────────────────────────────

_SECRET_KEYWORDS = ("password", "token", "secret", "key", "pass", "api_key")


def _is_secret_field(key: str) -> bool:
    k = key.lower()
    return any(w in k for w in _SECRET_KEYWORDS)


def _env_var_name(service_id: str, field_key: str) -> str:
    """Convert service_id + field_key → UPPER_SNAKE_CASE env var name."""
    return f"{service_id.upper()}_{field_key.upper()}"


# ── Session ───────────────────────────────────────────────────────────────────


class WizardSession:
    """Holds all state accumulated during the wizard run."""

    def __init__(self, profile: str = "prod"):
        self.profile = profile
        self.schemas: Dict[str, ServiceSchema] = {}
        self.selected_services: Set[str] = set()
        self.resolved_services: List[str] = []
        # field values (non-secret + secret, for internal use)
        self.service_configs: Dict[str, Dict[str, Any]] = {}
        # {ENV_VAR: value}  — secret fields extracted for .env
        self.env_vars: Dict[str, str] = {}
        # {service_id: {KEY: val}}  — custom env vars added by the user
        self.custom_env: Dict[str, Dict[str, str]] = {}
        self.global_context: Dict[str, Any] = {}

    # ── Profile helpers ───────────────────────────────────────────────────

    def get_profile_defaults(self, service_id: str) -> Dict[str, Any]:
        schema = self.schemas.get(service_id)
        if not schema or not schema.defaults:
            return {}
        if self.profile == "dev" and schema.defaults.dev:
            return schema.defaults.dev
        if self.profile == "prod" and schema.defaults.prod:
            return schema.defaults.prod
        return {}


# ── Step helpers ──────────────────────────────────────────────────────────────


def _select_profile(preset: Optional[str]) -> str:
    if preset:
        return "dev" if preset in ("dev", "development") else "prod"
    console.print("\n[bold]📋 Deployment Profile[/bold]")
    console.print("  • [cyan]prod[/cyan] — production certificates, optimised settings (default)")
    console.print("  • [cyan]dev[/cyan]  — staging certificates, debug logging, lighter resources")
    choice = Prompt.ask(
        "Profile",
        choices=["prod", "dev", "production", "development"],
        default="prod",
        show_choices=False,
    )
    return "dev" if choice in ("dev", "development") else "prod"


def _collect_core(existing: Dict[str, Any]) -> Dict[str, Any]:
    console.print("\n[bold]🌐 Core Settings[/bold]")
    domain = Prompt.ask(
        "Primary domain  [dim](e.g. homelab.example.com)[/dim]",
        default=existing.get("domain", "homelab.local"),
        show_default=False,
    )
    email = Prompt.ask(
        "Admin email     [dim](for Let's Encrypt + alerts)[/dim]",
        default=existing.get("email", "admin@example.com"),
        show_default=False,
    )
    return {"domain": domain, "email": email}


def _select_by_category(
    schemas: Dict[str, ServiceSchema],
    already_enabled: Set[str],
    non_interactive: bool,
) -> Set[str]:
    """
    For each category, show the services it contains and ask "Enable?" per service.
    Returns the set of service IDs the user said yes to.
    """
    categories = get_service_categories(schemas)
    selected: Set[str] = set()

    console.print("\n[bold]📦 Service Selection[/bold]")
    console.print(
        "[dim]You'll be asked about each category. Press Enter to accept the default.[/dim]\n"
    )

    for category, service_ids in sorted(categories.items()):
        # Category header
        console.print(f"[bold cyan]── {category} ──[/bold cyan]")

        for sid in sorted(service_ids):
            schema = schemas[sid]
            default_enabled = sid in already_enabled or bool(
                schema.defaults
                and (
                    getattr(schema.defaults, "prod", {}) or {}
                ).get("enabled", False)
            )
            dep_note = (
                f"  [dim](requires: {', '.join(schema.dependencies)})[/dim]"
                if schema.dependencies
                else ""
            )
            prompt_text = (
                f"  Enable [white]{schema.name}[/white]"
                f"  [dim]{schema.description}[/dim]{dep_note}"
            )

            if non_interactive:
                if default_enabled:
                    selected.add(sid)
                continue

            if Confirm.ask(prompt_text, default=default_enabled):
                selected.add(sid)

        console.print()

    return selected


def _configure_service(
    service_id: str,
    schema: ServiceSchema,
    session: WizardSession,
    existing_config: Dict[str, Any],
    service: Optional[str] = None,
) -> tuple[Dict[str, Any], Dict[str, str]]:
    """
    Interactively configure a single service.

    Returns:
        (non_secret_config, secret_env_vars)
    """
    console.print(f"\n{'─' * 60}")
    console.print(f"[bold blue]⚙  Configuring {schema.name}[/bold blue]")
    if schema.description:
        console.print(f"[dim]{schema.description}[/dim]")
    console.print("─" * 60)

    context = {**session.global_context}
    profile_defaults = session.get_profile_defaults(service_id)
    context.update(profile_defaults)

    # Existing values become defaults
    context.update(existing_config)

    # Inject peer service configs for cross-service conditionals
    for peer_id, peer_cfg in session.service_configs.items():
        for k, v in peer_cfg.items():
            context[f"{peer_id}.{k}"] = v

    plain_config: Dict[str, Any] = {"enabled": True}
    secret_vars: Dict[str, str] = {}

    for field in schema.fields:
        if field.key == "enabled":
            continue
        try:
            value = ask_field(field, context)
            context[field.key] = value

            if _is_secret_field(field.key) and value:
                env_key = _env_var_name(service_id, field.key)
                secret_vars[env_key] = str(value)
                # In config.yaml, store a reference instead of the literal
                plain_config[field.key] = f"${{{env_key}}}"
            else:
                plain_config[field.key] = value

        except KeyboardInterrupt:
            console.print(f"\n[yellow]Skipped remaining fields for {schema.name}[/yellow]")
            break
        except Exception as exc:
            console.print(f"[red]Error on field '{field.key}': {exc}[/red]")
            plain_config[field.key] = field.default

    display_field_summary({k: v for k, v in plain_config.items() if k != "enabled"}, schema.name)
    return plain_config, secret_vars


def _resolve_with_display(
    selected: Set[str], schemas: Dict[str, ServiceSchema]
) -> List[str]:
    console.print("\n[bold]🔗 Resolving dependencies…[/bold]")
    graph = DependencyGraph(schemas)
    resolved = graph.resolve_dependencies(list(selected))

    auto_added = set(resolved) - selected
    if auto_added:
        console.print("[yellow]Auto-adding required dependencies:[/yellow]")
        for sid in sorted(auto_added):
            console.print(f"  • [yellow]{schemas[sid].name}[/yellow]")

    enabled_names = [schemas[sid].name for sid in resolved if sid in selected or sid in auto_added]
    console.print(
        f"[green]✓ {len(resolved)} service(s) to configure: {', '.join(enabled_names)}[/green]"
    )
    return resolved


def _print_summary(
    session: WizardSession,
    schemas: Dict[str, ServiceSchema],
) -> None:
    enabled = [
        sid
        for sid in session.resolved_services
        if session.service_configs.get(sid, {}).get("enabled")
    ]
    all_ids = set(schemas.keys())
    disabled = sorted(all_ids - set(enabled))

    console.print("\n[bold]📋 Configuration Summary[/bold]")

    table = Table(show_header=True, header_style="bold cyan", box=None)
    table.add_column("Service", style="white", width=22)
    table.add_column("Status", width=12)
    table.add_column("Key Settings", style="dim")

    for sid in sorted(enabled):
        cfg = session.service_configs.get(sid, {})
        schema = schemas.get(sid)
        if not schema:
            continue
        settings = [
            f"{k}={v}"
            for k, v in cfg.items()
            if k not in ("enabled",) and not _is_secret_field(k) and v is not None
        ][:3]
        table.add_row(schema.name, "[green]✓ enabled[/green]", "; ".join(settings))

    for sid in disabled:
        schema = schemas.get(sid)
        if schema:
            table.add_row(schema.name, "[dim]disabled[/dim]", "")

    console.print(table)

    console.print(
        f"\n[bold]Enabled:[/bold] {', '.join(schemas[s].name for s in sorted(enabled)) or 'none'}"
    )
    console.print(
        f"[bold]Disabled:[/bold] {len(disabled)} service(s)"
    )
    if session.env_vars:
        console.print(f"\n[dim]🔐 {len(session.env_vars)} secret(s) will be written to .env[/dim]")


# ── Public class ──────────────────────────────────────────────────────────────


class WizardOrchestrator:
    """
    Main orchestrator for labctl init.

    Usage::

        orch = WizardOrchestrator(schemas)
        config_data = orch.run_wizard(profile="prod")
        # config_data["env_vars"] → write to .env
        # rest                    → write to config.yaml
    """

    def __init__(self, schemas: Dict[str, ServiceSchema]):
        self.schemas = schemas

    # ── Single-service reconfigure (--service flag) ────────────────────────

    def run_single_service(
        self,
        service_id: str,
        existing_config: Dict[str, Any],
        profile: str = "prod",
    ) -> tuple[Dict[str, Any], Dict[str, str]]:
        """Re-configure just one service, returning (config, env_vars)."""
        if service_id not in self.schemas:
            raise ValueError(f"Unknown service: {service_id}")
        schema = self.schemas[service_id]
        session = WizardSession(profile)
        session.schemas = self.schemas
        session.global_context = existing_config.get("core", {})
        cfg, env = _configure_service(
            service_id,
            schema,
            session,
            existing_config.get("services", {}).get(service_id, {}),
        )
        return cfg, env

    # ── Full wizard ────────────────────────────────────────────────────────

    def run_wizard(
        self,
        profile: Optional[str] = None,
        existing_config: Optional[Dict[str, Any]] = None,
        non_interactive: bool = False,
        single_service: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the full interactive wizard.

        Returns a dict with keys:
          version, profile, core, services, custom_env, env_vars
        """
        existing = existing_config or {}
        ex_services = existing.get("services", {})
        ex_core = existing.get("core", {})

        try:
            console.print(
                Panel.fit(
                    "🏠 [bold blue]Home Lab Setup Wizard v2[/bold blue]\n\n"
                    "[dim]Category-by-category service selection.\n"
                    "Existing values are shown as defaults — press Enter to keep them.[/dim]",
                    border_style="blue",
                )
            )

            session = WizardSession()
            session.schemas = self.schemas

            # --- Single-service shortcut ---
            if single_service:
                session.profile = profile or "prod"
                session.global_context = ex_core
                cfg, env = _configure_service(
                    single_service,
                    self.schemas[single_service],
                    session,
                    ex_services.get(single_service, {}),
                )
                result = dict(existing)
                result.setdefault("services", {})[single_service] = cfg
                result.setdefault("env_vars", {}).update(env)
                return result

            # --- Profile ---
            if not non_interactive:
                session.profile = _select_profile(profile)
            else:
                session.profile = profile or "prod"

            # --- Core ---
            if not non_interactive:
                core = _collect_core(ex_core)
            else:
                core = {
                    "domain": ex_core.get("domain", "homelab.local"),
                    "email": ex_core.get("email", "admin@homelab.local"),
                }
            session.global_context = core

            # --- Category-based selection ---
            already_enabled: Set[str] = {
                sid for sid, cfg in ex_services.items()
                if isinstance(cfg, dict) and cfg.get("enabled")
            }

            if not non_interactive:
                selected = _select_by_category(self.schemas, already_enabled, non_interactive=False)
            else:
                # Non-interactive: keep existing enabled set, or default minimal stack
                selected = already_enabled or {"traefik", "postgresql", "redis", "monitoring"}
                selected = {s for s in selected if s in self.schemas}

            if not selected:
                raise ValueError("No services selected — cancelling.")

            session.selected_services = selected

            # --- Dependency resolution ---
            session.resolved_services = _resolve_with_display(selected, self.schemas)

            # --- Per-service configuration ---
            for sid in session.resolved_services:
                schema = self.schemas[sid]
                existing_svc = ex_services.get(sid, {})

                if non_interactive:
                    # Use profile defaults, don't prompt
                    defaults = session.get_profile_defaults(sid)
                    plain_cfg = {"enabled": True, **defaults}
                    env_vars: Dict[str, str] = {}
                    # Auto-generate secrets
                    for field in schema.fields:
                        if field.key == "enabled":
                            continue
                        if _is_secret_field(field.key) and field.generate:
                            length = getattr(field, "length", 32) or 32
                            val = generate_password(length)
                            env_key = _env_var_name(sid, field.key)
                            env_vars[env_key] = val
                            plain_cfg[field.key] = f"${{{env_key}}}"
                else:
                    plain_cfg, env_vars = _configure_service(sid, schema, session, existing_svc)

                session.service_configs[sid] = plain_cfg
                session.env_vars.update(env_vars)

            # --- Summary + confirm ---
            _print_summary(session, self.schemas)

            if not non_interactive:
                if not Confirm.ask("\n💾 Save this configuration?", default=True):
                    raise ValueError("Configuration not confirmed — not saved.")

            return self._build_output(session, core)

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Wizard cancelled by user[/yellow]")
            raise

    # ── Internal ──────────────────────────────────────────────────────────

    def _build_output(self, session: WizardSession, core: Dict[str, Any]) -> Dict[str, Any]:
        """Convert session → config dict ready for saving."""
        return {
            "version": 2,
            "profile": session.profile,
            "core": core,
            "services": {
                sid: cfg
                for sid, cfg in session.service_configs.items()
                if cfg
            },
            "custom_env": session.custom_env,
            "env_vars": session.env_vars,
        }
