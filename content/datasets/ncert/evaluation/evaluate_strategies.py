"""Small dependency-free chapter retrieval benchmark over the checked-in JSONL sets."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CORPUS = ROOT / "content/datasets/ncert/chunks"
EVAL = Path(__file__).with_name("questions.jsonl")
STRATEGIES = ("page", "heading_aware_650_words", "fixed_450_words_overlap_75")
TOKEN = re.compile(r"[a-z0-9]+")


def terms(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def load_queries() -> list[dict]:
    return [json.loads(line) for line in EVAL.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_corpus(strategy: str) -> list[dict]:
    rows = []
    for path in sorted((CORPUS / strategy).rglob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            meta = row["metadata"]
            rows.append({"terms": Counter(terms(row["page_content"])), "text": row["page_content"], "meta": meta})
    return rows


def rank(query: str, docs: list[dict], avg_len: float, df: Counter, n: int, k1: float = 1.2, b: float = .75) -> list[tuple[float, dict]]:
    query_terms = set(terms(query))
    scored = []
    for doc in docs:
        freq = doc["terms"]
        length = sum(freq.values())
        score = 0.0
        for term in query_terms:
            tf = freq.get(term, 0)
            if not tf:
                continue
            idf = math.log(1 + (n - df[term] + .5) / (df[term] + .5))
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * length / max(avg_len, 1)))
        scored.append((score, doc))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored


def evaluate(strategy: str, queries: list[dict]) -> tuple[dict, dict[str, list[dict]]]:
    docs = load_corpus(strategy)
    df = Counter()
    lengths = []
    for doc in docs:
        df.update(doc["terms"].keys())
        lengths.append(sum(doc["terms"].values()))
    avg_len = sum(lengths) / max(len(lengths), 1)
    answerable = [q for q in queries if q["answerable"]]
    recall_values, reciprocal_ranks, citation_precision = [], [], []
    query_results = {}
    for query in queries:
        ranked = rank(query["query"], docs, avg_len, df, len(docs))[:5]
        found_codes = [str(doc["meta"]["chapter_code"]) for _, doc in ranked]
        query_results[query["id"]] = [
            {"chapter_code": doc["meta"]["chapter_code"], "chunk_id": doc["meta"]["chunk_id"],
             "citation": doc["meta"]["citation"], "page_start": doc["meta"]["page_start"],
             "page_end": doc["meta"]["page_end"], "score": round(score, 4),
             "text_excerpt": " ".join(doc["text"].split())[:180]}
            for score, doc in ranked
        ]
        if not query["answerable"]:
            continue
        expected = set(query["expected_chapter_codes"])
        hits = [idx for idx, code in enumerate(found_codes, 1) if code in expected]
        recall_values.append(len(set(found_codes) & expected) / max(len(expected), 1))
        reciprocal_ranks.append(1 / hits[0] if hits else 0.0)
        citation_precision.append(sum(code in expected for code in found_codes) / max(len(found_codes), 1))
    metrics = {
        "strategy": strategy,
        "documents": len(docs),
        "queries": len(queries),
        "answerable_queries": len(answerable),
        "unanswerable_queries": len(queries) - len(answerable),
        "chapter_recall_at_5": round(sum(recall_values) / max(len(recall_values), 1), 4),
        "mrr_at_5": round(sum(reciprocal_ranks) / max(len(reciprocal_ranks), 1), 4),
        "citation_precision_at_5": round(sum(citation_precision) / max(len(citation_precision), 1), 4),
        "ranking": "local lexical BM25; not Qdrant Cloud Inference",
    }
    return metrics, query_results


def main() -> None:
    queries = load_queries()
    if len(queries) < 60:
        raise SystemExit(f"Evaluation set too small: {len(queries)} questions (need at least 60)")
    combos = {(q["class"], q["subject"]) for q in queries}
    if len(combos) != 6:
        raise SystemExit(f"Expected six Class/subject combinations, found {len(combos)}")
    results = []
    detail = {}
    for strategy in STRATEGIES:
        metrics, per_query = evaluate(strategy, queries)
        results.append(metrics)
        detail[strategy] = per_query
    out = Path(__file__).with_name("results.json")
    out.write_text(json.dumps({"metrics": results, "query_results": detail}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    print(f"Detailed ranked hits written to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
