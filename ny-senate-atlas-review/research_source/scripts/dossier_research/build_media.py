
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import json,re,logging
import pdfplumber
logging.getLogger('pdfminer').setLevel(logging.ERROR)
ROOT=(RESEARCH_ROOT / 'dossier_research')
PDF=str(RESEARCH_ROOT / 'reference/US mid term/NY_State_Senate_Terminal_Master_Plan_v4.pdf')

def clean(s):
 s=s.translate(str.maketrans({'\ue081':'(','\ue082':')','\ue088':'-','\ue092':':','\ue087':'@','\ue09d':'+'}))
 return re.sub(r'\s+',' ',s).strip()

def col(words,lo,hi,join=' '):
 return clean(join.join(w['text'] for w in sorted(words,key=lambda w:(round(w['top'],1),w['x0'])) if lo<=w['x0']<hi))

def sd_refs(s):
 ds=set()
 for m in re.finditer(r'\bSD\s*[–-]?\s*(\d{1,2})(?:\s*[–-]\s*(\d{1,2}))?',s):
  a,b=map(int,(m.group(1),m.group(2) or m.group(1)))
  ds.update(i for i in range(a,b+1) if 1<=i<=63)
 return sorted(ds)

registry=[];logged=[]
with pdfplumber.open(PDF) as doc:
 for pn in [67,68,69,70]:
  words=doc.pages[pn-1].extract_words()
  anchors=sorted([w for w in words if re.fullmatch('S\\d+',w['text']) and w['x0']<80],key=lambda w:w['top'])
  for j,a in enumerate(anchors):
   rows=[w for w in words if w['top']>=a['top']-2 and w['top']<(anchors[j+1]['top']-2 if j+1<len(anchors) else 807)]
   raw_sd=col(rows,318,366,'')
   districts=[] if re.search(r'all|many',raw_sd,re.I) else [int(v) for v in re.findall(r'\d+',raw_sd) if 1<=int(v)<=63]
   row={'id':a['text'],'title':col(rows,75,207),'publisher':col(rows,207,274),'date':col(rows,274,318),'districts':districts,'districts_as_printed':raw_sd,'type':col(rows,366,419),'url':col(rows,419,600,''),'pdf_page':pn,'status':'Referenced in the supplied master plan, dated 19 Nov 2026; not independently refreshed','evidence_source':'Master-plan source register','association':'District number explicitly recorded in the source register'}
   registry.append(row)
 for pn in [73,74,75]:
  words=doc.pages[pn-1].extract_words()
  anchors=sorted([w for w in words if w['text'].startswith(('https://','http://')) and w['x0']>420],key=lambda w:w['top'])
  for j,a in enumerate(anchors):
   rows=[w for w in words if w['top']>=a['top']-3.5 and w['top']<(anchors[j+1]['top']-3.5 if j+1<len(anchors) else 790)]
   publisher=col(rows,45,128.5);title=col(rows,188,371);url=col(rows,430,600,'');date=col(rows,128.5,188);evidence=col(rows,371,430)
   kind='Video' if 'youtube.com' in url else 'Public social post' if 'x.com/' in url else 'Radio / podcast' if 'podcast' in url else 'Interview / reporting'
   logged.append({'id':f'LOG-{pn}-{j+1}','title':title,'publisher':publisher,'date':date,'date_timezone':'IST (as printed)','districts':sd_refs(title),'type':kind,'evidence':evidence,'url':url,'pdf_page':pn,'status':'Link logged in the supplied plan; current availability and full content not independently verified','evidence_source':'Master-plan logged social and video register','association':'District number explicitly mentioned in the logged summary'})
# Include only district-tagged news, voter guides, questionnaires and published endorsements as media.
news=[r for r in registry if r['districts'] and any(x in r['type'].lower() for x in ['news','guide','questionnaire','endorsement','interview'])]
by={i:[] for i in range(1,64)}
for r in news+logged:
 for sd in r['districts']:
  if sd in by:by[sd].append(r)
out={'metadata':{'source':'NY_State_Senate_Terminal_Master_Plan_v4.pdf','snapshot':'2026-11-19','sources_pages':[67,68,69,70,73,74,75],'verification':'Historical reference extraction, not a new media collection. Only explicitly district-tagged records are assigned; other records remain statewide/unassigned.'},'districts':[{'district':sd,'media_records':rows} for sd,rows in by.items()],'unassigned_logged_items':[r for r in logged if not r['districts']]}
(ROOT/'media_records.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'source_registry_structured.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2))
print(json.dumps({'district_news_source_records':len(news),'logged_records':len(logged),'assigned_media_entries':sum(len(x) for x in by.values()),'districts_with_records':sum(bool(x) for x in by.values()),'unassigned_logged':len(out['unassigned_logged_items'])}))
for sd in [17,28,43,44,59]:
 print(sd,[(x['id'],x['type'],x['publisher'],x['title'][:100],x['url']) for x in by[sd]])
