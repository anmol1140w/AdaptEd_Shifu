"""Evaluate the active isolated NCERT alias with Qdrant Cloud Inference."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from qdrant_client import QdrantClient, models
from backend.app.infrastructure.ai.settings import AISettings
from content.datasets.ncert.qdrant_pipeline import ACTIVE_ALIAS, CORPUS_ID, MODEL, SOURCE_KIND, _concept_lookup, _norm_title

ROOT=Path(__file__).resolve().parents[4]
EVAL=Path(__file__).with_name('questions.jsonl')
CATALOG=json.loads((ROOT/'content/books/ncert/catalog.json').read_text(encoding='utf-8'))
CHAPTERS={(b['class'],b['subject'].lower(),ch['chapter_code']):ch['chapter_title'] for b in CATALOG['books'] for ch in b['chapters']}

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--collection',help='evaluate a verified candidate collection before activating the official alias')
 args=parser.parse_args()
 settings=AISettings()
 if not settings.qdrant_url or not settings.qdrant_read_only_api_key:
  raise SystemExit('Qdrant read-only configuration missing')
 client=QdrantClient(url=settings.qdrant_url,api_key=settings.qdrant_read_only_api_key,cloud_inference=True,timeout=45)
 aliases={a.alias_name:a.collection_name for a in client.get_aliases().aliases}
 if ACTIVE_ALIAS not in aliases: raise SystemExit(f'{ACTIVE_ALIAS} alias is not configured')
 collection=args.collection or ACTIVE_ALIAS
 if args.collection and not client.collection_exists(collection): raise SystemExit(f'candidate collection does not exist: {collection}')
 mapping=_concept_lookup()
 queries=[json.loads(line) for line in EVAL.read_text(encoding='utf-8').splitlines() if line.strip()]
 rows=[]
 for q in queries:
  expected=q['expected_chapter_codes']; concepts=[]
  for code in expected:
   title=CHAPTERS.get((q['class'],q['subject'].lower(),code))
   if title: concepts.extend(mapping.get((q['class'],q['subject'].lower(),_norm_title(title)),()))
  if not q['answerable']:
   concepts=[ids[0] for (grade,subject,_),ids in sorted(mapping.items()) if grade==q['class'] and subject==q['subject'].lower() and ids][:1]
  points=[]
  for concept in dict.fromkeys(concepts):
   filt=models.Filter(must=[
    models.FieldCondition(key='corpus_id',match=models.MatchValue(value=CORPUS_ID)),
    models.FieldCondition(key='source_kind',match=models.MatchValue(value=SOURCE_KIND)),
    models.FieldCondition(key='subject',match=models.MatchValue(value=q['subject'])),
    models.FieldCondition(key='class',match=models.MatchValue(value=q['class'])),
    models.FieldCondition(key='concept_ids',match=models.MatchValue(value=concept)),
   ])
   result=client.query_points(collection_name=collection,query=models.Document(text=q['query'],model=MODEL),query_filter=filt,limit=5,with_payload=True,timeout=45)
   points.extend(result.points)
  points.sort(key=lambda p:float(p.score or 0),reverse=True)
  unique=[]; seen=set()
  for point in points:
   p=point.payload or {}; key=str(p.get('parent_chunk_id',p.get('chunk_id',point.id)))
   if key not in seen:seen.add(key);unique.append(point)
  rows.append({'id':q['id'],'answerable':q['answerable'],'expected':expected,'mapped_concepts':list(dict.fromkeys(concepts)),'hits':[
   {'chapter_code':(p.payload or {}).get('chapter_code'),'score':float(p.score or 0),'citation':(p.payload or {}).get('citation'),'source_kind':(p.payload or {}).get('source_kind')} for p in unique[:5]
  ]})
 answerable=[r for r in rows if r['answerable']]
 mapped=[r for r in answerable if r['mapped_concepts']]
 def metrics(threshold=None):
  recalls=[]; mrr=[]; precisions=[]
  for row in mapped:
   expected=set(row['expected'])
   hits=[h for h in row['hits'] if threshold is None or h['score']>=threshold]
   hits=hits[:5]
   found=[h['chapter_code'] for h in hits]
   relevant=[i for i,c in enumerate(found,1) if c in expected]
   recalls.append(len(set(found)&expected)/max(len(expected),1))
   mrr.append(1/relevant[0] if relevant else 0)
   precisions.append(sum(c in expected for c in found)/max(len(found),1))
  return {'chapter_recall_at_5':round(sum(recalls)/max(len(recalls),1),4),'mrr_at_5':round(sum(mrr)/max(len(mrr),1),4),'citation_precision_at_5':round(sum(precisions)/max(len(precisions),1),4),'answerable_with_mapped_evidence':len(mapped)}
 negative=[r for r in rows if not r['answerable']]
 summary={'alias':ACTIVE_ALIAS,'evaluated_target':collection,'target_is_active':collection==ACTIVE_ALIAS or aliases[ACTIVE_ALIAS]==collection,'model':MODEL,'questions':len(rows),'answerable':len(answerable),'unanswerable':len(negative),'no_threshold':metrics(),'threshold_0_6':metrics(.6),'unanswerable_top_score_ge_0_6':sum(bool(r['hits']) and r['hits'][0]['score']>=.6 for r in negative),'unanswerable_with_any_filtered_hit':sum(bool(r['hits']) for r in negative),'note':'An unanswerable case is searched through the first mapped concept in its class/subject because the production API requires a selected concept; this is a conservative probe, not a full abstention classifier.'}
 out=Path(__file__).with_name('qdrant_results.json')
 out.write_text(json.dumps({'summary':summary,'queries':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(summary,indent=2));print(f'Details written to {out.relative_to(ROOT)}')
if __name__=='__main__':main()
