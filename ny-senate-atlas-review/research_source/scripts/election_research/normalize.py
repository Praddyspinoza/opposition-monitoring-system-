
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import json,re,unicodedata
p=(RESEARCH_ROOT / 'election_research')
s=(p/'official_enr_2026.md').read_text()
starts=list(re.finditer(r'(\d+)(?:st|nd|rd|th) Senate District > All Counties \(Active Registered Voters: ([\d,]+)\) \| Election Districts Reporting: ([\d,]+) of ([\d,]+)',s))
num=lambda x:int(x.replace(',',''))
rs=json.loads((p/'roster_raw_0.json').read_text())
rows=re.findall(r'## ([^\n]+)\n+\(([^)]+)\)\n+(\d+)(?:st|nd|rd|th) District',rs['text'])
links=[x for x in rs['links'] if '/senators/' in x]
assert len(rows)==len(links)==63
roster={int(n):{'district':int(n),'name':name.removeprefix('Mr. '),'parties':parties.split(', '),'profileUrl':links[i],'sourceUrl':rs['url'],'sourceStatus':'current official roster; serving term before 2027'} for i,(name,parties,n) in enumerate(rows)}
norm=lambda x:[t for t in re.sub('[^a-z ]','',unicodedata.normalize('NFKD',x.lower())).split() if t not in ['jr','sr','iii','ii','iv']]
out=[]
for idx,m in enumerate(starts):
 n,registered,reporting,total=map(num,m.groups())
 end=starts[idx+1].start() if idx+1<len(starts) else s.index('1st Assembly District',m.end())
 block=s[m.end():end]
 candidates=[];other={};totals=None
 for line in block.splitlines():
  a=[x.strip() for x in line.strip().strip('|').split('|')]
  if not a:continue
  if a[0]=='Total Votes':totals=num(a[-1]);break
  if a[0] in ('Blank','Void','Write-in'):
   other[a[0].lower().replace('-','_')]=num(a[-1]);continue
  if len(a)==8 and re.fullmatch(r'[\d,]+',a[4]) and re.fullmatch(r'[\d,]+',a[7]):
   tokens=norm(a[0]);rt=norm(roster[n]['name']);match=tokens[-1]==rt[-1] or (n==63 and a[0]=='April N. McCants-Baskin')
   c={'name':a[0],'party':a[1],'ballotLines':[{'party':a[1],'votes':num(a[4])}],'votes':num(a[7]),'shareOfAllBallots':float(a[6].replace('%','').strip()),'incumbent':match}
   candidates.append(c)
  elif len(a)==7 and re.fullmatch(r'[\d,]+',a[3]) and candidates:
   candidates[-1]['ballotLines'].append({'party':a[0],'votes':num(a[3])})
 assert totals is not None and len(candidates)>0,(n,candidates,totals)
 valid=sum(c['votes'] for c in candidates)+other.get('write_in',0)
 for c in candidates:
  c['shareOfValidVotes']=round(c['votes']/valid*100,2)
  if n==12:c['incumbent']=False
  assert sum(x['votes'] for x in c['ballotLines'])==c['votes'],(n,c)
 ranked=sorted(candidates,key=lambda c:c['votes'],reverse=True)
 for i,c in enumerate(ranked):c['resultStatus']='Leading — unofficial' if i==0 else 'Trailing — unofficial'
 assert sum(c['votes'] for c in candidates)+sum(other.values())==totals,(n,totals,candidates,other)
 winner,runner=ranked[0],ranked[1] if len(ranked)>1 else None
 out.append({'district':n,'electionYear':2026,'electionDate':'2026-11-03','status':'Unofficial — not certified','sourceUpdatedAt':'2026-11-21 11:42:41 AM (as displayed by NYS BOE)','sourceUrl':'https://nyenr.elections.ny.gov/HomeNoJS.aspx','incumbent':roster[n],'candidates':ranked,'leadingCandidate':winner['name'],'leadingParty':winner['party'],'leadVotes':winner['votes']-(runner['votes'] if runner else other.get('write_in',0)),'leadPercentagePoints':round((winner['votes']-runner['votes'])/valid*100,2) if runner else None,'unopposedOnPrintedBallot':len(candidates)==1,'activeRegisteredVoters':registered,'totalBallots':totals,'validVotes':valid,'otherBallots':other,'electionDistrictsReporting':reporting,'electionDistrictsTotal':total,'reportingPercent':round(reporting/total*100,2),'incumbentOnPrintedGeneralBallot':any(c['incumbent'] for c in candidates),'nonContestants':[],'nonContestantsStatus':'No individual non-contesting/withdrawn-candidate claim is made without a source.'})
assert [r['district'] for r in out]==list(range(1,64))
out[11]['officialRosterEntry']=out[11]['incumbent']
out[11]['incumbent']={'district':12,'name':'Vacant at election','parties':[],'previousSenator':'Michael Gianaris','profileUrl':'https://www.nysenate.gov/senators/michael-gianaris','sourceUrl':'https://www.nysenate.gov/senators/michael-gianaris','sourceStatus':'Gianaris official former-member page records service ending August 10, 2026. Kawas is senator-elect, not the election incumbent.'}
out[11]['incumbentOnPrintedGeneralBallot']=False
data={'meta':{'title':'2026 New York State Senate unofficial general-election results','publisher':'New York State Board of Elections','retrievedOn':'2026-11-22','sourceUpdatedAt':'2026-11-21 11:42:41 AM','sourceUrl':'https://nyenr.elections.ny.gov/HomeNoJS.aspx','rosterSourceUrl':'https://www.nysenate.gov/senators-committees','status':'Unofficial; no certified winners assigned','statewideCaution':'NYS BOE states that unscanned emergency Election Day ballots from Westchester County are missing. All results remain unofficial; precinct reporting counts may be inconsistent with vote totals as reported by BOE.','voteShareMethod':'shareOfAllBallots uses official page percentage including blank/void ballots; shareOfValidVotes divides candidate vote total by all candidate votes plus aggregate write-ins.','fusionVotingMethod':'Votes aggregated across ballot lines by candidate; each ballot line is preserved.','incumbencyMethod':'Candidate matched to serving senator from current official Senate roster, not next-term winner.'},'districts':out}
(p/'senate_elections_2026.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(p/'senate_roster_2026.json').write_text(json.dumps({'meta':{'sourceUrl':rs['url'],'retrievedOn':'2026-11-22'},'senators':[roster[n] for n in sorted(roster)]},ensure_ascii=False,indent=2))
print('Districts',len(out),'Candidates',sum(len(r['candidates']) for r in out))
print('Incumbents absent from general ballot',[(r['district'],r['incumbent']['name']) for r in out if not r['incumbentOnPrintedGeneralBallot']])
print('SD43',json.dumps(out[42],ensure_ascii=False));print('Lead counts',{p:sum(r['leadingParty']==p for r in out) for p in ['DEM','REP','CON','WOR']})
