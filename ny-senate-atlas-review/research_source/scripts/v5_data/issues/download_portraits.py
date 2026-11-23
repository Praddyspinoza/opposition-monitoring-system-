
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

import concurrent.futures,json,pathlib,urllib.request,hashlib
P=(RESEARCH_ROOT / 'v5_data/issues');D=P/'portraits';D.mkdir(exist_ok=True)
pro=json.loads((P/'official_profiles.json').read_text())
def fetch(p):
 u=p['headshotUrl'];sd=p['district'];out={'district':sd,'name':p['name'],'sourceUrl':u,'profileUrl':p['headshotSourceUrl'],'attribution':p['headshotAttribution'],'license':p['imageLicense'],'policyUrl':p['imagePolicyUrl'],'retrievedAt':RESEARCH_RETRIEVED_AT}
 try:
  r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25)
  mime=r.headers.get('content-type','');b=r.read(6000000)
  if not mime.startswith('image/'):raise ValueError('Unexpected content type '+mime)
  if len(b)>=6000000:raise ValueError('Asset exceeds six MB limit')
  ext='png' if 'png' in mime else 'webp' if 'webp' in mime else 'jpg'
  filename=f'sd{sd:02d}.{ext}';(D/filename).write_bytes(b)
  out.update(status='downloaded',localPath=str(D/filename),filename=filename,bytes=len(b),mimeType=mime,sha256=hashlib.sha256(b).hexdigest())
 except Exception as e:out.update(status='unavailable',error=str(e))
 return out
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(fetch,pro['profiles']))
(P/'portraits_manifest.json').write_text(json.dumps({'retrievedAt':RESEARCH_RETRIEVED_AT,'portraits':results,'downloaded':sum(x['status']=='downloaded' for x in results),'bytes':sum(x.get('bytes',0)for x in results)},ensure_ascii=False,indent=2))
mapping={r['district']:r for r in results}
for p in pro['profiles']:
 r=mapping[p['district']]
 if r['status']=='downloaded':p['headshotLocalPath']=r['localPath'];p['headshotFilename']=r['filename']
(P/'official_profiles.json').write_text(json.dumps(pro,ensure_ascii=False,indent=2))
data=json.loads((P/'normalized.json').read_text());data['profiles']=pro['profiles'];data['meta']['downloadedHeadshotCount']=sum(x['status']=='downloaded' for x in results)
(P/'normalized.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps({'downloaded':sum(x['status']=='downloaded' for x in results),'bytes':sum(x.get('bytes',0)for x in results),'errors':[r for r in results if r['status']!='downloaded']},ensure_ascii=False))
