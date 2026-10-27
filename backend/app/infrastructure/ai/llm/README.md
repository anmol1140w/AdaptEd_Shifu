# Generation adapters

This directory contains implementations of the application's tutor and quiz
generation ports.

`ollama_cloud.py` implements both generation ports using the configured
Ollama Cloud model and the official `/api/chat` endpoint. It requests JSON,
validates the response shape locally, and leaves source, concept, anti-spoiler,
and quiz checks to the application validator.

`mock.py` provides deterministic local tutor and weak-area quiz generators,
plus curated fallbacks. These need no network access or credentials. Ollama
Cloud generation is selected by passing `use_ollama_cloud=True` to the runtime
builder. The runtime otherwise keeps its deterministic offline adapters.
