"""Deterministic Offline Mock Retrieval Adapter for AdaptEd.

Provides deterministic in-memory indexing and keyword/concept retrieval of approved
lesson content and worked examples without external vector databases or network access.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from backend.app.application.ports.ai_ports import RetrievedChunk, RetrieverPort


class MockKnowledgeRetriever(RetrieverPort):
    """Deterministic, 100% offline knowledge base retriever for Class 9 Mathematics."""

    # Curated fallback knowledge base guaranteeing 100% offline autonomy
    DEFAULT_APPROVED_CHUNKS: List[Dict[str, Any]] = [
        {
            "id": "lesson-algebra-03",
            "source_id": "lesson-algebra-03",
            "concept_id": "ALG-DIST-01",
            "title": "The Distributive Property: Multiplying Across Parentheses",
            "text": (
                "The Distributive Property states that multiplying a factor across a sum or difference "
                "requires applying the multiplier to every term inside the parentheses: a(b + c) = ab + ac. "
                "When the multiplier is a negative quantity, each term inside the parentheses must be multiplied "
                "by that negative number, reversing the signs: -a(b + c) = -ab - ac, and -a(b - c) = -ab + ac. "
                "A frequent misconception is multiplying only the first term and leaving subsequent terms unchanged, "
                "such as writing -2(x + 3) = -2x + 3 instead of distributing the -2 to both x and +3 to obtain -2x - 6. "
                "Always multiply the outer factor by each internal term individually before simplifying."
            ),
            "tags": [
                "distributive property",
                "brackets",
                "parentheses",
                "negative multiplier",
                "sign change",
                "linear expressions",
                "algebra",
                "ALG-DIST-01",
            ],
            "score": 1.0,
        },
        {
            "id": "worked-example-07",
            "source_id": "worked-example-07",
            "concept_id": "ALG-DIST-01",
            "title": "Worked Example: Distributing a Negative Multiplier Across Parentheses",
            "text": (
                "Problem: Expand and simplify the expression -2(x + 3).\n"
                "Step 1 (Identify terms): The multiplier outside the parentheses is -2. The terms inside the parentheses are x and +3.\n"
                "Step 2 (Distribute to first term): Multiply -2 by x: (-2) * x = -2x.\n"
                "Step 3 (Distribute to second term): Multiply -2 by +3: (-2) * (+3) = -6.\n"
                "Step 4 (Combine results): Combine the distributed products: -2x + (-6) = -2x - 6.\n"
                "Key Takeaway: The negative sign belongs to the multiplier and must be distributed to BOTH terms inside the parentheses. "
                "Writing -2x + 3 is a misconception where the constant was not multiplied."
            ),
            "tags": [
                "worked example",
                "distributive property",
                "negative multiplier",
                "common misconception",
                "algebra",
                "ALG-DIST-01",
            ],
            "score": 1.0,
        },
        {
            "id": "lesson-algebra-04",
            "source_id": "lesson-algebra-04",
            "concept_id": "ALG-TWOSTEP-01",
            "title": "Solving Two-Step Linear Equations",
            "text": (
                "A two-step linear equation takes the general form ax + b = c, where a and b are known coefficients and x is the unknown variable. "
                "Solving two-step equations requires isolating the variable term by applying inverse operations in the reverse order of arithmetic operations. "
                "Step 1: Use addition or subtraction to eliminate the constant term b from the side containing the variable (e.g., subtract b from both sides). "
                "Step 2: Use multiplication or division to eliminate coefficient a (e.g., divide both sides by a). "
                "When equations contain parentheses, such as a(x + b) = c, expand the expression using the distributive property first, "
                "or divide both sides by a if divisible without remainder."
            ),
            "tags": [
                "two-step equations",
                "linear equations",
                "inverse operations",
                "isolating variable",
                "coefficients",
                "algebra",
                "ALG-TWOSTEP-01",
            ],
            "score": 1.0,
        },
        {
            "id": "worked-example-08",
            "source_id": "worked-example-08",
            "concept_id": "ALG-TWOSTEP-01",
            "title": "Worked Example: Solving Two-Step Equations with Parentheses",
            "text": (
                "Problem: Solve the equation -2(x + 3) = 8 for x.\n"
                "Method 1 (Distribute First):\n"
                "Step 1: Expand the left-hand side using the distributive property: -2(x + 3) becomes -2x - 6. The equation is now -2x - 6 = 8.\n"
                "Step 2: Isolate the variable term by adding 6 to both sides: -2x = 8 + 6 => -2x = 14.\n"
                "Step 3: Solve for x by dividing both sides by -2: x = 14 / (-2) => x = -7.\n"
                "Verification: Check your answer by substituting x = -7 into the original equation: -2(-7 + 3) = -2(-4) = 8. "
                "Since 8 = 8, the solution is correct.\n"
                "Common Error Alert: Adding 6 before properly distributing the negative multiplier leads to an incorrect sign."
            ),
            "tags": [
                "worked example",
                "two-step equations",
                "linear equations",
                "brackets",
                "inverse operations",
                "algebra",
                "ALG-TWOSTEP-01",
            ],
            "score": 1.0,
        },
    ]

    def __init__(
        self,
        content_dirs: Optional[List[str]] = None,
        min_similarity_threshold: float = 0.15,
        chunks: Optional[List[RetrievedChunk]] = None,
        content_dir: Optional[str] = None,
    ):
        self._chunks: Dict[str, RetrievedChunk] = {}
        self.min_similarity_threshold = min_similarity_threshold

        # Load default embedded chunks first
        for chunk_data in self.DEFAULT_APPROVED_CHUNKS:
            chunk = RetrievedChunk.from_dict(chunk_data)
            self._chunks[chunk.id] = chunk

        # If explicit chunks list passed, register them
        if chunks:
            for ch in chunks:
                if isinstance(ch, RetrievedChunk):
                    self._chunks[ch.id] = ch
                elif isinstance(ch, dict):
                    c = RetrievedChunk.from_dict(ch)
                    self._chunks[c.id] = c

        # Index specified or standard content directories if available
        search_dirs: List[str] = []
        if content_dir:
            search_dirs.append(content_dir)
        elif content_dirs:
            search_dirs.extend(content_dirs)
        elif not chunks:
            search_dirs.extend([
                "content/lessons",
                "/data/adapted/AdaptEd/content/lessons",
            ])

        for cdir in search_dirs:
            if os.path.exists(cdir):
                self.index_directory(cdir)

    def add_chunk(self, chunk: RetrievedChunk) -> None:
        """Add or update a chunk in the in-memory index."""
        self._chunks[chunk.id] = chunk

    def get_chunk_by_id(self, chunk_id: str) -> Optional[RetrievedChunk]:
        """Direct lookup of a chunk by ID."""
        return self._chunks.get(chunk_id)

    def clear(self) -> None:
        """Clear all indexed chunks."""
        self._chunks.clear()

    def index_directory(self, dir_path: str) -> int:
        """Scan directory and index all valid JSON lesson chunks or item files."""
        loaded_count = 0
        path = Path(dir_path)
        if not path.exists():
            return 0

        for file_path in path.glob("**/*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "id" in data and "text" in data:
                    chunk = RetrievedChunk.from_dict(data)
                    self._chunks[chunk.id] = chunk
                    loaded_count += 1
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "id" in item and ("text" in item or "question" in item):
                            text_content = item.get("text") or (
                                f"{item.get('question', '')} {item.get('explanation', '')}"
                            )
                            chunk = RetrievedChunk(
                                id=str(item["id"]),
                                text=text_content,
                                concept_id=str(item.get("concept_id", "")),
                                source_id=str(item.get("source_id", item["id"])),
                                title=item.get("title", item.get("question", "")[:60]),
                                score=1.0,
                                tags=item.get("tags", [item.get("representation", ""), item.get("misconception_tag", "")]),
                            )
                            self._chunks[chunk.id] = chunk
                            loaded_count += 1
            except Exception:
                continue

        return loaded_count

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        """Normalize and tokenize text into lowercase alphanumeric words."""
        cleaned = re.sub(r"[^\w\s-]", " ", text.lower())
        tokens = set(re.findall(r"\b[a-z0-9_-]{2,}\b", cleaned))
        # Filter generic English stopwords to focus on mathematical terms
        stopwords = {
            "the", "and", "that", "this", "with", "for", "from", "are", "was",
            "were", "have", "has", "had", "what", "which", "how", "who", "when",
            "where", "why", "can", "could", "should", "would", "will", "shall",
            "into", "onto", "upon", "about", "above", "after", "again", "also",
        }
        return tokens - stopwords

    def _compute_relevance(
        self, chunk: RetrievedChunk, target_concept_id: str, query_tokens: Set[str]
    ) -> float:
        """Compute deterministic relevance score in [0.0, 1.0] for a chunk."""
        score = 0.0

        # Exact concept ID match contributes a major baseline
        concept_match = False
        if target_concept_id and chunk.concept_id:
            if target_concept_id.strip().upper() == chunk.concept_id.strip().upper():
                score += 0.50
                concept_match = True

        # Tokenize chunk metadata and content
        chunk_text_tokens = self._tokenize(chunk.text)
        chunk_tag_tokens = set()
        for t in chunk.tags:
            chunk_tag_tokens.update(self._tokenize(t))
        if chunk.title:
            chunk_tag_tokens.update(self._tokenize(chunk.title))

        all_chunk_tokens = chunk_text_tokens | chunk_tag_tokens

        if query_tokens and all_chunk_tokens:
            overlap = query_tokens & all_chunk_tokens
            # Jaccard overlap on tags (high weight)
            tag_overlap = query_tokens & chunk_tag_tokens
            if chunk_tag_tokens:
                score += 0.30 * (len(tag_overlap) / max(len(query_tokens), 1))
            # Overlap on body text
            score += 0.20 * (len(overlap) / max(len(query_tokens), 1))

        # If concept matches and query is minimal/empty, ensure strong score
        if concept_match and not query_tokens:
            score = max(score, 0.85)

        return min(round(score, 4), 1.0)

    def retrieve(
        self, concept_id: str, query: str = "", top_k: int = 3
    ) -> List[RetrievedChunk]:
        """Retrieve approved content chunks deterministically matching concept and query.

        If similarity is below threshold or no chunks match, returns empty list so
        calling tutor service can escalate to teacher review.
        """
        if top_k <= 0:
            return []

        concept_normalized = concept_id.strip().upper() if concept_id else ""
        # If concept_id is specified, verify at least one chunk exists for this concept
        if concept_normalized:
            has_concept = any(
                chunk.concept_id and chunk.concept_id.strip().upper() == concept_normalized
                for chunk in self._chunks.values()
            )
            if not has_concept:
                return []

        query_tokens = self._tokenize(query)
        scored_chunks: List[RetrievedChunk] = []

        for chunk in self._chunks.values():
            if concept_normalized and chunk.concept_id:
                if chunk.concept_id.strip().upper() != concept_normalized:
                    continue

            rel_score = self._compute_relevance(chunk, concept_id, query_tokens)
            if rel_score >= self.min_similarity_threshold:
                # Return a cloned chunk with the dynamic score populated
                scored = RetrievedChunk(
                    id=chunk.id,
                    text=chunk.text,
                    concept_id=chunk.concept_id,
                    source_id=chunk.source_id,
                    title=chunk.title,
                    score=rel_score,
                    tags=list(chunk.tags),
                )
                scored_chunks.append(scored)

        # Sort deterministically: highest score first, then stable chunk ID
        scored_chunks.sort(key=lambda c: (-c.score, c.id))

        return scored_chunks[:top_k]
