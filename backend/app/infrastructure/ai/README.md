# AI infrastructure boundary

This directory is the adapter boundary for AdaptEd's language-model, retrieval, prompt and generated-output validation concerns.

Anmol owns the AI behavior and evaluation inside this boundary. Sharad owns the application integration and learning-intelligence orchestration around it. The first implementation must support mocked providers so the platform remains testable without live credentials.

Implemented dependency-free adapters now provide:

- approved in-memory source retrieval;
- deterministic tutor and weak-area quiz generation;
- curated fallback responses when retrieval or generation fails;
- structured-output validation for sources, hints and quiz alignment; and
- in-memory audit records for provider, source and fallback decisions.

Provider-specific LLM or vector-store adapters can implement the same ports
without changing the application use cases.
