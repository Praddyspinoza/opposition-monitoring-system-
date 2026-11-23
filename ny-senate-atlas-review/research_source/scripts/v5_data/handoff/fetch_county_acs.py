
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
from urllib.parse import urlencode
import urllib.request,json,concurrent.futures,hashlib
OUT=(RESEARCH_ROOT / 'v5_data/handoff/raw')
fields=['NAME']+[f'B07004{grp}_{col}{typ}' for grp in ['H','B','D','I'] for col in ['001','005','006'] for typ in ['E','M']]+[f'{tab}_{col}{typ}' for tab,col in [('B25004','006'),('B25002','001')] for typ in ['E','M']]
hfields=['NAME']+[f'{tab}_{col}{typ}' for tab,col in [('B25004','006'),('B25002','001')] for typ in ['E','M']]
qs={'county_mobility_housing':{'get':','.join(fields),'for':'county:*','in':'state:36'},'east_end_housing':{'get':','.join(hfields),'for':'county subdivision:*','in':'state:36 county:103'},'state_housing':{'get':','.join(hfields),'for':'state:36'}}
def run(item):
 name,params=item;url='https://api.census.gov/data/2024/acs/acs5?'+urlencode(params);p=OUT/(name+'.json')
 try:
  b=urllib.request.urlopen(url,timeout=75).read();j=json.loads(b);p.write_bytes(b);r={'file':p.name,'url':url,'rows':len(j)-1,'status':'ok','sha256':hashlib.sha256(b).hexdigest(),'retrievedAt':RESEARCH_RETRIEVED_AT}
 except Exception as e:r={'file':p.name,'url':url,'status':'error','error':str(e)}
 print(json.dumps(r),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:r=list(pool.map(run,qs.items()))
(OUT/'acs_downloads.json').write_text(json.dumps(r,indent=2))
