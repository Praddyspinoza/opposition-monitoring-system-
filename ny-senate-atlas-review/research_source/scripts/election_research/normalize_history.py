
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import csv,json,re,io,collections
p=(RESEARCH_ROOT / 'election_research')
source=json.loads((p/'archive2024_raw.json').read_text())['results'][0]
rows=[r for r in csv.DictReader(io.StringIO(source['text'])) if r['office_name']=='State Senator' and r['election_type']=='General' and r['election_date'].startswith('2024-11-05')]
out=[]
for n in range(1,64):
 districtrows=[r for r in rows if int(r['district_name'])==n]
 bycandidate={};other=collections.defaultdict(int);counties=set();total=0
 for r in districtrows:
  name=r['candidate_name'];votes=int(r['votes']);counties.add(r['division_name'])
  if name=='Total Votes':total+=votes;continue
  if name in ['Blank','Void','Scattering']:
   other[name.lower()]+=votes;continue
  c=bycandidate.setdefault(r['candidate_id'],{'name':name,'candidateId':r['candidate_id'],'votes':0,'ballotLines':{}})
  c['votes']+=votes
  c['ballotLines'][r['candidate_party_name']]=c['ballotLines'].get(r['candidate_party_name'],0)+votes
 candidates=sorted(bycandidate.values(),key=lambda c:c['votes'],reverse=True)
 assert sum(c['votes'] for c in candidates)+sum(other.values())==total,(n,total,candidates,other)
 valid=sum(c['votes'] for c in candidates)+other.get('scattering',0)
 for i,c in enumerate(candidates):
  c['winner']=i==0
  c['shareOfValidVotes']=round(c['votes']/valid*100,2)
  c['shareOfAllBallots']=round(c['votes']/total*100,2)
  c['ballotLines']=[{'party':k,'votes':v} for k,v in c['ballotLines'].items()]
  c['resultStatus']='Won — certified' if c['winner'] else 'Lost — certified'
 winners=[c for c in candidates if c['winner']];assert len(winners)==1,(n,winners)
 out.append({'district':n,'electionYear':2024,'electionDate':'2024-11-05','status':'Certified historical result','sourceUrl':'https://results.elections.ny.gov/search?df=2024&dt=2024&p=1','candidates':candidates,'winner':winners[0]['name'],'winnerVotes':winners[0]['votes'],'totalBallots':total,'validVotes':valid,'otherBallots':dict(other),'counties':sorted(counties),'marginVotes':candidates[0]['votes']-candidates[1]['votes'] if len(candidates)>1 else None,'marginPercentagePoints':round((candidates[0]['votes']-candidates[1]['votes'])/valid*100,2) if len(candidates)>1 else None})
data={'meta':{'title':'Certified 2024 New York State Senate general-election returns','sourceUrl':'https://results.elections.ny.gov/search?df=2024&dt=2024&p=1','csvUrl':source['url'],'publisher':'NYS Board of Elections official archived results','retrievedOn':'2026-11-22','aggregation':'Sum County rows by district and candidate across fusion ballot lines. District winner is the candidate with the largest district-wide total; the CSV is_winner flag is county-level and is NOT used for district conclusions. Blank, void and scattering counted separately.','voteShareMethod':'Valid votes include all named candidates plus aggregate scattering/write-in votes and exclude blank and void ballots. Margin is first minus second named candidate divided by valid votes.','countyNote':'Counties here are election-reporting units in the 2024 official returns, not a substitute for the official GIS geography.','status':'Certified historical results; do not conflate with 2026 returns.'},'districts':out}
(p/'senate_elections_2024.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
print('2024',len(out),'districts',sum(len(d['candidates']) for d in out),'named candidates');print('SD44',out[43])
