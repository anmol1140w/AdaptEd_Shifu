# Generation adapters

This directory contains implementations of the application's tutor and quiz
generation ports.

`ollama_cloud.py` implements both generation ports using the configured
Ollama Cloud model and the official `/api/chat` endpoint. It prompts for JSON,
parses the response into the application's typed drafts, and leaves source,
concept, anti-spoiler, and quiz checks to the application validator.

`mock.py` provides deterministic local tutor and weak-area quiz generators,
plus curated fallbacks. These need no network access or credentials. Ollama
Cloud is selected by passing `use_ollama_cloud=True` to the runtime builder;
there is no alternate model configured.
