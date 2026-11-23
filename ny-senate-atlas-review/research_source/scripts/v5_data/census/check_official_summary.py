#!/usr/bin/env python3
"""Cross-check every NY Senate district against official Census summary files.

Use normal HTTP byte ranges on the public, lexically GEO_ID-sorted table files
to avoid downloading the all-US files. This does not use the keyed data API.
"""

# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

import concurrent.futures
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=(RESEARCH_ROOT / 'v5_data/census')
UA='The Sixty-Three civic research terminal'
TARGET='610'

def get(url,start,end):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Range':f'bytes={start}-{end}'})
    with urllib.request.urlopen(req,timeout=40) as r:
        assert r.status==206, f'Expected byte range response: {r.status}'
        return r.read(),{k.lower():v for k,v in r.headers.items()}

def rows(block,start):
    lines=block.decode('utf-8').splitlines()
    return lines[1:-1] if start else lines[:-1]

def check(table):
    url=f'https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-{table.lower()}.dat'
    beginning,h=get(url,0,8191)
    total=int(h['content-range'].split('/')[-1])
    header=beginning.decode().splitlines()[0]
    lo,hi=0,total-1
    calls=1
    found=None
    while hi-lo>8192:
        mid=(lo+hi)//2
        block,_=get(url,mid,min(mid+8191,total-1));calls+=1
        rr=rows(block,mid)
        first=rr[0].split('|',1)[0]
        last=rr[-1].split('|',1)[0]
        if TARGET<first:
            hi=mid
        elif TARGET>last:
            lo=mid+len(block)-len(rr[-1])-100
        else:
            found=mid
            break
    pos=found if found is not None else lo
    start=max(0,pos-16384)
    end=min(total-1,(found if found is not None else hi)+700000)
    block,h=get(url,start,end);calls+=1
    ny=[line for line in rows(block,start) if re.match(r'^610[A-Z0-9]{4}US36\d{3}\|',line)]
    assert len(ny)==63,(table,len(ny),start,end)
    content=header+'\n'+'\n'.join(ny)+'\n'
    path=ROOT/'raw'/f'official_summary_extract_{table}.psv'
    path.write_text(content)
    columns=header.split('|')
    raw=json.loads((ROOT/'raw'/f'{table}.json').read_text())
    mismatch=[]
    for line in ny:
        values=dict(zip(columns,line.split('|')))
        district=int(values['GEO_ID'][-3:])
        cr=raw['data'][f'61000US36{district:03d}'][table]
        for k,v in values.items():
            if k=='GEO_ID':continue
            field,number=k.split('_')[1][0],k[-3:]
            expected=cr['estimate' if field=='E' else 'error'][f'{table}{number}']
            official=float(v) if v.strip() else None
            if expected is None and (official is None or official<0):continue
            if official!=expected:
                mismatch.append({'district':district,'cell':k,'official':official,'reporter':expected})
    return {'table':table,'sourceUrl':url,'districts':63,'fieldsPerDistrict':len(columns)-1,
            'mismatches':mismatch,'httpRangeRequests':calls,'officialFileBytes':total,
            'extractFile':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(content.encode()).hexdigest(),
            'retrievedAt':datetime.now(timezone.utc).isoformat(),'lastModified':h.get('last-modified')}

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        checks=list(pool.map(check,['B01003','B19013','B11001']))
    out={'method':'Official public Census table-based summary-file HTTP byte-range extraction; all63 NY Senate rows checked against Census Reporter estimate and MOE cells.',
         'checks':checks,'allMatch':all(not c['mismatches'] for c in checks)}
    (ROOT/'official_crosscheck.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
