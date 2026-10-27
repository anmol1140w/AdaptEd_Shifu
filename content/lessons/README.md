# Lessons

Each subject/class lesson file follows the `subject_class_number.json` pattern and contains retrieval units with explanation, worked-example, and misconception chunks. Chunks carry subject/class/topic metadata, stable IDs, a source reference, syllabus alignment reference, and review status. The original Algebra lesson fixtures remain alongside them because the application's mock retrieval flows cite their IDs.

Official NCERT retrieval corpora are datasets rather than authored lessons; find the page-based, heading-aware, and fixed-window JSONL files under [`../datasets/ncert/chunks/`](../datasets/ncert/chunks/). Loading instructions are in [`../datasets/ncert/README.md`](../datasets/ncert/README.md), and source PDFs plus rebuild instructions are in [`../books/ncert/`](../books/ncert/README.md).
