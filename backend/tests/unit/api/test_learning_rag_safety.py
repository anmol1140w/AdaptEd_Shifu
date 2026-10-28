from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))
from content.books.ncert.process_ncert_corpus import apply_page_overrides, load_page_overrides

def _source_python(code: str) -> str:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_ROOT / 'backend/src'}:{REPO_ROOT}"
    return subprocess.check_output([sys.executable, "-c", code], cwd=REPO_ROOT / "backend", env=env, text=True).strip()


class LearningRagSafetyTests(unittest.TestCase):
    def test_practice_loader_does_not_promote_unapproved_starter_items(self) -> None:
        result = _source_python("""
from backend.app.api.v1.routes.learning import _load_practice_bank
class Rows:
 def __init__(self,rows): self.rows=rows
 def fetchall(self): return self.rows
class DB:
 def __init__(self): self.sql=[]
 def execute(self,sql,params=()):
  self.sql.append(sql)
  if 'FROM learning_concepts' in sql: return Rows([{'concept_id':'phy-11-test','subject':'physics','class_level':11,'chapter':'Test','name':'Test','prerequisite_ids':[]}])
  return Rows([{'item_id':'teacher-approved','concept_id':'phy-11-test','approved':True}])
db=DB(); _,items=_load_practice_bank(db,'physics',11)
print(__import__('json').dumps({'sql':db.sql[1],'ids':[i['item_id'] for i in items]}))
""")
        result = json.loads(result)
        self.assertIn("approved=TRUE", result["sql"])
        self.assertNotIn("ANY", result["sql"])
        self.assertEqual(result["ids"], ["teacher-approved"])

    def test_unavailable_semantic_grader_returns_unscored_instead_of_similarity_guess(self) -> None:
        result = json.loads(_source_python("""
from unittest.mock import patch
from backend.app.api.v1.routes import learning
class Settings: ollama_api_key=''
with patch.object(learning,'AISettings',return_value=Settings()):
 result=learning._grade_answer(question='Explain why the object accelerates.',answer='The net force is zero, so it accelerates.',answer_guide='A non-zero net force produces acceleration.',explanation='Newton second law.')
print(__import__('json').dumps(result))
"""))
        self.assertIsNone(result["correct"])
        self.assertIsNone(result["score"])
        self.assertEqual(result["method"], "manual_review")

    def test_normalized_exact_answer_is_still_scored_without_model(self) -> None:
        result = json.loads(_source_python("""
from unittest.mock import patch
from backend.app.api.v1.routes import learning
class Settings: ollama_api_key=''
with patch.object(learning,'AISettings',return_value=Settings()):
 result=learning._grade_answer(question='What is the result?',answer='v = 2 m/s',answer_guide='v=2m/s',explanation='')
print(__import__('json').dumps(result))
"""))
        self.assertTrue(result["correct"])
        self.assertEqual(result["method"], "exact")

    def test_tutor_can_search_related_concepts_but_keep_class_and_subject_filters(self) -> None:
        result = _source_python("""
from unittest.mock import patch
from types import SimpleNamespace
from backend.app.api.v1.routes import learning
class Settings: qdrant_url='configured'; qdrant_read_only_api_key='configured'
class Client:
 def __init__(self,**kwargs): pass
 def query_points(self,**kwargs): print(__import__('json').dumps([x.key for x in kwargs['query_filter'].must])); return SimpleNamespace(points=[])
with patch.object(learning,'AISettings',return_value=Settings()),patch.object(learning,'QdrantClient',Client): learning._retrieve('physics',11,'phy-11-test','query',allow_related_concepts=True)
""")
        keys = set(json.loads(result))
        self.assertEqual(keys, {"corpus_id", "source_kind", "subject", "class"})

    def test_concept_filter_is_kept_for_concept_specific_retrieval(self) -> None:
        result = _source_python("""
from unittest.mock import patch
from types import SimpleNamespace
from backend.app.api.v1.routes import learning
class Settings: qdrant_url='configured'; qdrant_read_only_api_key='configured'
class Client:
 def __init__(self,**kwargs): pass
 def query_points(self,**kwargs): print(__import__('json').dumps([x.key for x in kwargs['query_filter'].must])); return SimpleNamespace(points=[])
with patch.object(learning,'AISettings',return_value=Settings()),patch.object(learning,'QdrantClient',Client): learning._retrieve('physics',11,'phy-11-test','query')
""")
        keys = set(json.loads(result))
        self.assertIn("concept_ids", keys)

    def test_page_override_requires_pdf_verification_and_is_applied(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "overrides.jsonl"
            path.write_text('{"book_code":"kech1","chapter_code":"kech104","pdf_page":9,"verified_text":"Lewis structure checked","verified_against_pdf":true,"reviewer":"teacher","reviewed_at":"2026-10-28"}\n', encoding="utf-8")
            overrides = load_page_overrides(path)
        rows = apply_page_overrides([{"pdf_page": 9, "page_text": "broken extract", "word_count": 2, "has_unmapped_private_use_glyphs": True}], "kech1", "kech104", overrides)
        self.assertEqual(rows[0]["page_text"], "Lewis structure checked")
        self.assertEqual(rows[0]["text_origin"], "human_verified_page_override")
        self.assertEqual(rows[0]["override_reviewer"], "teacher")


if __name__ == "__main__":
    unittest.main()
