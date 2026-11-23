
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import json,shutil,hashlib,gzip,base64
B=RESEARCH_ROOT; D=B/'senate_v5/dist'
def read(p,default=None):
 p=B/p
 return json.loads(p.read_text()) if p.exists() else default
old=read('atlas_work/reference-data.json',{})
research=read('dossier_research/district_enrichment_compact.json',{})
for row in research.get('districts',[]):
 rows=[]
 for name in ['media_records.json','candidate_media_records.json']:
  raw=read('dossier_research/'+name,{})
  rr=raw.get('districts',[]) if isinstance(raw,dict) else raw
  match=next((x for x in rr if x.get('district')==row['district']),{})
  rows+=match.get('media_records',match.get('media',[]))
 row['media_records']=list({x['id']:x for x in rows}.values())
data={'meta':{'revision':'v5-command-20261123','builtAt':'2026-11-23','title':'The Sixty-Three','referenceImage':'assets/reference-command-center.jpg'},'geometry':read('senate_v5/map-data.json'), 'elections':read('election_research/senate_elections_2026.json'),'finance':read('finance_research/atlas_finance_normalized.json'),'directory':read('election_research/district_counties_official.json'),'research':research,'issuePlan':read('dossier_research/issues_corrected.json',[]),'handoff':read('v5_data/handoff/normalized.json',{}),'census':read('v5_data/census/normalized.json',{'districts':[]}), 'issueEvidence':read('v5_data/issues/normalized.json',{'issues':[],'records':[],'legislation':[]}), 'overlays':read('v5_data/handoff/district_overlays.json',{}),'profiles':read('v5_data/issues/official_profiles.json',{}),'migrationFresh':read('v5_data/handoff/fresh_migration.json',{})}
# Keep full source content and source identifiers; each collection retains its own dates.
raw=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode()
# Keep an unpacked QA checkpoint outside published assets. The public payload is losslessly compressed.
(B/'senate_v5/data-unpacked.json').write_bytes(raw)
compressed=base64.b64encode(gzip.compress(raw,compresslevel=9,mtime=0)).decode()
chunk_size=480000
parts=[compressed[i:i+chunk_size] for i in range(0,len(compressed),chunk_size)]
for i,part in enumerate(parts):
    (D/f'data-{i:02d}.js').write_text(('window.SENATE_PARTS=[];' if i==0 else '')+f"window.SENATE_PARTS[{i}]='"+part+"';\n")
loader="window.SENATE_DATA=JSON.parse(fflate.strFromU8(fflate.gunzipSync(Uint8Array.from(atob(window.SENATE_PARTS.join('')),c=>c.charCodeAt(0)))));delete window.SENATE_PARTS;\n"
(D/'data.js').write_text(loader)
html=(D/'index.html').read_text()
import re
html=re.sub(r'<script defer src="\./data-\d+\.js\?v=5"></script>','',html)
scripts=''.join(f'<script defer src="./data-{i:02d}.js?v=5"></script>' for i in range(len(parts)))
html=html.replace('<script defer src="./data.js?v=5">',scripts+'<script defer src="./data.js?v=5">')
(D/'index.html').write_text(html)

# Copy original supplied charts without changing their original research vintage.
for p in (B/'v5_data/handoff/charts').glob('*.png'):
 dest=D/'assets/charts'/p.name;dest.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(p,dest)
print(json.dumps({'districts':len(data['elections']['districts']),'candidates':sum(len(x['candidates']) for x in data['elections']['districts']),'layers':len(data['handoff'].get('layers',[])),'censusDistricts':len(data['census'].get('districts',[])),'dataBytes':(D/'data.js').stat().st_size}))
