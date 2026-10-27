# Learning Content

Structured PCM learning content for Classes 11 and 12. Stable IDs link the content areas. JSON filenames use full subject names and class numbers (for example, `physics_class_11.json`); stable IDs inside the data retain their original short subject codes so existing application references continue to work.

- `books/`: six learning-book manifests plus the downloaded NCERT source corpus for Classes 11 and 12.
- `concepts/`: canonical concept catalogs, explicit prerequisites, and misconception links.
- `lessons/`: authored explanation, worked-example, and misconception passages.
- `datasets/ncert/chunks/`: generated LangChain-compatible NCERT documents in three comparable chunking strategies, ready for vectorization.
- `items/`: formative questions linked to concepts, lessons, and supporting chunks.
- `references/`: curriculum references and citation policy.
- `seeds/`: fictional learner profiles and item-linked attempt evidence.
- `scenarios/`: reusable learner flows that bind seed evidence to retrieval and practice expectations.

The authored AdaptEd instructional passages are original material and require subject-teacher review before classroom use. The NCERT chunk collection is extracted from the official English textbook PDFs; each chunk carries its source volume, chapter, and inclusive PDF page span for retrieval citations. Source archives, chapter PDFs, extraction metadata, and rebuild instructions are in [`books/ncert/`](books/ncert/README.md); dataset format and loading details are in [`datasets/ncert/`](datasets/ncert/README.md). Consult NCERT's current reuse terms before redistributing extracted text. The original Algebra fixtures remain in `items/` and `lessons/` because the application's mock retrieval and question flows still refer to their IDs.
