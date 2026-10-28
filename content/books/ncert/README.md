# NCERT PCM source corpus

Official English-medium NCERT textbook source files for Classes 11 and 12 are stored here. `source_archives/` contains the NCERT complete-book ZIP downloads; `source_pdfs/` contains the chapter PDFs extracted from those archives. Each PDF remains a citation source. Derived JSONL retrieval datasets are kept separately in [`../../datasets/ncert/`](../../datasets/ncert/README.md).

`catalog.json` records book/part/chapter identity, official download URL, edition text, PDF page count, and extracted word count. PDF page numbers are the citation locator; printed page numbering can differ because front matter is included.

## Rebuild source catalog and derived datasets

Run `python3 content/books/ncert/process_ncert_corpus.py` from the repository root after obtaining the source archives. The script requires Poppler's `pdftotext` at `/usr/bin/pdftotext` and the bundled standard Python libraries. It regenerates the LangChain-compatible JSONL datasets under `content/datasets/ncert/chunks/` and the source catalog from the retained PDFs.

## Review and correct extraction

Export flagged source pages with `python3 content/books/ncert/export_extraction_review.py`. To compare selected pages with Tesseract, pass exact `--target-page CHAPTER:PDF_PAGE` pairs and `--tesseract /path/to/tesseract`; OCR is recorded for review and is never applied automatically. Render every candidate page and verify its text and notation against the PDF before adding a row to `page_text_overrides.jsonl` with `verified_against_pdf: true`. Then rerun `process_ncert_corpus.py` and the Qdrant corpus validator. The override path preserves Unicode subscripts and superscripts; diagram contents must remain figure references unless manually transcribed from a verified source.

The PDFs and extracted text are for the project's local educational RAG experiments. Attribute textbook content to NCERT and consult NCERT's current reuse terms before redistribution.
