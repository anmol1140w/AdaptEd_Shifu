# NCERT PCM source corpus

Official English-medium NCERT textbook source files for Classes 11 and 12 are stored here. `source_archives/` contains the NCERT complete-book ZIP downloads; `source_pdfs/` contains the chapter PDFs extracted from those archives. Each PDF remains a citation source. Derived JSONL retrieval datasets are kept separately in [`../../datasets/ncert/`](../../datasets/ncert/README.md).

`catalog.json` records book/part/chapter identity, official download URL, edition text, PDF page count, and extracted word count. PDF page numbers are the citation locator; printed page numbering can differ because front matter is included.

## Rebuild source catalog and derived datasets

Run `python3 content/books/ncert/process_ncert_corpus.py` from the repository root after obtaining the source archives. The script requires Poppler's `pdftotext` at `/usr/bin/pdftotext` and the bundled standard Python libraries. It regenerates the LangChain-compatible JSONL datasets under `content/datasets/ncert/chunks/` and the source catalog from the retained PDFs.

The PDFs and extracted text are for the project's local educational RAG experiments. Attribute textbook content to NCERT and consult NCERT's current reuse terms before redistribution.
