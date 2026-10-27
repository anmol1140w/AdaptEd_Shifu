# Architecture documentation

This area describes how AdaptEd is divided into independently testable parts.

The planned boundaries are:

- API transport and role-aware access.
- Application use cases.
- Learning-domain logic.
- AI and retrieval ports.
- Database and external-service adapters.
- Shared frontend/backend contracts.

The domain learning logic should remain independent from FastAPI, PostgreSQL and any particular LLM provider.

The PS-22 diagrams and product assets are stored in `PS22_Diagrams_and_Product_Assets.md` in this directory.
