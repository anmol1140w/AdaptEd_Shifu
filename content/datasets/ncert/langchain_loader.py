"""Load NCERT JSONL records as LangChain Document objects.

LangChain is imported lazily so the source corpus can be processed without it.
"""
from __future__ import annotations

import json
from pathlib import Path


def load_documents(path: str | Path):
    """Return ``langchain_core.documents.Document`` objects from one JSONL file."""
    try:
        from langchain_core.documents import Document
    except ImportError as exc:
        raise RuntimeError(
            "Install langchain-core in the application environment to create Document objects. "
            "The JSONL records already use LangChain's page_content/metadata schema."
        ) from exc

    documents = []
    with Path(path).open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record.get("page_content"), str) or not isinstance(record.get("metadata"), dict):
                raise ValueError(f"Invalid LangChain document record at line {line_number} in {path}")
            documents.append(Document(page_content=record["page_content"], metadata=record["metadata"]))
    return documents
