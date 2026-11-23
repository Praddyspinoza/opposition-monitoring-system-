"""Fetch Census-origin ACS 2020–2024 tables for all NY upper-chamber districts.

Uses the documented public Census Reporter API. No credentials, private data,
headless browser or synthetic estimates. Raw responses and hashes are retained.
"""

# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import json, hashlib, time

BASE=(RESEARCH_ROOT / 'v5_data/census')
RAW=BASE/'raw'
RAW.mkdir(exist_ok=True)
TABLES=['B01003','B03002','B03001','B02015','B04006','B05006','C16001',
        'B21001','C24010','C24030','B19059','B01001','B01002','B19013',
        'B19301','B17001','B15003','B05002','B11001','B11003','B23009',
        'B08202','B12001','B25003','B25007','B25024','B25032','B19037',
        'B19131','B25070','B25064','B25077','B25004','B25002','B07003',
        'B07013','B19001','B08301']
API='https://api.censusreporter.org/1.0/data/show/acs2024_5yr'
UA='The Sixty-Three civic research terminal'

def fetch(table):
    source=API+'?'+urlencode({'table_ids':table,'geo_ids':'610|04000US36'})
    result={'table':table,'sourceUrl':source}
    for attempt in range(2):
        try:
            req=Request(source,headers={'User-Agent':UA,'Accept':'application/json'})
            with urlopen(req,timeout=50) as response:
                body=response.read()
            data=json.loads(body)
            districts={k:v for k,v in data.get('data',{}).items() if k.startswith('61000US36') and 1<=int(k[-3:])<=63}
            if len(districts)!=63:
                raise ValueError('Expected 63 NY districts, received '+str(len(districts)))
            path=RAW/(table+'.json')
            path.write_bytes(body)
            result.update(status='downloaded',districtCount=len(districts),bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),retrievedAt=datetime.now(timezone.utc).isoformat(),release=data.get('release'),title=data.get('tables',{}).get(table,{}).get('title'))
            return result
        except Exception as exc:
            result.update(status='unavailable',error=f'{type(exc).__name__}: {exc}')
            if attempt==0: time.sleep(1)
    return result

if __name__=='__main__':
    report=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fetch,t):t for t in TABLES}
        for future in as_completed(futures):
            row=future.result();report.append(row)
            print(json.dumps(row),flush=True)
            (BASE/'fetch_report.json').write_text(json.dumps(sorted(report,key=lambda r:r['table']),indent=2))
    print('Complete:',sum(r['status']=='downloaded' for r in report),'/',len(TABLES),flush=True)
