# Generation adapters

This directory contains implementations of the application's tutor and quiz
generation ports.

`grok.py` implements both generation ports using xAI's Responses API and strict
JSON Schema output. The model defaults to `grok-4.7`. `ollama_cloud.py` provides
the JSON-prompted backup through Ollama Cloud; Ollama Cloud currently does not
enforce JSON schemas, so its output is strictly parsed and locally validated.
`primary_fallback.py` runs the primary output through application validation
and tries Ollama if Grok fails, returns malformed data, or violates a learning
contract. If Ollama also fails, the use case returns its curated safe fallback.

`mock.py` provides deterministic local tutor and weak-area quiz generators,
plus curated fallbacks. These need no network access or credentials. Ollama
Cloud generation is selected by passing `use_grok=True` to the runtime builder.
This configures Grok as primary and Ollama Cloud as backup. The legacy
`use_ollama_cloud=True` flag remains an alias for the same provider chain.
The runtime otherwise keeps its deterministic offline adapters.
