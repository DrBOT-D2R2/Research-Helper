# Speckit for Knowledge Vault

Speckit is the lightweight project memory for this repository. It keeps product intent, architecture boundaries, data shape, implementation tasks, and known risks close to the code so the project can move quickly without losing decisions.

## How it works

- `product.md` explains what problem the project solves and for whom.
- `architecture.md` describes system boundaries, components, and local data flow.
- `data-model.md` captures the durable domain model before code hardens around it.
- `api.md` defines the backend contract used by the frontend.
- `ux.md` documents the core screens and the minimum user journeys.
- `tasks.md` is the working implementation order for the MVP.
- `risks.md` tracks technical unknowns and mitigation plans.
- `decisions.md` records architectural decisions over time.
- `roadmap.md` separates one-week MVP scope from PS-1 expansion.
- `security.md` defines how local files are handled safely.
- `observability.md` documents logs, metrics, and operational behavior.

## How to use it during development

1. Start with `product.md` and `tasks.md` before adding scope.
2. Update `decisions.md` when a meaningful tradeoff is locked in.
3. Change `api.md` and `data-model.md` alongside backend contract changes.
4. Review `risks.md` at the start of each milestone.
5. Keep the MVP honest by comparing changes against `roadmap.md`.

Speckit is intentionally lightweight. It is not meant to replace issues or formal design docs; it keeps the minimum project context needed to build fast without drifting.
