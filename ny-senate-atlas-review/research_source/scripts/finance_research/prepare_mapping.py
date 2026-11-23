
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

import json,pathlib,re,unicodedata
BASE=(RESEARCH_ROOT / 'finance_research')
elections=json.loads((RESEARCH_ROOT / 'election_research/senate_elections_2026.json').read_text())
filers=json.loads((BASE/'active_filers.json').read_text()); byid={f['filer_id']:f for f in filers}

# Reviewed committee names from official active filer registry, in the official election candidate order.
committee_ids={
1:['591082','496416'],2:['13467','591703'],3:['496633',None],4:['456367','569851'],
5:['445867','591584'],6:['456052','591168'],7:['591597','580573'],8:['527697','590937'],
9:['591120','456194'],10:['13265'],11:['445875','580695'],12:['569740','4946'],
13:[None,None],14:['483'],15:['371928',None],16:['445971'],17:['580618','496606'],
18:['382860'],19:['3467'],20:['371690'],21:['8843','591166'],22:['517207','445478'],
23:['456128',None],24:['591155','580677'],25:['456378'],26:['456326',None],27:['319624',None],
28:['371436',None],29:['9909'],30:['414451'],31:['517368'],32:['404039'],33:['506847'],
34:['383641',None],35:['414606','580704'],36:['14797',None],37:['445903','591579'],
38:['580325','456053'],39:['549093','506855'],40:['445743','591221'],41:['506858','506818'],
42:['496616','591610',None],43:['569247','506864'],44:['590867','446000'],45:['8056','580693'],
46:['445891','591105'],47:['580669',None],48:['445982','580424'],49:['227512','591070'],
50:['445987','580454'],51:['527663','414488'],52:['456058','591247'],53:['496610','580566'],
54:['414323','528327'],55:['456325','591233'],56:['445964','414614'],57:['371726','590887'],
58:['496619',None],59:['445624'],60:['371484'],61:['569429'],62:['22460','591108'],
63:['414556','591224']}

def norm(s):return re.sub('[^a-z0-9 ]',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
def sig(s):return {t for t in norm(s).split() if len(t)>1 and t not in ['jr','sr','ii','iii']}

records=[];ids=set()
for district in elections['districts']:
    sd=district['district']; cands=district['candidates']; selection=committee_ids[sd]
    assert len(cands)==len(selection),(sd,len(cands),len(selection))
    for cand,cid in zip(cands,selection):
        token=sig(cand['name'])
        candidates=[f for f in filers if f.get('office_desc')=='State Senator' and f.get('district')==str(sd)]
        scored=sorted([(len(token & sig(f['filer_name'])),f) for f in candidates],key=lambda p:p[0],reverse=True)
        direct=[]
        if scored and scored[0][0]>=2:
            if len(scored)==1 or scored[0][0]>scored[1][0]:direct=[scored[0][1]['filer_id']]
        fs=[byid[fid] for fid in ([cid] if cid else []) + direct]
        for f in fs:ids.add(f['filer_id'])
        rec={'district':sd,'candidate':cand['name'],'committeeFilerId':cid,'candidateFilerIds':direct,
             'filers':fs,'mappingBasis':'Official BOE active filer register: candidate office/district/name and reviewed committee name.',
             'mappingStatus':'reviewed_name_match' if cid else 'candidate_direct_filings_only' if direct else 'unresolved'}
        records.append(rec)
        print(sd,cand['name'],'=>',[(f['filer_id'],f['filer_name']) for f in fs])
(BASE/'candidate_filer_mapping.json').write_text(json.dumps(records,indent=2))
(BASE/'selected_filer_ids.json').write_text(json.dumps(sorted(ids,key=int)))
print('Candidates',len(records),'Committee matches',sum(bool(r['committeeFilerId']) for r in records),'Filers',len(ids))
