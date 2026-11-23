
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import csv,json,re,io,collections,unicodedata
p=(RESEARCH_ROOT / 'election_research')
data=json.loads((p/'senate_elections_2026.json').read_text())
history=json.loads((p/'senate_elections_2024.json').read_text())
source=json.loads((p/'archive2026_raw.json').read_text())['results'][0]
rows=[r for r in csv.DictReader(io.StringIO(source['text'])) if r['office_name']=='State Senator' and r['election_type']=='Primary']
contests=[]
for contestid in sorted(set(r['contest_id'] for r in rows)):
 rr=[r for r in rows if r['contest_id']==contestid];first=rr[0];n=int(first['district_name'])
 bycandidate={};other=collections.defaultdict(int);total=0
 for r in rr:
  name=r['candidate_name'];votes=int(r['votes'])
  if name=='Total Votes':total+=votes;continue
  if name in ['Blank','Void','Scattering']:
   other[name.lower()]+=votes;continue
  c=bycandidate.setdefault(r['candidate_id'],{'name':name,'candidateId':r['candidate_id'],'votes':0})
  c['votes']+=votes
 candidates=sorted(bycandidate.values(),key=lambda c:c['votes'],reverse=True)
 assert sum(c['votes'] for c in candidates)+sum(other.values())==total,(n,total,candidates,other)
 valid=sum(c['votes'] for c in candidates)+other.get('scattering',0)
 for i,c in enumerate(candidates):
  c['winner']=i==0
  c['shareOfValidVotes']=round(c['votes']/valid*100,2) if valid else None
  c['resultStatus']='Won primary — certified' if c['winner'] else 'Lost primary — certified'
 contests.append({'district':n,'electionDate':'2026-06-23','party':first['primary_party'],'status':'Certified primary result','candidates':candidates,'totalBallots':total,'validVotes':valid,'otherBallots':dict(other),'sourceUrl':'https://results.elections.ny.gov/search?df=2026&dt=2026'})
norm=lambda s:re.sub(r'[^a-z]','',unicodedata.normalize('NFKD',s.lower())).replace('jr','')
for d in data['districts']:
 n=d['district'];h=history['districts'][n-1]
 d['history2024']=h
 d['counties']=h['counties']
 d['countiesSourceUrl']=h['sourceUrl']
 d['countiesSourceNote']='Election-reporting counties from certified 2024 returns; use official GIS for geographic county coverage.'
 d['primaryElections']=[c for c in contests if c['district']==n]
 currentnames={norm(c['name']) for c in d['candidates']}
 previous=[]
 for contest in d['primaryElections']:
  for c in contest['candidates']:
   if not c['winner'] and norm(c['name']) not in currentnames:
    previous.append({'name':c['name'],'status':'Lost '+contest['party']+' primary; not on the printed general-election ballot','votes':c['votes'],'primaryDate':contest['electionDate'],'sourceUrl':contest['sourceUrl']})
 d['primaryNonAdvancers']=previous
 d['nonContestantsStatus']='No independently sourced withdrawal/nonparticipation entry added for this district.'
 d['incumbencyNote']='Incumbent appeared on the printed general-election ballot.' if d['incumbentOnPrintedGeneralBallot'] else 'Incumbent did not appear on the printed general-election ballot; see the documented election path.'
 if n in [13,61]:
  d['incumbencyNote']='Incumbent lost the June 23 Democratic primary and did not appear on the printed general-election ballot.'
  d['incumbencySourceUrl']='https://results.elections.ny.gov/search?df=2026&dt=2026'
 noncontesters={
  7:{'name':'Jack M. Martins','status':'Did not seek Senate reelection in 2026','sourceUrl':'https://ballotpedia.org/Jack_Martins','sourceType':'Secondary election reference'},
  8:{'name':'Alexis Weik','status':'Did not seek Senate reelection in 2026','sourceUrl':'https://ballotpedia.org/Alexis_Weik','sourceType':'Secondary election reference'},
  12:{'name':'Michael Gianaris','status':'Former senator; official service ended August 10, 2026; did not contest the November general election','sourceUrl':'https://www.nysenate.gov/senators/michael-gianaris','sourceType':'Official Senate service record and BOE general-election returns'},
  27:{'name':'Brian Kavanagh','status':'Announced February 3, 2026 that he would not seek reelection','sourceUrl':'https://www.nysenate.gov/newsroom/press-releases/2026/brian-kavanagh/statement-state-senator-brian-kavanagh','sourceType':'Official statement'},
  51:{'name':'Peter Oberacker','status':'Sought New York Congressional District 19 instead of Senate reelection','sourceUrl':'https://ballotpedia.org/Peter_Oberacker','sourceType':'Secondary election reference'}
 }
 if n in noncontesters:
  d['nonContestants']=[noncontesters[n]];d['nonContestantsStatus']='Documented non-contesting former/incumbent senator.'
  d['incumbencyNote']=noncontesters[n]['status'];d['incumbencySourceUrl']=noncontesters[n]['sourceUrl']
 if n==12:
  d['incumbencyNote']='Seat was vacant at the general election. Former senator Michael Gianaris left office August 10, 2026; Aber Kawas is not labelled an incumbent.'
data['meta']['historicalSourceUrl']=history['meta']['sourceUrl']
data['meta']['primarySourceUrl']='https://results.elections.ny.gov/search?df=2026&dt=2026'
data['meta']['incumbencyMethod']='Serving senator matched to BOE ballot names; April N. McCants-Baskin mapped to April Baskin. SD12 is vacant at election based on official Gianaris service end date; the directory entry for incoming Kawas is preserved separately, not treated as incumbency.'
(p/'senate_elections_2026.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(p/'senate_primaries_2026.json').write_text(json.dumps({'meta':{'sourceUrl':'https://results.elections.ny.gov/search?df=2026&dt=2026','csvUrl':source['url'],'status':'Certified primary elections only','retrievedOn':'2026-11-22','winnerMethod':'Ranked candidate vote totals aggregated across all reporting counties; county-level is_winner flags are NOT used for district conclusions.','voteShareMethod':'Valid votes include named candidates plus scattering/write-ins; blank/void ballots excluded.'},'contests':contests},ensure_ascii=False,indent=2))
print('Enriched63 districts; primaries',len(contests),'primary nonadvancers',sum(len(d['primaryNonAdvancers']) for d in data['districts']),'noncontesting senators',sum(len(d['nonContestants']) for d in data['districts']))
