# AI infrastructure boundary

This directory is the adapter boundary for AdaptEd's language-model, retrieval, prompt and generated-output validation concerns.

Anmol owns the AI behavior and evaluation inside this boundary. Sharad owns the application integration and learning-intelligence orchestration around it. The first implementation must support mocked providers so the platform remains testable without live credentials.
