
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

import json, pathlib, urllib.request, urllib.parse, concurrent.futures, sys, time

BASE=(RESEARCH_ROOT / 'finance_research')
SELECT=','.join(['filer_id','cand_comm_name','election_year','filing_cat_desc','filing_sched_abbrev','filing_sched_desc','trans_number','filing_trans_id','sched_date','flng_ent_name','flng_ent_first_name','flng_ent_middle_name','flng_ent_last_name','cntrbr_type_desc','org_amt','r_itemized','r_amend'])

def fetch(ids, label):
    outfile=BASE/'raw'/f'{label}.json'
    if outfile.exists():
        j=json.loads(outfile.read_text());return {'label':label,'ids':ids,'rows':len(j),'cached':True}
    where="filer_id in("+','.join(str(int(x)) for x in ids)+") AND election_year>=2025 AND sched_date >= '2025-01-01T00:00:00' AND sched_date < '2026-11-23T00:00:00' AND filing_sched_abbrev in('A','B','C') AND filing_cat_desc='Itemized'"
    args={'$select':SELECT,'$where':where,'$limit':50000}
    url='https://data.ny.gov/resource/e9ss-239a.json?'+urllib.parse.urlencode(args)
    for attempt in range(2):
        try:
            with urllib.request.urlopen(url,timeout=75) as r:
                payload=r.read()
            j=json.loads(payload)
            if not isinstance(j,list):raise ValueError(str(j)[:300])
            if len(j)>=50000:raise ValueError('Result reached limit; split batch')
            outfile.write_text(json.dumps(j,separators=(',',':')))
            (BASE/'raw'/f'{label}.source.json').write_text(json.dumps({'url':url,'ids':ids,'retrieved':RESEARCH_RETRIEVED_AT,'rows':len(j)},indent=2))
            return {'label':label,'ids':ids,'rows':len(j),'bytes':len(payload)}
        except Exception as e:
            if attempt:return {'label':label,'ids':ids,'error':str(e)}
    return {}

if __name__=='__main__':
    (BASE/'raw').mkdir(exist_ok=True)
    ids=json.loads(pathlib.Path(sys.argv[1]).read_text())
    ids=sorted(set(str(x) for x in ids),key=int)
    batches=[ids[i:i+8] for i in range(0,len(ids),8)]
    prefix=sys.argv[2] if len(sys.argv)>2 else 'donations'
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futs={pool.submit(fetch,b,f'{prefix}_{i:02d}'):i for i,b in enumerate(batches)}
        for future in concurrent.futures.as_completed(futs):
            result=future.result();results.append(result);print(json.dumps(result),flush=True)
    (BASE/f'{prefix}_fetch_report.json').write_text(json.dumps(results,indent=2))
