
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import json,concurrent.futures,urllib.request,hashlib,datetime
D=(RESEARCH_ROOT / 'v5_data/handoff')/'raw';D.mkdir(exist_ok=True)
urls={'nyc_senate_districts':'https://data.cityofnewyork.us/resource/afns-vxeu.geojson?$limit=1000','nyc_nta2020':'https://data.cityofnewyork.us/resource/9nt8-h7nd.geojson?$limit=1000','nyc_election_districts':'https://data.cityofnewyork.us/resource/wwxk-38u4.geojson?$limit=10000'}
def get(item):
 name,url=item
 try:
  with urllib.request.urlopen(url,timeout=90) as f:b=f.read()
  d=json.loads(b);assert d.get('type')=='FeatureCollection',str(d)[:300]
  (D/(name+'.geojson')).write_bytes(b)
  result={'name':name,'url':url,'features':len(d['features']),'bytes':len(b),'retrievedAt':RESEARCH_RETRIEVED_AT,'sha256':hashlib.sha256(b).hexdigest(),'status':'ok'}
 except Exception as e: result={'name':name,'url':url,'status':'error','error':str(e)}
 print(json.dumps(result),flush=True)
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 results=list(pool.map(get,urls.items()))
(D/'geometry_downloads.json').write_text(json.dumps(results,indent=2))
