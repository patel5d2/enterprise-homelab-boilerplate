# Architecture

How the Enterprise Home Lab CLI is structured internally.

---

## Module Map

```
enterprise-homelab-boilerplate/
├── bootstrap.sh              ← ONE-command fresh-machine setup
├── Makefile                  ← make bootstrap / make doctor / make test
├── labctl                    ← project-local launcher (activates venv)
│
├── cli/labctl/
│   ├── cli/
│   │   ├── main.py           ← Typer app, command registration
│   │   ├── commands/
│   │   │   ├── init_cmd.py   ← labctl init  (Phase 2 wizard driver)
│   │   │   ├── doctor_cmd.py ← labctl doctor (Phase 3 health checks)
│   │   │   ├── build_cmd.py  ← labctl build  (compose generation)
│   │   │   ├── deploy_cmd.py ← labctl deploy (docker compose up)
│   │   │   ├── validate_cmd.py
│   │   │   └── ...
│   │   └── wizard/
│   │       ├── orchestrator.py  ← WizardOrchestrator (category flow)
│   │       └── prompter.py      ← field-level Rich prompts + validation
│   │
│   └── core/
│       ├── config.py         ← Pydantic v2 models (LabConfig, services…)
│       ├── config_writer.py  ← save_config_to_yaml
│       ├── compose.py        ← schema → docker-compose.yml generator
│       ├── secrets.py        ← .env read/write helpers
│       ├── health.py         ← service healthcheck utilities
│       └── services/
│           ├── schema.py     ← load_service_schemas, ServiceSchema model
│           ├── deps.py       ← DependencyGraph, resolve_with_dependencies
│           └── __init__.py
│
├── config/
│   ├── config.yaml           ← user config (written by labctl init)
│   └── services-v2/          ← 17 service schema YAML files
│       ├── SCHEMA.md         ← schema DSL reference
│       ├── traefik.yaml
│       ├── postgresql.yaml
│       └── ...
│
└── tests/
    ├── test_services_v2.py
    ├── test_doctor.py
    └── test_init.py
```

---

## Data Flow

### `labctl init` → config.yaml + .env

```
User input
    │
    ▼
WizardOrchestrator.run_wizard()
    │  reads schemas from config/services-v2/*.yaml
    │  prompts by category
    │  resolves dependencies (DependencyGraph)
    │  collects field values per service
    │
    ├──▶ Non-secret fields ──▶ config/config.yaml
    └──▶ Secret fields     ──▶ .env  (merged, never overwrites existing)
```

### `labctl build` → docker-compose.yml

```
config/config.yaml  +  config/services-v2/*.yaml  +  .env
         │
         ▼
    core/compose.py  (ComposeGenerator)
         │
         ▼
    config/compose/docker-compose.yml
```

### `labctl deploy`

```
docker compose -f config/compose/docker-compose.yml up -d
```

---

## Configuration Models

Two Pydantic v2 model trees coexist (legacy migration is deferred):

| Class | Location | Used by |
|---|---|---|
| `LabConfig` | `core/config.py` | v2 schema pipeline, compose generator |
| `Config` (legacy) | `core/config.py` | older validate/status commands |

`LabConfig` is the canonical model. New code should use it.

---

## Schema → Compose Pipeline

Each `config/services-v2/<id>.yaml` defines:

1. **`fields:`** — interactive prompts (type, default, validation, conditionals)
2. **`compose:`** — Docker Compose fragment template with `${field_name}` substitutions
3. **`defaults:`** — `dev:` / `prod:` profile overrides

`ComposeGenerator` (in `core/compose.py`) merges the user-supplied field values into the compose template, resolves `${global:domain}` cross-references, and writes the final `docker-compose.yml`.

---

## Secret Separation

Secrets never land in `config.yaml`. The wizard detects fields whose `key` contains `password`, `token`, `secret`, `key`, or `pass` and:

1. Writes the value to `.env` as `SERVICE_FIELD=<value>`
2. Writes a reference `${SERVICE_FIELD}` in `config.yaml`
3. The compose generator picks up env vars via Docker Compose's native `${VAR}` expansion

This means `.env` can be rotated independently of `config.yaml`.
