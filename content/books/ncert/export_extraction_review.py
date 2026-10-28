#!/usr/bin/env python3
"""Export text-extraction warning pages for review against the original NCERT PDFs.

Optional OCR is included as a comparison aid only; OCR output is never inserted
into the corpus unless a reviewer verifies it and records a page override.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGE_CHUNKS = ROOT / "content/datasets/ncert/chunks/page"


def flagged_pages() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(PAGE_CHUNKS.rglob("*.jsonl")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            meta = record["metadata"]
            flags = set(str(meta.get("content_flags", "")).split(",")) - {""}
            needs_equation_check = bool(meta.get("requires_source_pdf_for_equation_review"))
            needs_visual_check = bool(meta.get("requires_source_pdf_for_visual_review"))
            glyph_pages = {int(value) for value in str(meta.get("unmapped_glyph_pages", "")).split(",") if value.strip()}
            needs_glyph_check = int(meta["page_start"]) in glyph_pages
            if needs_glyph_check:
                flags.add("unmapped_private_use_glyph")
            if not (flags or needs_equation_check or needs_visual_check or needs_glyph_check):
                continue
            rows.append({
                "book_code": str(meta["book_id"]).removeprefix("ncert-"),
                "chapter_code": str(meta["chapter_code"]),
                "chapter_title": str(meta["chapter_title"]),
                "class": int(meta["class"]),
                "subject": str(meta["subject"]),
                "pdf_page": int(meta["page_start"]),
                "source_pdf": str(meta["source_pdf_path"]),
                "chunk_id": str(meta["chunk_id"]),
                "flags": sorted(flags),
                "equation_review": needs_equation_check,
                "visual_review": needs_visual_check,
                "glyph_review": needs_glyph_check,
                "extracted_text": record["page_content"],
                "ocr_text": None,
                "review_status": "needs_source_pdf_review",
                "override_jsonl": "content/books/ncert/page_text_overrides.jsonl",
            })
    return rows


def ocr_page(row: dict, tesseract: str) -> str:
    pdf = ROOT / row["source_pdf"]
    with tempfile.TemporaryDirectory(prefix="ncert-page-ocr-") as temp:
        image_prefix = Path(temp) / "page"
        subprocess.run(
            ["pdftoppm", "-f", str(row["pdf_page"]), "-l", str(row["pdf_page"]), "-singlefile", "-r", "300", "-png", str(pdf), str(image_prefix)],
            check=True, capture_output=True, text=True,
        )
        image_path = image_prefix.with_suffix(".png")
        result = subprocess.run([tesseract, str(image_path), "stdout", "--psm", "6"], check=True, capture_output=True, text=True)
        return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "content/books/ncert/extraction_review_queue.jsonl")
    parser.add_argument("--ocr", action="store_true", help="add Tesseract OCR comparison text; never auto-correct corpus text")
    parser.add_argument("--max-pages", type=int, help="limit OCR work for a smoke check")
    parser.add_argument("--chapter-code", action="append", default=[], help="include only this chapter in the review queue; repeatable")
    parser.add_argument("--subject", choices=("Physics", "Chemistry", "Mathematics"), help="include only this subject")
    parser.add_argument("--class", dest="class_number", type=int, choices=(11, 12), help="include only this class")
    parser.add_argument("--pdf-page", type=int, action="append", default=[], help="OCR only these PDF page numbers; repeatable")
    parser.add_argument("--glyph-only", action="store_true", help="limit queue to pages with unmapped private-use glyphs")
    parser.add_argument("--target-page", action="append", default=[], metavar="CHAPTER:PAGE", help="include an exact chapter/PDF-page pair; repeatable")
    parser.add_argument("--tesseract", type=Path, help="Tesseract executable; defaults to PATH lookup")
    args = parser.parse_args()
    rows = flagged_pages()
    if args.glyph_only:
        rows = [row for row in rows if row["glyph_review"]]
    if args.target_page:
        targets: set[tuple[str, int]] = set()
        for value in args.target_page:
            try:
                chapter_code, page = value.rsplit(":", 1)
                targets.add((chapter_code, int(page)))
            except ValueError as exc:
                raise SystemExit(f"Invalid --target-page {value!r}; expected CHAPTER:PAGE") from exc
        rows = [row for row in rows if (row["chapter_code"], row["pdf_page"]) in targets]
    if args.chapter_code:
        chapter_codes = set(args.chapter_code)
        rows = [row for row in rows if row["chapter_code"] in chapter_codes]
    if args.subject:
        rows = [row for row in rows if row["subject"] == args.subject]
    if args.class_number:
        rows = [row for row in rows if row["class"] == args.class_number]
    if args.pdf_page:
        pages = set(args.pdf_page)
        rows = [row for row in rows if row["pdf_page"] in pages]
    if args.ocr:
        tesseract = str(args.tesseract) if args.tesseract else shutil.which("tesseract")
        if not tesseract:
            raise SystemExit("Tesseract is not installed; install it to generate OCR comparison text. The review queue can still be exported without --ocr.")
        if not Path(tesseract).is_file():
            raise SystemExit(f"Tesseract executable not found: {tesseract}")
        version = subprocess.run([tesseract, "--version"], check=True, capture_output=True, text=True).stdout.splitlines()[0]
        for row in rows[:args.max_pages]:
            row["ocr_text"] = ocr_page(row, tesseract)
            row["ocr_engine"] = version
            row["ocr_disposition"] = "comparison_only_not_applied"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as target:
        for row in rows:
            target.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Exported {len(rows)} flagged pages to {args.output}")
    if args.ocr:
        print(f"Added OCR comparison text to {min(len(rows), args.max_pages or len(rows))} pages; no OCR text was applied to the corpus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
