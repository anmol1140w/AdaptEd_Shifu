# AdaptEd backend

The backend will provide the learning platform's application services.

Planned responsibilities:

- Authentication and role-aware access.
- Assessment sessions and attempt recording.
- Subject summaries and concept-level mastery states.
- Skill-gap detection and next-best-action recommendations.
- Grounded tutor responses and weak-area quiz generation.
- Teacher analytics and intervention review.
- Audit events for recommendations and generated content.

The backend currently contains a provider-independent learning slice,
framework-independent assessment facade, v1 API adapter and reusable in-memory
composition root. An HTTP server, production database adapters,
authentication implementation and live AI adapters are still integration work.
