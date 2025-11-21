"""
Wizard Orchestrator

This module coordinates the entire interactive configuration flow,
from service selection to final configuration summary.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from ...core.services import (
    DependencyGraph,
    ServiceSchema,
    get_service_categories,
    load_service_schemas,
    resolve_with_dependencies,
)
from .prompter import ask_custom_environment_variables, ask_field, display_field_summary

console = Console()


class WizardSession:
    """
    Manages the configuration session state and context
    """

    def __init__(self, profile: str = "prod"):
        self.profile = profile
        self.schemas: Dict[str, ServiceSchema] = {}
        self.selected_services: Set[str] = set()
        self.resolved_services: List[str] = []
        self.service_configs: Dict[str, Dict[str, Any]] = {}
        self.custom_env: Dict[str, Dict[str, str]] = {}
        self.global_context: Dict[str, Any] = {}

    def load_schemas(self, schemas_dir: Path) -> None:
        """Load service schemas"""
        self.schemas = load_service_schemas(schemas_dir)
        console.print(f"[green]Loaded {len(self.schemas)} service schemas[/green]")

    def set_global_context(self, context: Dict[str, Any]) -> None:
        """Set global context values (like domain)"""
        self.global_context.update(context)

    def get_profile_defaults(self, service_id: str) -> Dict[str, Any]:
        """Get profile-specific defaults for a service"""
        schema = self.schemas.get(service_id)
        if not schema or not schema.defaults:
            return {}

        if self.profile == "dev" and schema.defaults.dev:
            return schema.defaults.dev
        elif self.profile == "prod" and schema.defaults.prod:
            return schema.defaults.prod

        return {}

    def is_service_enabled(self, service_id: str) -> bool:
        """Check if a service is enabled"""
        return self.service_configs.get(service_id, {}).get("enabled", False)


def display_welcome() -> None:
    """Display welcome message"""
    welcome_text = """
🏠 [bold blue]Enterprise Home Lab Configuration Wizard[/bold blue] 🏠

Welcome to the interactive service configuration wizard!
This will guide you through selecting and configuring 
your home lab infrastructure services.

Features:
• Service-specific configuration with validation
• Automatic dependency resolution
• Secure password generation
• Profile-based defaults (development vs production)
• Beautiful interactive experience
    """.strip()

    console.print(Panel(welcome_text, border_style="blue", padding=(1, 2)))


def select_profile() -> str:
    """Select deployment profile"""
    console.print("\n[bold]📋 Profile Selection[/bold]")
    console.print("Choose your deployment profile:")
    console.print(
        "• [cyan]Development[/cyan] - Staging certificates, debug logging, lower resource usage"
    )
    console.print(
        "• [cyan]Production[/cyan] - Production certificates, optimized settings, higher security"
    )

    profile_choice = Prompt.ask(
        "Profile",
        choices=["dev", "prod", "development", "production"],
        default="prod",
        show_choices=False,
        console=console,
    )

    # Normalize profile names
    if profile_choice in ["dev", "development"]:
        return "dev"
    else:
        return "prod"


def display_service_categories(schemas: Dict[str, ServiceSchema]) -> None:
    """Display available services grouped by category"""
    categories = get_service_categories(schemas)

    console.print("\n[bold]📦 Available Services[/bold]")

    for category, service_ids in categories.items():
        console.print(f"\n[bold cyan]{category}:[/bold cyan]")

        for service_id in sorted(service_ids):
            schema = schemas[service_id]
            deps_text = (
                f" [dim](depends on: {', '.join(schema.dependencies)})[/dim]"
                if schema.dependencies
                else ""
            )
            maturity_badge = ""

            if schema.maturity == "alpha":
                maturity_badge = " [red][ALPHA][/red]"
            elif schema.maturity == "beta":
                maturity_badge = " [yellow][BETA][/yellow]"

            console.print(
                f"  • [white]{schema.name}[/white]{maturity_badge} - {schema.description}{deps_text}"
            )


def select_services(schemas: Dict[str, ServiceSchema]) -> Set[str]:
    """Interactive service selection"""
    display_service_categories(schemas)

    console.print("\n[bold]🎯 Service Selection[/bold]")
    console.print("[dim]Select services by entering their IDs (space-separated):[/dim]")
    console.print("[dim]Example: traefik postgresql nextcloud[/dim]")

    available_ids = list(schemas.keys())
    console.print(
        f"\n[dim]Available service IDs: {', '.join(sorted(available_ids))}[/dim]"
    )

    while True:
        try:
            selection_input = Prompt.ask(
                "Selected services", default="traefik", console=console
            )

            selected = set(selection_input.split())

            # Validate all services exist
            invalid_services = selected - set(available_ids)
            if invalid_services:
                console.print(
                    f"[red]Error: Unknown services: {', '.join(invalid_services)}[/red]"
                )
                console.print(
                    f"[dim]Available: {', '.join(sorted(available_ids))}[/dim]"
                )
                continue

            if not selected:
                console.print("[red]Error: At least one service must be selected[/red]")
                continue

            return selected

        except KeyboardInterrupt:
            console.print("\n[yellow]Selection cancelled[/yellow]")
            return set()


def resolve_dependencies(
    selected: Set[str], schemas: Dict[str, ServiceSchema]
) -> List[str]:
    """Resolve and display service dependencies"""
    console.print("\n[bold]🔗 Dependency Resolution[/bold]")

    graph = DependencyGraph(schemas)
    resolved = graph.resolve_dependencies(list(selected))

    # Show what was added
    auto_added = set(resolved) - selected
    if auto_added:
        console.print("[yellow]Automatically added dependencies:[/yellow]")
        for service_id in sorted(auto_added):
            schema = schemas[service_id]
            console.print(f"  • [yellow]{schema.name}[/yellow] - {schema.description}")

    # Display final service list in dependency order
    console.print(f"\n[green]✓ Final service list ({len(resolved)} services):[/green]")
    for i, service_id in enumerate(resolved, 1):
        schema = schemas[service_id]
        console.print(f"  {i}. [cyan]{schema.name}[/cyan]")

    return resolved


def configure_service(
    service_id: str, schema: ServiceSchema, session: WizardSession
) -> Dict[str, Any]:
    """Configure a single service interactively"""
    console.print(f"\n" + "=" * 60)
    console.print(f"[bold blue]⚙️  Configuring {schema.name}[/bold blue]")
    console.print(f"[dim]{schema.description}[/dim]")
    console.print("=" * 60)

    # Build context for this service
    context = session.global_context.copy()
    profile_defaults = session.get_profile_defaults(service_id)
    context.update(profile_defaults)

    # Add other services' config to context for conditional fields
    for other_service, other_config in session.service_configs.items():
        for key, value in other_config.items():
            context[f"{other_service}.{key}"] = value

    service_config = {}

    # Process fields in order
    for field in schema.fields:
        try:
            # Apply profile defaults
            if field.key in profile_defaults:
                context[field.key] = profile_defaults[field.key]

            value = ask_field(field, context)
            service_config[field.key] = value
            context[field.key] = value

        except KeyboardInterrupt:
            console.print(
                f"\n[yellow]Configuration of {schema.name} cancelled[/yellow]"
            )
            return {}
        except Exception as e:
            console.print(f"[red]Error configuring field '{field.key}': {e}[/red]")
            service_config[field.key] = field.default

    # Ask for custom environment variables
    try:
        custom_env = ask_custom_environment_variables()
        if custom_env:
            session.custom_env[service_id] = custom_env
    except KeyboardInterrupt:
        console.print("\n[yellow]Custom environment variables skipped[/yellow]")

    # Show configuration summary
    display_field_summary(service_config, schema.name)

    return service_config


def show_configuration_summary(session: WizardSession) -> None:
    """Display complete configuration summary"""
    console.print("\n" + "=" * 80)
    console.print("[bold green]📋 Complete Configuration Summary[/bold green]")
    console.print("=" * 80)

    console.print(f"[bold]Profile:[/bold] {session.profile}")
    console.print(f"[bold]Services:[/bold] {len(session.service_configs)}")

    # Create summary table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Service", style="white", width=20)
    table.add_column("Status", width=10)
    table.add_column("Key Settings", style="dim")

    for service_id in session.resolved_services:
        config = session.service_configs.get(service_id, {})
        schema = session.schemas.get(service_id)

        if not config or not schema:
            continue

        # Determine status
        enabled = config.get("enabled", False)
        status = "[green]✓ Enabled[/green]" if enabled else "[red]✗ Disabled[/red]"

        # Key settings (non-sensitive)
        key_settings = []
        for key, value in config.items():
            if key == "enabled":
                continue
            if (
                "password" in key.lower()
                or "token" in key.lower()
                or "secret" in key.lower()
            ):
                if value:
                    key_settings.append(f"{key}: [dim]●●●●●●●●[/dim]")
            else:
                if isinstance(value, bool):
                    key_settings.append(f"{key}: {'Yes' if value else 'No'}")
                elif isinstance(value, list):
                    key_settings.append(
                        f"{key}: {', '.join(value) if value else 'none'}"
                    )
                elif value:
                    key_settings.append(f"{key}: {value}")

        settings_text = "; ".join(key_settings[:3])  # Limit to first 3 settings
        if len(key_settings) > 3:
            settings_text += f" (+{len(key_settings) - 3} more)"

        table.add_row(schema.name, status, settings_text)

    console.print(table)

    # Show custom environment variables summary
    if session.custom_env:
        console.print(f"\n[bold]Custom Environment Variables:[/bold]")
        for service_id, env_vars in session.custom_env.items():
            schema = session.schemas.get(service_id)
            if schema and env_vars:
                console.print(f"  • {schema.name}: {len(env_vars)} variables")


def confirm_configuration(session: WizardSession) -> bool:
    """Confirm the configuration before saving"""
    console.print("\n[bold]💾 Save Configuration?[/bold]")

    if not Confirm.ask("Save this configuration?", default=True, console=console):
        return False

    # Option to edit specific services
    while Confirm.ask(
        "Edit any service configuration?", default=False, console=console
    ):
        service_names = [session.schemas[sid].name for sid in session.resolved_services]
        console.print(f"Services: {', '.join(service_names)}")

        service_input = Prompt.ask("Service ID to edit", console=console)
        if service_input in session.schemas:
            schema = session.schemas[service_input]
            session.service_configs[service_input] = configure_service(
                service_input, schema, session
            )
        else:
            console.print(f"[red]Unknown service: {service_input}[/red]")

    return True


def run_wizard(
    schemas_dir: Path, profile: Optional[str] = None
) -> Optional[WizardSession]:
    """
    Run the complete configuration wizard

    Args:
        schemas_dir: Directory containing service schemas
        profile: Optional profile override

    Returns:
        WizardSession with complete configuration, or None if cancelled
    """
    try:
        display_welcome()

        # Initialize session
        session = WizardSession()
        session.load_schemas(schemas_dir)

        if not session.schemas:
            console.print("[red]Error: No service schemas found[/red]")
            return None

        # Select profile
        if not profile:
            profile = select_profile()
        session.profile = profile
        console.print(f"[green]✓ Selected profile: {profile}[/green]")

        # Select services
        selected = select_services(session.schemas)
        if not selected:
            return None

        session.selected_services = selected

        # Resolve dependencies
        session.resolved_services = resolve_dependencies(selected, session.schemas)

        # Configure each service
        for service_id in session.resolved_services:
            schema = session.schemas[service_id]
            config = configure_service(service_id, schema, session)
            session.service_configs[service_id] = config

            # Skip remaining if this service was cancelled
            if not config:
                console.print("[yellow]Configuration cancelled[/yellow]")
                return None

        # Show summary and confirm
        show_configuration_summary(session)

        if not confirm_configuration(session):
            console.print("[yellow]Configuration not saved[/yellow]")
            return None

        console.print(
            "\n[bold green]✅ Configuration completed successfully![/bold green]"
        )
        return session

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Wizard cancelled by user[/yellow]")
        return None
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        return None


def create_dependency_tree_display(session: WizardSession) -> None:
    """Display service dependencies as a tree"""
    console.print("\n[bold]🌳 Service Dependency Tree[/bold]")

    graph = DependencyGraph(session.schemas)
    tree = Tree("Services")

    # Find root services (no dependencies within selected set)
    selected_set = set(session.resolved_services)
    roots = []

    for service_id in session.resolved_services:
        deps = graph.get_dependencies(service_id) & selected_set
        if not deps:
            roots.append(service_id)

    def add_service_branch(parent_tree, service_id: str, visited: Set[str]):
        if service_id in visited:
            parent_tree.add(f"[dim]{session.schemas[service_id].name} (circular)[/dim]")
            return

        visited.add(service_id)
        schema = session.schemas[service_id]
        enabled = session.is_service_enabled(service_id)
        status = "[green]✓[/green]" if enabled else "[red]✗[/red]"

        service_branch = parent_tree.add(f"{status} [cyan]{schema.name}[/cyan]")

        # Add dependents
        dependents = graph.get_dependents(service_id) & selected_set
        for dependent in sorted(dependents):
            add_service_branch(service_branch, dependent, visited.copy())

    # Add root services to tree
    for root in sorted(roots):
        add_service_branch(tree, root, set())

    console.print(tree)


class WizardOrchestrator:
    """
    Main orchestrator class for the configuration wizard
    """

    def __init__(self, schemas: Dict[str, ServiceSchema]):
        self.schemas = schemas

    def run_wizard(self, profile: Optional[str] = None) -> dict:
        """
        Run the complete configuration wizard and return config data

        Args:
            profile: Optional profile override (dev/prod)

        Returns:
            Configuration dictionary ready for saving
        """
        try:
            display_welcome()

            # Initialize session
            session = WizardSession()
            session.schemas = self.schemas

            if not session.schemas:
                console.print("[red]Error: No service schemas found[/red]")
                raise ValueError("No service schemas available")

            # Select profile
            if not profile:
                profile = select_profile()
            session.profile = profile
            console.print(f"[green]✓ Selected profile: {profile}[/green]")

            # Core configuration
            console.print("\n[bold]🌐 Core Configuration[/bold]")
            domain = Prompt.ask(
                "Primary domain", default="homelab.local", console=console
            )

            email = Prompt.ask(
                "Admin email", default="admin@example.com", console=console
            )

            session.set_global_context(
                {"domain": domain, "email": email, "profile": profile}
            )

            # Select services
            selected = select_services(session.schemas)
            if not selected:
                raise ValueError("No services selected")

            session.selected_services = selected

            # Resolve dependencies
            session.resolved_services = resolve_dependencies(selected, session.schemas)

            # Configure each service
            for service_id in session.resolved_services:
                schema = session.schemas[service_id]
                config = configure_service(service_id, schema, session)
                session.service_configs[service_id] = config

                # Skip remaining if this service was cancelled
                if not config:
                    console.print("[yellow]Configuration cancelled[/yellow]")
                    raise ValueError("Configuration cancelled")

            # Show summary and confirm
            show_configuration_summary(session)

            if not confirm_configuration(session):
                console.print("[yellow]Configuration not saved[/yellow]")
                raise ValueError("Configuration not confirmed")

            # Convert session to config format
            config_data = self._session_to_config(session)

            console.print(
                "\n[bold green]✅ Configuration completed successfully![/bold green]"
            )
            return config_data

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Wizard cancelled by user[/yellow]")
            raise
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
            raise

    def _session_to_config(self, session: WizardSession) -> dict:
        """
        Convert wizard session to configuration dictionary format

        Args:
            session: Completed wizard session

        Returns:
            Configuration dictionary
        """
        config_data = {
            "version": 2,
            "profile": session.profile,
            "core": session.global_context,
            "services": {},
            "custom_env": session.custom_env,
            "env_vars": {},
        }

        # Convert service configs
        for service_id, service_config in session.service_configs.items():
            if service_config:  # Skip empty configs
                config_data["services"][service_id] = service_config

        # Extract environment variables that should go to .env
        env_vars = {}
        for service_id, service_config in session.service_configs.items():
            for field_key, field_value in service_config.items():
                # Check if this field should generate an environment variable
                if isinstance(field_value, str) and field_value.startswith("$("):
                    # This is a placeholder for generated value
                    if "password" in field_key.lower():
                        env_key = f"{service_id.upper()}_{field_key.upper()}"
                        env_vars[env_key] = "$(generate_password)"

        # Add some common generated passwords
        if "postgresql" in session.service_configs:
            env_vars["POSTGRES_PASSWORD"] = "$(generate_password)"
        if "redis" in session.service_configs:
            env_vars["REDIS_PASSWORD"] = "$(generate_password)"
        if "monitoring" in session.service_configs:
            env_vars["GRAFANA_ADMIN_PASSWORD"] = "$(generate_password)"

        config_data["env_vars"] = env_vars

        return config_data
