# NCERT PCM corpus quality and retrieval report

Run date: 2026-10-28. This report describes local extraction and the live Qdrant Cloud checks performed from the current repository.

## Sources and chapter coverage

The source archive directory contains 11 official English NCERT book-part ZIPs and 104 extracted chapter PDFs for Classes 11 and 12 Physics, Chemistry, and Mathematics. The PDFs mark the edition as **Reprint 2026–27**; the catalog stores the official archive URL, book/part, chapter code/title, PDF page count, and word count. Page citations use PDF page numbers, which can differ from printed page numbers.

Of 104 source PDFs, **all 74 curricular chapters now map to 94 authored concept IDs** and are indexed for student retrieval. Thirty book-matter PDFs are intentionally excluded: 11 answer keys, 11 preliminaries, 7 appendices, and 1 supplementary-material file. Chapter-specific concept definitions and source chapter links were added for the previous 11 gaps: Class 11 Mathematics `kemh102`, `kemh111`, `kemh113`; Class 11 Physics `keph201`, `keph202`, `keph204`, `keph205`; Class 12 Mathematics `lemh101`; and Class 12 Physics `leph105`, `leph204`, `leph206`. The validator now reports zero curricular chapters needing mappings.

The live latest official collection was scanned against the source catalog: **14,851 points, all 74 expected curricular chapter codes, no missing or unexpected chapter codes, and every PDF page number covered by at least one indexed chunk span**. Each corresponding local page corpus also has one non-empty text chunk for every catalogued PDF page. This confirms page/chapter coverage, not exact recovery of every glyph or visual element.

Chapter inventory in the latest collection:

- **Class 11 Physics (14):** Units and Measurements; Motion in a Straight Line; Motion in a Plane; Laws of Motion; Work, Energy and Power; System of Particles and Rotational Motion; Gravitation; Mechanical Properties of Solids; Mechanical Properties of Fluids; Thermal Properties of Matter; Thermodynamics; Kinetic Theory; Oscillations; Waves.
- **Class 11 Chemistry (9):** Some Basic Concepts of Chemistry; Structure of Atom; Classification of Elements and Periodicity in Properties; Chemical Bonding and Molecular Structure; Thermodynamics; Equilibrium; Redox Reactions; Organic Chemistry: Some Basic Principles and Techniques; Hydrocarbons.
- **Class 11 Mathematics (14):** Sets; Relations and Functions; Trigonometric Functions; Complex Numbers and Quadratic Equations; Linear Inequalities; Permutations and Combinations; Binomial Theorem; Sequences and Series; Straight Lines; Conic Sections; Introduction to Three Dimensional Geometry; Limits and Derivatives; Statistics; Probability.
- **Class 12 Physics (14):** Electric Charges and Fields; Electrostatic Potential and Capacitance; Current Electricity; Moving Charges and Magnetism; Magnetism and Matter; Electromagnetic Induction; Alternating Current; Electromagnetic Waves; Ray Optics and Optical Instruments; Wave Optics; Dual Nature of Radiation and Matter; Atoms; Nuclei; Semiconductor Electronics.
- **Class 12 Chemistry (10):** Solutions; Electrochemistry; Chemical Kinetics; The d- and f-Block Elements; Coordination Compounds; Haloalkanes and Haloarenes; Alcohols, Phenols and Ethers; Aldehydes, Ketones and Carboxylic Acids; Amines; Biomolecules.
- **Class 12 Mathematics (13):** Relations and Functions; Inverse Trigonometric Functions; Matrices; Determinants; Continuity and Differentiability; Applications of Derivatives; Integrals; Applications of Integrals; Differential Equations; Vector Algebra; Three Dimensional Geometry; Linear Programming; Probability.

The extraction marks possible unresolved glyphs on PDF pages in 30 chapters. Those pages remain present in Qdrant but need source-PDF review before relying on exact notation:

- **Class 11 Physics:** Motion in a Straight Line p. 2; Motion in a Plane pp. 3, 5–6, 8; Work, Energy and Power p. 16; Gravitation pp. 1, 3–4, 8, 11–14, 16; Waves p. 11.
- **Class 11 Chemistry:** Some Basic Concepts of Chemistry pp. 10, 12, 14; Structure of Atom pp. 6, 8, 19–24; Chemical Bonding and Molecular Structure pp. 30, 35; Thermodynamics pp. 6–7, 9, 11, 13, 16–20, 24–26, 29; Equilibrium pp. 10, 12–14, 30, 34, 36, 39; Organic Chemistry: Some Basic Principles and Techniques pp. 8–9, 15, 19, 30–31, 33, 35.
- **Class 11 Mathematics:** Relations and Functions pp. 12, 16–17; Trigonometric Functions p. 27; Limits and Derivatives pp. 10, 22–23.
- **Class 12 Physics:** Electrostatic Potential and Capacitance p. 5; Moving Charges and Magnetism pp. 2, 4; Wave Optics p. 12.
- **Class 12 Chemistry:** Solutions pp. 3, 16; Electrochemistry pp. 1, 8, 16, 20, 23; Chemical Kinetics pp. 10, 12, 14–15, 18–19, 21–22, 27; The d- and f-Block Elements pp. 12, 18, 29; Coordination Compounds p. 6; Alcohols, Phenols and Ethers pp. 18, 29; Amines pp. 9, 12, 16, 21–22; Biomolecules pp. 3, 15.
- **Class 12 Mathematics:** Relations and Functions p. 11; Continuity and Differentiability pp. 3, 7–8, 13–15; Applications of Derivatives pp. 8, 21, 25, 36; Integrals p. 60; Probability p. 6.

The `unmapped_glyph_pages` flag is a conservative PDF text-extraction warning, not a claim that the entire listed page is missing. Separately, diagram artwork is not embedded: captions and nearby extracted text may be present, but geometry, circuit diagrams, plots, molecular structures, and labels inside figures must be checked in the cited PDF.

The authored Mathematics concept “Principle of Mathematical Induction” has no corresponding chapter in the downloaded NCERT book set and is not indexed. The `Complex Numbers` authored concept now maps to the source chapter `Complex Numbers and Quadratic Equations`; that mapping correction is included in the active collection fingerprint.

## Extraction and chunking

`process_ncert_corpus.py` builds page, heading-aware (soft 650-word), and fixed 450-word/75-word-overlap datasets. The active strategy is **heading-aware 650 words**, which preserves explicit section boundaries and worked examples when detected. It produces 4,499 source chunks; 3,596 mapped chunks become 14,851 embedding segments capped at 64 whitespace-delimited words with 10-word overlap. The other prepared strategies currently produce 14,211 page segments and 17,569 fixed-window segments. Point IDs are deterministic; segment fingerprints are SHA-256. The collection payload includes `corpus_id`, `source_kind`, `source_id`, `ingest_batch`, `content_fingerprint`, source book and edition, class, subject, part, chapter code/title, concept IDs, page span, citation, parent chunk and segment IDs, extraction/chunk strategies, text, and extraction-review flags.

The `langchain_loader.load_documents` path accepts a JSONL file or a strategy directory and creates LangChain `Document` objects with extracted text, stable chunk IDs, citation metadata, and the extraction strategy preserved. `langchain-core` remains an optional import for users of that loader; the app's production retrieval uses Qdrant Cloud Inference directly.

Representative PDF/text inspection found:

- Physics laws-of-motion prose and its equation `p = mv` extract clearly. Figure captions survive as text, but the diagrams themselves are not extracted.
- Chemistry chemical-bonding pages have severe text-layer glyph loss in examples (visible in the extracted text as missing letters in words such as “Write,” “carbon,” and “oxygen”) and broken Lewis structures. Reaction and formula flags cannot repair missing source glyphs. These passages must be checked against the PDF before precise chemical notation is taught.
- Mathematics complex-number pages retain most equations, but superscripts, fractions, and multi-line alignment flatten into linear text. Matrix, vector, and diagram layouts need PDF inspection where flagged.

The pipeline marks equation, figure, table, and unmapped-glyph pages with review notes. It does not claim to understand diagrams or recover two-dimensional notation from extracted text. The Chemistry defects are a material source-quality limitation; no OCR reconstruction has been applied.

## Retrieval evaluation

`evaluation/questions.jsonl` contains 71 authored questions across the six class/subject pairs, including equations, worked examples, cross-concept questions, misconceptions, and six corpus-unanswerable queries. It includes at least one chapter-specific question for each of the 11 newly mapped chapters; expected source chapters are listed for answerable questions.

Local lexical BM25 strategy comparison (chapter-level relevance, top 5):

| Strategy | Source chunks | Recall@5 | MRR@5 | Citation precision@5 |
|---|---:|---:|---:|---:|
| Page | 2,281 | 0.9692 | 0.9462 | 0.8154 |
| Heading-aware 650 words | 4,499 | 0.9846 | 0.9359 | 0.8092 |
| Fixed 450 words, overlap 75 | 2,239 | 0.9769 | 0.9385 | 0.8462 |

This favors heading-aware retrieval on chapter recall and fixed windows on precision, but the ranking is a local lexical BM25 proxy, not embedding retrieval. The active semantic strategy was separately evaluated in Qdrant Cloud Inference on the same 71 questions. All 65 answerable questions now have mapped evidence.

| Qdrant cutoff | Chapter Recall@5 | MRR@5 | Chapter citation precision@5 | Unanswerable probes scoring above cutoff |
|---|---:|---:|---:|---:|
| No cutoff | 1.0000 | 1.0000 | 1.0000 | Not applicable |
| 0.60 | 0.9231 | 0.9231 | 0.9231 | 0 of 6 |

Each of the six unanswerable probes returned some points when forced through a mapped concept filter, but none scored 0.60 or higher. The production routes therefore keep the measured 0.60 cutoff and return a no-passage error when all results are below it. This is a constrained concept-filtered benchmark; its chapter-level citation precision does not validate every individual citation or generalize to arbitrary questions. The cutoff loses about 7.7 percentage points on answerable queries. Five answerable queries fell below it; the lowest-scoring new chapter probe was Class 11 Statistics at 0.6011, so small query changes may cause abstention.

Manual live Qdrant probes returned chapter-correct evidence for all six class/subject combinations: Class 11 Physics `keph104`, Chemistry `kech201`, Mathematics `kemh104`; Class 12 Physics `leph101`, Chemistry `lech102`, Mathematics `lemh201`. The complex-number probe returned `kemh104` after the alias correction. Returned source IDs are unique chunk/segment identifiers; the API now binds citations to passages returned by Qdrant instead of asking the model to reproduce long IDs.

## Qdrant collections and source isolation

The pre-existing collection `ncertpcm_headingaware650words_minilm_3d8abc75b04a` had 13,165 points and remains served by `ncert_pcm_active`. Every old point was compared against deterministic local point IDs and source metadata: text, citation, source PDF path, chapter, class, and subject matched. Eighty-two `concept_ids` values differ from the corrected mapping for the Complex Numbers chapter. No text or citation conflict was found.

Before changing the app's routing, an export of all 13,165 legacy point IDs and full payloads was written and verified at `content/datasets/ncert/backups/ncert_pcm_active_20261028.jsonl`; its checksum is in the adjacent manifest. The backup directory is Git-ignored. Vectors were not exported; they can be recreated from the same configured embedding inference model. The old collection and `ncert_pcm_active` alias were left untouched.

The expanded official corpus is indexed separately in `ncertpcm_headingaware650words_minilm_115b85a3a358_official_v1` with 14,851 points, served by `ncert_pcm_official_active`. The earlier task-created versions `ncertpcm_headingaware650words_minilm_7db46a3abced_official_v1` and `ncertpcm_headingaware650words_minilm_a990fecc399b_official_v1` remain available as rollback snapshots; no collection was deleted. The active collection is 384-dimensional cosine and uses `sentence-transformers/all-minilm-l6-v2` for upload and query embedding. Its filters require corpus ID, official source kind, subject, class, and concept. All 11 newly mapped chapter queries and six class/subject representative filters passed; a deliberately mismatched corpus filter returned zero points. The application never queries the legacy alias, so legacy data is not blended into NCERT responses.

The Qdrant evaluator applies class, subject, corpus, source-kind, and mapped-concept filters for each question. These results should be read as concept-filtered retrieval evidence, not open-ended retrieval quality.

## Runtime and provider checks

The packaged FastAPI routes use `QDRANT_READ_ONLY_API_KEY` for retrieval and `QDRANT_API_KEY` only for ingestion. They use the same embedding model and official alias, preserve source type and page citations, and distinguish missing configuration, no passage above the measured cutoff, Qdrant failure, and invalid model output. The runtime continues to use the configured Ollama Cloud model (`gemma4:31b` in this environment); no fallback model was added. Live non-persistent Ollama checks produced schema-valid tutor, recommendation, and two-question quiz responses against retrieved Physics evidence. Backend-assigned citations came only from the retrieved passages. The production quiz route continues to save drafts as `pending_review` for teacher review.

The UI renders the source kind, citation, score, passage, and unique passage ID. Existing tutor history remains in PostgreSQL and is not rewritten.
