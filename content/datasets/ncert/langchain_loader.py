"""Load NCERT JSONL records as LangChain Document objects.

LangChain is imported lazily so the source corpus can be processed without it.
"""
from __future__ import annotations

import json
from pathlib import Path


def load_documents(path: str | Path):
    """Load one JSONL file or a strategy directory as LangChain Documents.

    Directory traversal is sorted so repeated loads yield the same document
    order. Each document keeps the original extracted page content and scalar
    citation metadata without rewriting or flattening the source record.
    """
    try:
        from langchain_core.documents import Document
    except ImportError as exc:
        raise RuntimeError(
            "Install langchain-core in the application environment to create Document objects. "
            "The JSONL records already use LangChain's page_content/metadata schema."
        ) from exc

    source_path = Path(path)
    paths = [source_path] if source_path.is_file() else sorted(source_path.rglob("*.jsonl"))
    if not paths:
        raise FileNotFoundError(f"No JSONL corpus files found at {source_path}")
    documents = []
    for file_path in paths:
        with file_path.open(encoding="utf-8") as source:
            for line_number, line in enumerate(source, 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if not isinstance(record.get("page_content"), str) or not isinstance(record.get("metadata"), dict):
                    raise ValueError(f"Invalid LangChain document record at line {line_number} in {file_path}")
                metadata = dict(record["metadata"])
                if not metadata.get("chunk_id") or not metadata.get("citation"):
                    raise ValueError(f"Document is missing stable chunk or citation metadata at {file_path}:{line_number}")
                metadata.setdefault("extraction_strategy", "pdftotext_layout_nfkc_font_repair_v1")
                documents.append(Document(page_content=record["page_content"], metadata=metadata))
    return documents
