#!/usr/bin/env python3
"""Create a verified, payload-only backup of a Qdrant collection."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from content.datasets.ncert.qdrant_pipeline import _qdrant_client

ROOT = Path(__file__).resolve().parents[3]
BACKUP_ROOT = ROOT / "content/datasets/ncert/backups"


def backup(collection: str, prefix: str) -> Path:
    client = _qdrant_client(read_only=True)
    if not client.collection_exists(collection):
        raise SystemExit(f"Qdrant collection does not exist: {collection}")
    aliases = sorted(
        alias.alias_name for alias in client.get_aliases().aliases
        if alias.collection_name == collection
    )
    expected = client.count(collection_name=collection, exact=True).count
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    output = BACKUP_ROOT / f"{prefix}.jsonl"
    manifest_path = BACKUP_ROOT / f"{prefix}.manifest.json"
    if output.exists() or manifest_path.exists():
        raise SystemExit(f"Refusing to overwrite existing backup {prefix}")
    temporary = output.with_suffix(".jsonl.tmp")
    offset = None
    count = 0
    digest = hashlib.sha256()
    try:
        with temporary.open("wb") as stream:
            while True:
                points, offset = client.scroll(
                    collection_name=collection,
                    limit=256,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )
                for point in points:
                    row = {"id": str(point.id), "payload": point.payload or {}}
                    if not row["payload"]:
                        raise RuntimeError(f"Point {point.id} has no payload; refusing incomplete text backup")
                    if not any(key in row["payload"] for key in ("page_content", "text", "content")):
                        raise RuntimeError(f"Point {point.id} has no recognized text field; refusing backup")
                    data = (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
                    stream.write(data)
                    digest.update(data)
                    count += 1
                if offset is None:
                    break
            stream.flush()
            os.fsync(stream.fileno())
        if count != expected:
            raise RuntimeError(f"Backup record count {count} differs from Qdrant count {expected}")
        os.replace(temporary, output)
        manifest = {
            "collection": collection,
            "aliases": aliases,
            "points": count,
            "sha256": digest.hexdigest(),
            "format": "Qdrant point id and full payload JSONL; vectors omitted",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return output
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--prefix", required=True, help="stable filename prefix for the backup")
    args = parser.parse_args()
    path = backup(args.collection, args.prefix)
    manifest = json.loads(path.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    print(f"Verified backup: points={manifest['points']} sha256={manifest['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
