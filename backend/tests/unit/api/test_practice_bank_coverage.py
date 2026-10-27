"""Ensure each adaptive concept has at least one mapped starter question."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]


class PracticeBankCoverageTests(unittest.TestCase):
    def test_every_class_subject_concept_has_a_review_required_item(self) -> None:
        for concept_path in sorted((REPO_ROOT / "content/concepts").glob("*_class_*.json")):
            concepts = json.loads(concept_path.read_text(encoding="utf-8"))["concepts"]
            item_path = REPO_ROOT / "content/items" / concept_path.name
            items = json.loads(item_path.read_text(encoding="utf-8"))["items"]
            concept_ids = {concept["concept_id"] for concept in concepts}
            item_concepts = {item["concept_id"] for item in items}

            self.assertFalse(concept_ids - item_concepts, f"Missing mapped items in {item_path.name}")
            self.assertFalse(item_concepts - concept_ids, f"Orphan item mappings in {item_path.name}")
            for item in items:
                self.assertFalse(item.get("teacher_approved", False), item["item_id"])
                self.assertEqual(item.get("citation_status"), "teacher_review_required", item["item_id"])


if __name__ == "__main__":
    unittest.main()
