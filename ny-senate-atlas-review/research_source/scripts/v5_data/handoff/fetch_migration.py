
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import urllib.request,concurrent.futures,json,hashlib,time
OUT=(RESEARCH_ROOT / 'v5_data/handoff/raw');urls={}
# Published filenames on IRS SOI migration data pages. Preserve all six vintages separately.
for y in ['2324','2223','1819','1920','2021','2122']:
 for kind in ['stateinflow','stateoutflow','countyinflow','countyoutflow']:urls[kind+y+'.csv']='https://www.irs.gov/pub/irs-soi/'+kind+y+'.csv'
urls['coest2025.csv']='https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv'
urls['coest2019.csv']='https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/counties/totals/co-est2019-alldata.csv'
def get(pair):
 name,url=pair;p=OUT/name
 try:
  if p.exists():b=p.read_bytes()
  else:
   b=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 research-terminal'}),timeout=75).read()
   if b[:100].lstrip().lower().startswith((b'<html',b'<!doctype')):raise ValueError('HTML returned rather than CSV')
   p.write_bytes(b)
  r={'file':name,'url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'retrievedAt':RESEARCH_RETRIEVED_AT,'status':'ok'}
 except Exception as e:r={'file':name,'url':url,'status':'error','error':str(e),'retrievedAt':RESEARCH_RETRIEVED_AT}
 print(json.dumps(r),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:r=list(pool.map(get,urls.items()))
(OUT/'migration_downloads.json').write_text(json.dumps(r,indent=2))
