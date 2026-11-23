
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
G={'Bronx':'05000US36005','Brooklyn':'05000US36047','Manhattan':'05000US36061','Queens':'05000US36081','Staten Island':'05000US36085','Nassau':'05000US36059','Suffolk':'05000US36103','Westchester':'05000US36119','Palm Beach FL':'05000US12099','Broward FL':'05000US12011','Miami-Dade FL':'05000US12086','Bergen NJ':'05000US34003','Southampton town':'06000US3610368473','East Hampton town':'06000US3610322194','Shelter Island town':'06000US3610366839','Southold town':'06000US3610369463','Riverhead town':'06000US3610361984','New York State':'04000US36'}
qs={'migration_acs_mobility':['B07004H','B07004B','B07004D','B07004I'],'migration_acs_housing_ancestry':['B25004','B25002','B04006','B01003']}
def run(item):
 name,tables=item;url='https://api.censusreporter.org/1.0/data/show/acs2024_5yr?'+urlencode({'table_ids':','.join(tables),'geo_ids':','.join(G.values())});p=OUT/(name+'.json')
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'TheSixtyThree-research-project public aggregate statistics'})
  b=urllib.request.urlopen(req,timeout=75).read();j=json.loads(b);assert 'data' in j,j;p.write_bytes(b);r={'file':p.name,'url':url,'geographies':len(j['data']),'tables':tables,'status':'ok','sha256':hashlib.sha256(b).hexdigest(),'retrievedAt':RESEARCH_RETRIEVED_AT,'dataOrigin':'U.S. Census Bureau ACS2020–2024 five-year, delivered through Census Reporter API mirror'}
 except Exception as e:r={'file':p.name,'url':url,'status':'error','error':str(e)}
 print(json.dumps(r),flush=True);return r
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(run,qs.items()))
(OUT/'acs_mirror_downloads.json').write_text(json.dumps({'geographies':G,'downloads':r},indent=2))
