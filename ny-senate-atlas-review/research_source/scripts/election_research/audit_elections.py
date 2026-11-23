
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import json,math,hashlib,re,unicodedata,collections
p=(RESEARCH_ROOT / 'election_research')
ep=p/'senate_elections_2026.json';data=json.loads(ep.read_text());ds=data['districts']
hist=json.loads((p/'senate_elections_2024.json').read_text())
prim=json.loads((p/'senate_primaries_2026.json').read_text())
directory=json.loads((p/'district_counties_official.json').read_text())
errors=[];checks=collections.Counter();warnings=[]
def check(condition,label,detail=None):
 checks[label]+=1
 if not condition:errors.append({'check':label,'detail':detail})
def norm(s):return re.sub('[^a-z]','',unicodedata.normalize('NFKD',s.lower()))
check([d['district'] for d in ds]==list(range(1,64)),'all63_unique_current_districts')
check(sum(len(d['candidates']) for d in ds)==112,'all112_named_candidates')
for d in ds:
 n=d['district'];cs=d['candidates'];v=d['validVotes'];other=d['otherBallots']
 check([c['votes'] for c in cs]==sorted([c['votes'] for c in cs],reverse=True),'current_candidates_sorted',n)
 check(sum(c['votes'] for c in cs)+other['write_in']==v,'current_valid_vote_denominator',n)
 check(v+other['blank']+other['void']==d['totalBallots'],'current_ballots_reconcile',n)
 check(d['leadingCandidate']==cs[0]['name'],'current_leader',n)
 check(d['leadingParty']==cs[0]['party'],'current_leading_party',n)
 check('Unofficial' in d['status'],'current_not_certified',n)
 for c in cs:
  check(sum(x['votes'] for x in c['ballotLines'])==c['votes'],'fusion_vote_lines_reconcile',(n,c['name']))
  check(abs(c['shareOfValidVotes']-c['votes']/v*100)<=0.0051,'current_valid_vote_share',(n,c['name']))
  check(abs(c['shareOfAllBallots']-c['votes']/d['totalBallots']*100)<=0.0051,'official_all_ballot_share',(n,c['name']))
 if len(cs)>1:
  check(d['leadVotes']==cs[0]['votes']-cs[1]['votes'],'current_margin_votes',n)
  check(abs(d['leadPercentagePoints']-d['leadVotes']/v*100)<=0.0051,'current_margin_percentage',n)
 else:check(d['leadPercentagePoints'] is None,'unopposed_has_no_named_runner_margin',n)
 check(d['incumbentOnPrintedGeneralBallot']==any(c['incumbent'] for c in cs),'incumbent_ballot_flag',n)
 dr=directory['districts'][n-1]
 check(norm(dr['memberAtSourceDate'].split(',')[0]) in norm(d['incumbent']['name']),'pre_election_official_incumbent',n)
 check(d['electionDistrictsReporting']<=d['electionDistrictsTotal'],'reporting_counter_bounds',n)
 check(d['reportingPercent']==round(d['electionDistrictsReporting']/d['electionDistrictsTotal']*100,2),'reporting_percent_math',n)
 if d['electionDistrictsReporting']==0 and d['totalBallots']>0:warnings.append({'district':n,'kind':'official_source_counter_conflict','note':'BOE displays zero election districts reporting alongside nonzero votes; retain exact source and explain.', 'ballots':d['totalBallots']})
 h=d['history2024'];check(h==hist['districts'][n-1],'embedded_history_matches_standalone',n)
 hc=h['candidates'];hv=h['validVotes']
 check(h['winner']==hc[0]['name'],'historical_winner_is_districtwide_leader',n)
 check(sum(c['winner'] for c in hc)==1 and hc[0]['winner'],'historical_single_district_winner',n)
 check(sum(c['votes'] for c in hc)+h['otherBallots'].get('scattering',0)==hv,'historical_valid_vote_denominator',n)
 check(sum(c['votes'] for c in hc)+sum(h['otherBallots'].values())==h['totalBallots'],'historical_ballots_reconcile',n)
 for c in hc:
  check(sum(x['votes'] for x in c['ballotLines'])==c['votes'],'historical_fusion_lines',(n,c['name']))
  check(abs(c['shareOfValidVotes']-c['votes']/hv*100)<=0.0051,'historical_valid_vote_share',(n,c['name']))
 if len(hc)>1:
  check(h['marginVotes']==hc[0]['votes']-hc[1]['votes'],'historical_margin_votes',n)
  check(abs(h['marginPercentagePoints']-h['marginVotes']/hv*100)<=0.0051,'historical_margin_percentage',n)
 else:check(h['marginVotes'] is None and h['marginPercentagePoints'] is None,'historical_unopposed_margin',n)
for c in prim['contests']:
 cs=c['candidates'];n=c['district']
 check([x['votes'] for x in cs]==sorted([x['votes'] for x in cs],reverse=True),'primary_sorted',n)
 check(sum(x['winner'] for x in cs)==1 and cs[0]['winner'],'primary_districtwide_winner',n)
 check(sum(x['votes'] for x in cs)+sum(c['otherBallots'].values())==c['totalBallots'],'primary_ballots_reconcile',n)
check(not any(c['incumbent'] for c in ds[11]['candidates']) and ds[11]['incumbent']['name']=='Vacant at election','district12_vacancy_correct')
check(ds[62]['candidates'][0]['incumbent'],'district63_baskin_alias_correct')
report={'status':'passed' if not errors else 'failed','checkedAt':'2026-11-22','dataSha256':hashlib.sha256(ep.read_bytes()).hexdigest(),'checks':dict(checks),'errors':errors,'warnings':warnings,'preElectionDirectoryUrl':directory['meta']['sourceUrl'],'preElectionDirectoryDate':directory['meta']['sourceDate'],'historicalWinnerMethod':'Ranked districtwide totals across all counties; county is_winner field is not used.','correctedHistoricalWinnerDistricts':[11,12,23,40,43,48],'correctedPrimaryWinnerDistricts':[51],'currentLeadCounts':dict(collections.Counter(d['leadingParty'] for d in ds)),'historicalWinnerPartyCounts':dict(collections.Counter(d['candidates'][0]['ballotLines'][0]['party'] for d in hist['districts']))}
(p/'election_data_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
