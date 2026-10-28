#!/usr/bin/env python3
"""Extract official NCERT chapter PDFs and build comparable retrieval chunk sets."""
from __future__ import annotations

import json
import re
import subprocess
import unicodedata
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARCHIVES = ROOT / "source_archives"
PDF_ROOT = ROOT / "source_pdfs"
DOCUMENT_ROOT = ROOT.parent.parent / "datasets" / "ncert" / "chunks"
INDEX_PATH = ROOT / "catalog.json"
PAGE_OVERRIDES_PATH = ROOT / "page_text_overrides.jsonl"
PDFTOTEXT = "/usr/bin/pdftotext"

BOOKS = {
    "keph1": (11, "physics", "Physics", 1), "keph2": (11, "physics", "Physics", 2),
    "kech1": (11, "chemistry", "Chemistry", 1), "kech2": (11, "chemistry", "Chemistry", 2),
    "kemh1": (11, "mathematics", "Mathematics", None),
    "leph1": (12, "physics", "Physics", 1), "leph2": (12, "physics", "Physics", 2),
    "lech1": (12, "chemistry", "Chemistry", 1), "lech2": (12, "chemistry", "Chemistry", 2),
    "lemh1": (12, "mathematics", "Mathematics", 1), "lemh2": (12, "mathematics", "Mathematics", 2),
}

CHAPTER_NAMES = {
    "keph1": ["Units and Measurements", "Motion in a Straight Line", "Motion in a Plane", "Laws of Motion", "Work, Energy and Power", "System of Particles and Rotational Motion", "Gravitation"],
    "keph2": ["Mechanical Properties of Solids", "Mechanical Properties of Fluids", "Thermal Properties of Matter", "Thermodynamics", "Kinetic Theory", "Oscillations", "Waves"],
    "kech1": ["Some Basic Concepts of Chemistry", "Structure of Atom", "Classification of Elements and Periodicity in Properties", "Chemical Bonding and Molecular Structure", "Thermodynamics", "Equilibrium"],
    "kech2": ["Redox Reactions", "Organic Chemistry: Some Basic Principles and Techniques", "Hydrocarbons"],
    "kemh1": ["Sets", "Relations and Functions", "Trigonometric Functions", "Complex Numbers and Quadratic Equations", "Linear Inequalities", "Permutations and Combinations", "Binomial Theorem", "Sequences and Series", "Straight Lines", "Conic Sections", "Introduction to Three Dimensional Geometry", "Limits and Derivatives", "Statistics", "Probability"],
    "leph1": ["Electric Charges and Fields", "Electrostatic Potential and Capacitance", "Current Electricity", "Moving Charges and Magnetism", "Magnetism and Matter", "Electromagnetic Induction", "Alternating Current", "Electromagnetic Waves"],
    "leph2": ["Ray Optics and Optical Instruments", "Wave Optics", "Dual Nature of Radiation and Matter", "Atoms", "Nuclei", "Semiconductor Electronics"],
    "lech1": ["Solutions", "Electrochemistry", "Chemical Kinetics", "The d- and f-Block Elements", "Coordination Compounds"],
    "lech2": ["Haloalkanes and Haloarenes", "Alcohols, Phenols and Ethers", "Aldehydes, Ketones and Carboxylic Acids", "Amines", "Biomolecules"],
    "lemh1": ["Relations and Functions", "Inverse Trigonometric Functions", "Matrices", "Determinants", "Continuity and Differentiability", "Applications of Derivatives"],
    "lemh2": ["Integrals", "Applications of Integrals", "Differential Equations", "Vector Algebra", "Three Dimensional Geometry", "Linear Programming", "Probability"],
}

def clean(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    # Some textbook fonts encode normal ASCII text in U+F020..U+F07E.
    # Reverse the font's +0xF000 shift so those pages remain searchable.
    text = "".join(chr(ord(ch) - 0xF000) if 0xF020 <= ord(ch) <= 0xF07E else ch for ch in text)
    # Poppler exposes these stretchy math delimiters as private-use glyphs in
    # some NCERT PDFs. Convert only unambiguous bracket pieces to plain brackets.
    for glyph in "": text = text.replace(glyph, "(")
    for glyph in "": text = text.replace(glyph, ")")
    for glyph in "": text = text.replace(glyph, "[")
    for glyph in "": text = text.replace(glyph, "]")
    for glyph in "": text = text.replace(glyph, "{")
    for glyph in "": text = text.replace(glyph, "}")
    text = text.replace("®", " → ").replace("úú", " || ").replace("ú", " | ").replace("\uf0b4", " × ")
    lines = []
    for line in text.splitlines():
        s = re.sub(r"\s+", " ", line).strip()
        if not s or re.fullmatch(r"(?:Reprint\s+)?20\d\d-\d\d", s, re.I):
            continue
        if s.upper() in {"NCERT", "NATIONAL COUNCIL OF EDUCATIONAL RESEARCH AND TRAINING"}:
            continue
        lines.append(s)
    return "\n".join(lines).strip()

def clean_verified_override(text: str) -> str:
    """Tidy authored corrections while preserving scientific Unicode notation.

    Unlike extracted PDF text, verified overrides already have repaired glyphs;
    NFKC would flatten subscript/superscript charges and indices in equations.
    """
    return "\n".join(re.sub(r"\s+", " ", line).strip() for line in text.splitlines()).strip()

def pdf_pages(pdf: Path) -> list[str]:
    result = subprocess.run([PDFTOTEXT, "-layout", str(pdf), "-"], check=True, capture_output=True, text=True)
    raw_pages = result.stdout.split("\f")
    if raw_pages and not raw_pages[-1].strip():
        raw_pages.pop()  # pdftotext adds a final form-feed after the last page.
    return [clean(p) for p in raw_pages]

def jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def chapter_title(pages: list[str], filename: str) -> str:
    excluded = re.compile(r"^(?:CHAPTER(?:\s+[A-Z]+)?|UNIT(?:\s+\d+)?|OBJECTIVES|AFTER STUDYING(?: THIS)? UNIT.*|TEXTBOOK.*|CLASS\s+(?:XI|XII)|PART\s+[I|V]+|REPRINT.*|NCERT)$", re.I)
    objective_block = False
    for page_no, page in enumerate(pages[:3], 1):
        for line_no, line in enumerate(page.splitlines(), 1):
            s = re.sub(r"\s+", " ", line).strip(" -:;")
            if s.lower() == "objectives":
                objective_block = True
                continue
            if not (3 <= len(s) <= 100) or excluded.match(s):
                continue
            if re.match(r"^(?:\d+(?:\.\d+)?|[A-Z])\s+", s) or re.search(r"[.!?]$", s):
                continue
            words = s.split()
            if len(words) > 8 or s.lower().startswith(("after studying", "you will be able", "objectives")):
                continue
            if s.startswith(("•", "·", "-")) or (objective_block and s[0].islower()):
                continue
            alpha = [c for c in s if c.isalpha()]
            if not alpha:
                continue
            upper_ratio = sum(c.isupper() for c in alpha) / len(alpha)
            if upper_ratio >= 0.5 or not objective_block:
                return s.title() if s.isupper() else s[0].upper() + s[1:]
    return filename

def official_chapter_title(book_code: str, chapter_code: str, extracted: str) -> str:
    suffix = chapter_code[len(book_code):]
    if suffix.isdigit():
        number = int(suffix[-2:])
        names = CHAPTER_NAMES.get(book_code, [])
        if 1 <= number <= len(names):
            return names[number - 1]
    if suffix.endswith("ps"):
        return "Prelims"
    if suffix.endswith("an"):
        return "Answers"
    if suffix.startswith("a"):
        return "Appendix"
    if suffix.endswith("sm"):
        return "Supplementary Material"
    return extracted

def page_records(book_code: str, pdf: Path, pages: list[str], title: str, meta: tuple):
    grade, subject_slug, subject, part = meta
    return [{
        "page_id": f"ncert-{book_code}-{pdf.stem}-p{num:03d}",
        "source_id": f"ncert-{book_code}", "book_code": book_code, "class": grade,
        "subject": subject, "part": part, "chapter_code": pdf.stem,
        "chapter_title": title, "pdf_page": num, "page_text": page,
        "has_unmapped_private_use_glyphs": bool(re.search(r"[\uE000-\uF8FF]", page)),
        "word_count": len(page.split()), "source_pdf": str(pdf.relative_to(PDF_ROOT)),
    } for num, page in enumerate(pages, 1)]

def load_page_overrides(path: Path = PAGE_OVERRIDES_PATH) -> dict[tuple[str, int], dict[str, str]]:
    """Load human-verified page corrections without touching source PDFs.

    Each JSONL row must include book_code, chapter_code, pdf_page,
    verified_text, verified_against_pdf=true, reviewer, and reviewed_at.
    Example: {"book_code":"kech1","chapter_code":"kech104","pdf_page":9,
    "verified_text":"...","verified_against_pdf":true,"reviewer":"name",
    "reviewed_at":"2026-10-28"}.
    """
    if not path.exists():
        return {}
    overrides: dict[tuple[str, int], dict[str, str]] = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid page override JSON at {path}:{line_no}: {exc}") from exc
        required = ("book_code", "chapter_code", "pdf_page", "verified_text", "verified_against_pdf", "reviewer", "reviewed_at")
        missing = [key for key in required if key not in row or row[key] in (None, "")]
        if missing:
            raise ValueError(f"Page override at {path}:{line_no} is missing {', '.join(missing)}")
        if row["verified_against_pdf"] is not True:
            raise ValueError(f"Page override at {path}:{line_no} must be explicitly verified against its source PDF")
        page_no = int(row["pdf_page"])
        if page_no < 1 or not isinstance(row["verified_text"], str):
            raise ValueError(f"Invalid page number or corrected text at {path}:{line_no}")
        key = (f"{row['book_code']}/{row['chapter_code']}", page_no)
        if key in overrides:
            raise ValueError(f"Duplicate page override for {key[0]} page {page_no}")
        overrides[key] = {"text": clean_verified_override(row["verified_text"]), "reviewer": str(row["reviewer"]), "reviewed_at": str(row["reviewed_at"])}
    return overrides

def apply_page_overrides(records: list[dict], book_code: str, chapter_code: str,
                         overrides: dict[tuple[str, int], dict[str, str]]) -> list[dict]:
    source_key = f"{book_code}/{chapter_code}"
    corrected = []
    for record in records:
        row = dict(record)
        override = overrides.get((source_key, int(row["pdf_page"])))
        if override:
            row["page_text"] = override["text"]
            row["word_count"] = len(override["text"].split())
            row["has_unmapped_private_use_glyphs"] = bool(re.search(r"[\uE000-\uF8FF]", override["text"]))
            row["text_origin"] = "human_verified_page_override"
            row["override_reviewer"] = override["reviewer"]
            row["override_reviewed_at"] = override["reviewed_at"]
        else:
            row["text_origin"] = "pdftotext_layout"
        corrected.append(row)
    return corrected

def heading_aware(records: list[dict], prefix: str, max_words: int = 650):
    # Keep explicit worked examples together, even when they exceed the target size.
    # Split at section, example, and exercise boundaries; otherwise use a soft word cap.
    heading = re.compile(r"^\s*(?:\d+(?:\.\d+)+\s+[A-Z]|[A-Z]\s+[A-Z][A-Z0-9 ,()’'&/–—:-]{2,})")
    example = re.compile(r"^\s*(?:(?:Worked|Solved)\s+)?Example\s*(?:No\.?\s*)?\d+(?:\.\d+)?\b|^\s*Illustration\s+\d+", re.I)
    exercise = re.compile(r"^\s*(?:EXERCISE|EXERCISES)\s+\d", re.I)
    groups, current, words, in_example = [], [], 0, False
    for rec in records:
        for line in rec["page_text"].splitlines():
            # PDF layout extraction can place a heading after text from an adjacent
            # column. Split explicit Example/Illustration labels out before grouping.
            marker = re.compile(r"\b(?:(?:Worked|Solved)\s+)?Example\s+(?:No\.?\s*)?\d+(?:\.\d+)?\b|\bIllustration\s+\d+", re.I)
            segments = []
            rest = line
            match = marker.search(rest)
            while match:
                if rest[:match.start()].strip(): segments.append(rest[:match.start()].strip())
                segments.append(rest[match.start():].strip())
                rest = ""
                break
            if not segments:
                segments = [line]
            for segment in segments:
                line_words = len(segment.split())
                begins_example = bool(example.match(segment))
                begins_exercise = bool(exercise.match(segment))
                begins_section = bool(heading.match(segment)) and not begins_example and not begins_exercise
                if current and (begins_example or begins_exercise or begins_section):
                    groups.append(current); current, words = [], 0
                    in_example = False
                if begins_example:
                    in_example = True
                if begins_exercise:
                    in_example = False
                if current and words + line_words > max_words and not in_example:
                    groups.append(current); current, words = [], 0
                current.append((rec["pdf_page"], segment)); words += line_words
    if current:
        groups.append(current)
    out = []
    for i, group in enumerate(groups, 1):
        text = "\n".join(line for _, line in group).strip()
        if text:
            out.append((f"{prefix}-section-{i:04d}", text, min(p for p, _ in group), max(p for p, _ in group)))
    return out

def page_content_flags(text: str) -> set[str]:
    flags = set()
    if re.search(r"\b(?:(?:Worked|Solved)\s+)?Example\s*\d|\bIllustration\s+\d", text, re.I):
        flags.add("worked_example")
    if re.search(r"\bExercise(?:s)?\s+\d", text, re.I):
        flags.add("exercise")
    if re.search(r"\bFig(?:ure)?\.?\s*\d+(?:\.\d+)?", text, re.I):
        flags.add("diagram_or_figure_reference")
    if re.search(r"\bTable\s+\d+(?:\.\d+)?", text, re.I):
        flags.add("table_reference")
    # This is deliberately broad: it marks pages for which linear text may not
    # faithfully preserve two-dimensional mathematical or chemical notation.
    if re.search(r"(?:=|≈|≠|≤|≥|±|→|←|↔|⇌|⇒|∫|∑|√|∆|Δ|∞|lim\b|_[0-9]|\^[0-9])", text):
        flags.add("formula_or_equation")
    if re.search(r"(?:\b[A-Z][a-z]?\s*\d+|\b\d+\s*[A-Z][a-z]?\b).*(?:→|⇌|=)|(?:→|⇌)\s*[A-Z]", text):
        flags.add("chemical_equation")
    if "®" in text or "ú" in text:
        flags.add("chemical_equation")
    return flags

def fixed_chunks(records: list[dict], prefix: str, size: int = 450, overlap: int = 75):
    tokens = []
    for rec in records:
        for token in rec["page_text"].split():
            tokens.append((token, rec["pdf_page"]))
    out, start, i = [], 0, 1
    while start < len(tokens):
        end = min(start + size, len(tokens))
        text = " ".join(token for token, _ in tokens[start:end])
        out.append((f"{prefix}-fixed450o75-{i:04d}", text, tokens[start][1], tokens[end - 1][1]))
        if end == len(tokens): break
        start = end - overlap; i += 1
    return out

def assemble_chunks(parts, records, book_code, grade, subject, part_num, chapter_code, title, strategy):
    pages_by_num = {r["pdf_page"]: r["page_text"] for r in records}
    result = []
    for chunk_id, text, pstart, pend in parts:
        page_flags = {p: page_content_flags(pages_by_num.get(p, "")) for p in range(pstart, pend + 1)}
        combined_flags = set().union(*page_flags.values()) if page_flags else set()
        visual_pages = [p for p, flags in page_flags.items() if "diagram_or_figure_reference" in flags]
        table_pages = [p for p, flags in page_flags.items() if "table_reference" in flags]
        formula_pages = [p for p, flags in page_flags.items() if "formula_or_equation" in flags or "chemical_equation" in flags]
        glyph_pages = [r["pdf_page"] for r in records if pstart <= r["pdf_page"] <= pend and r["has_unmapped_private_use_glyphs"]]
        overrides = [r for r in records if pstart <= r["pdf_page"] <= pend and r.get("text_origin") == "human_verified_page_override"]
        source_pdf = f"content/books/ncert/source_pdfs/{book_code}/{chapter_code}.pdf"
        notes = []
        if visual_pages:
            notes.append("Diagram artwork is in the cited source PDF page; extracted text may contain its caption only.")
        if formula_pages:
            notes.append("Use the cited source PDF page for exact equation layout, superscripts, subscripts, and fraction structure.")
        if glyph_pages:
            notes.append("Some math glyphs could not be mapped from PDF text; use the cited source PDF for the exact notation.")
        if table_pages:
            notes.append("Use the cited source PDF page to verify table row and column alignment.")
        result.append({
            "page_content": text,
            "metadata": {
                "chunk_id": chunk_id, "book_id": f"ncert-{book_code}",
                "source_id": f"ncert-{book_code}", "source_reference_id": f"ncert-{book_code}",
                "class": grade, "subject": subject,
                "book_part": str(part_num) if part_num is not None else "single",
                "chapter_code": chapter_code, "chapter_title": title,
                "chunking_strategy": strategy, "page_start": pstart, "page_end": pend,
                "extraction_strategy": "pdftotext_layout_nfkc_font_repair_v1",
                "source_pdf_path": source_pdf,
                "text_normalization": "NFKC; NCERT shifted-font ASCII repair; common reaction and cell-notation repair",
                "page_content_is_text_only": True,
                "source_pdf_retains_original_visual_layout": True,
                "citation": f"NCERT {subject}, Class {grade}, " + (f"Part {part_num}, " if part_num is not None else "") + f"{title}, PDF pp. {pstart}-{pend}",
                "word_count": len(text.split()),
                "content_flags": ",".join(sorted(combined_flags)),
                "figure_reference_pages": ",".join(map(str, visual_pages)),
                "table_reference_pages": ",".join(map(str, table_pages)),
                "formula_pages": ",".join(map(str, formula_pages)),
                "unmapped_glyph_pages": ",".join(map(str, glyph_pages)),
                "human_verified_override_pages": ",".join(str(r["pdf_page"]) for r in overrides),
                "human_verified_override_reviewers": ",".join(sorted({str(r["override_reviewer"]) for r in overrides})),
                "requires_source_pdf_for_visual_review": bool(visual_pages or table_pages),
                "requires_source_pdf_for_equation_review": bool(formula_pages or glyph_pages),
                "extraction_notes": " ".join(notes),
            },
        })
    return result

def main():
    missing = [c for c in BOOKS if not (ARCHIVES / f"{c}dd.zip").exists()]
    if missing:
        raise SystemExit("Missing downloaded NCERT archives: " + ", ".join(missing))
    catalog = {"schema_version": "1.0", "title": "NCERT PCM Class 11–12 Source Corpus", "language": "en",
               "source_authority": "National Council of Educational Research and Training (NCERT)",
               "source_catalog": "https://ncert.nic.in/textbook.php", "books": []}
    page_overrides = load_page_overrides()
    for code, meta in BOOKS.items():
        grade, slug, subject, part = meta
        archive = ARCHIVES / f"{code}dd.zip"
        book_title = f"{subject}, Class {grade}" if part is None else f"{subject}, Part {part}, Class {grade}"
        book_rec = {"book_id": f"ncert-{code}", "book_code": code, "class": grade,
                    "subject": subject, "part": part, "title": book_title,
                    "edition_label": "Reprint 2026-27 (as marked in downloaded source PDFs)",
                    "archive": str(archive.relative_to(ROOT)),
                    "official_download_url": f"https://ncert.nic.in/textbook/pdf/{code}dd.zip",
                    "chapters": []}
        with zipfile.ZipFile(archive) as zf:
            pdf_members = sorted(n for n in zf.namelist() if n.lower().endswith(".pdf"))
            for member in pdf_members:
                pdf_name = Path(member).name
                pdf_path = PDF_ROOT / code / pdf_name
                pdf_path.parent.mkdir(parents=True, exist_ok=True)
                if not pdf_path.exists():
                    pdf_path.write_bytes(zf.read(member))
                pages = pdf_pages(pdf_path)
                if not pages:
                    continue
                title = official_chapter_title(code, pdf_path.stem, chapter_title(pages, pdf_path.stem))
                records = apply_page_overrides(page_records(code, pdf_path, pages, title, meta), code, pdf_path.stem, page_overrides)
                chapter = {"chapter_code": pdf_path.stem, "chapter_title": title,
                           "source_pdf": str(pdf_path.relative_to(ROOT)), "pdf_pages": len(pages),
                           "word_count": sum(r["word_count"] for r in records)}
                book_rec["chapters"].append(chapter)
                prefix = f"{code}-{pdf_path.stem}"
                sets = {
                    "page": [(f"{prefix}-page-{r['pdf_page']:04d}", r["page_text"], r["pdf_page"], r["pdf_page"]) for r in records if r["page_text"]],
                    "heading_aware_650_words": heading_aware(records, prefix),
                    "fixed_450_words_overlap_75": fixed_chunks(records, prefix),
                }
                for strategy, chunks in sets.items():
                    jsonl(DOCUMENT_ROOT / strategy / code / f"{pdf_path.stem}.jsonl",
                          assemble_chunks(chunks, records, code, grade, subject, part, pdf_path.stem, title, strategy))
        catalog["books"].append(book_rec)
    INDEX_PATH.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    refs_path = ROOT.parent.parent / "references" / "pcm_sources.json"
    refs_data = json.loads(refs_path.read_text(encoding="utf-8"))
    refs_data["citation_policy"]["page_policy"] = (
        "Authored digital material has no page number. NCERT textbook chunks cite the exact class, "
        "subject, part, chapter, and inclusive PDF page span from the source edition."
    )
    refs_data["references"] = [r for r in refs_data["references"] if not r["reference_id"].startswith("ncert-")]
    for book in catalog["books"]:
        refs_data["references"].append({
            "reference_id": book["book_id"], "reference_type": "official_textbook",
            "title": book["title"], "publisher": catalog["source_authority"],
            "publication_year": "2026", "edition": book["edition_label"], "language": "English",
            "url": book["official_download_url"], "archive_path": f"content/books/ncert/{book['archive']}",
            "scope": "Primary textbook source for page-aware retrieval chunks. Cite the chunk's chapter title and PDF page span.",
            "page_start": None, "page_end": None
        })
    refs_path.write_text(json.dumps(refs_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for manifest_path in (ROOT.parent).glob("*.json"):
        if manifest_path.name == "catalog.json":
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(manifest, dict) or "class" not in manifest or "subject" not in manifest:
            continue
        grade = manifest["class"]
        subject = str(manifest["subject"]).lower()
        manifest["supplemental_ncert_reference_ids"] = [
            b["book_id"] for b in catalog["books"]
            if b["class"] == grade and b["subject"].lower() == subject
        ]
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Catalogued {len(catalog['books'])} source books")
    print(f"Extracted chapters: {sum(len(b['chapters']) for b in catalog['books'])}")
    for strategy in ("page", "heading_aware_650_words", "fixed_450_words_overlap_75"):
        rows = 0
        for path in (DOCUMENT_ROOT / strategy).rglob("*.jsonl"):
            rows += sum(1 for _ in path.open(encoding="utf-8"))
        print(f"{strategy}: {rows} chunks")

if __name__ == "__main__": main()
