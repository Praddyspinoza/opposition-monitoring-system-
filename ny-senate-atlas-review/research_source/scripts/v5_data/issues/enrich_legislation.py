
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

import collections,datetime,hashlib,json,pathlib,re,unicodedata
P=(RESEARCH_ROOT / 'v5_data/issues');ROOT=P.parents[1];NOW='2026-11-23'
data=json.loads((P/'normalized.json').read_text())
raw={}
for f in [P/'fresh_bill_profiles_a.json',P/'fresh_bills_b.json',P/'fresh_issue_primary.json',P/'fresh_budget_current.json']:
 for x in json.loads(f.read_text())['results']:
  m=re.search(r'/bills/2025/(S\d+)',x['url'])
  if m:raw[m[1]]=x
web={}
def clean(t):return re.sub(r'【\d+†([^†】]+)(?:†[^】]*)?】',r'\1',t)
for f in sorted(P.glob('official_bill_*.txt')):
 for part in re.split(r'\n-{20,}\n',f.read_text()):
  m=re.search(r'\(https://www.nysenate.gov/legislation/bills/2025/(S\d+)[^)]*\)',part)
  if not m:continue
  v=web.setdefault(m[1],{'lines':{},'webRefs':[]})
  rr=re.search(r'【(turn\w+(?:view|search)\d+)】',part)
  if rr and rr[1] not in v['webRefs']:v['webRefs'].append(rr[1])
  for lineno,txt in re.findall(r'^L(\d+): ?(.*)$',part,re.M):v['lines'][int(lineno)]=txt
def norm(t):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode().lower())
roster=json.loads((ROOT/'election_research/senate_roster_2026.json').read_text())['senators']
elections={x['district']:x for x in json.loads((ROOT/'election_research/senate_elections_2026.json').read_text())['districts']}
lookup={}
for s in roster:
 n=s['name'];parts=re.sub(r'\b(?:Jr\.|Sr\.)','',n).strip().split();lookup[norm(parts[-1])]=s;lookup[norm(n)]=s
lookup.update({'gianaris':{'district':12,'name':'Michael Gianaris','profileUrl':'https://www.nysenate.gov/senators/michael-gianaris'},'hoylmansigal':{'district':47,'name':'Brad Hoylman-Sigal','profileUrl':'https://www.nysenate.gov/senators/brad-hoylman-sigal'},'addabboj r':next(s for s in roster if s['district']==15)})
lookup['addabbojr']=next(s for s in roster if s['district']==15);lookup['sandersjr']=next(s for s in roster if s['district']==10)
def person(name,sd=None):
 v=lookup.get(norm(name))
 if v:return {'name':v['name'],'district':v['district'],'profileUrl':v.get('profileUrl')}
 if sd:return {'name':name,'district':int(sd),'profileUrl':next((x['profileUrl'] for x in roster if x['district']==int(sd) and norm(name)==norm(x['name'])),None)}
 return {'name':name,'district':None,'profileUrl':None}
def iso(t):
 for fmt in ['%b %d, %Y','%B %d, %Y']:
  try:return datetime.datetime.strptime(t.strip(),fmt).date().isoformat()
  except ValueError:pass
 return None
issueMap={'S10642':[1,7,8,14,16],'S4781':[2],'S2235':[3],'S8612':[4],'S8623':[5],'S3670':[6,12],'S3425':[12],'S4158':[7,8],'S5533':[13],'S533':[9],'S3961':[15],'S9006':[10,11,13],'S2056':[2,17],'S3207':[16],'S6653':[2,12],'S9827':[6,19]}
leg=[];newRecords=[]
for billId,x in raw.items():
 if billId not in issueMap:continue
 w=web.get(billId,{});lineMap=w.get('lines',{});wt='\n'.join(txt for _,txt in sorted(lineMap.items()));t=x['text'];u=x['url'].split('/amendment/')[0]
 top=re.search(r'# (?:Senate|Assembly) Bill (\w+)',wt or t);active=top[1] if top else billId
 header=t.split('## Sponsored By')[0];hm=re.search(r'Legislative Session\s+(.+?)(?:\n\n|download bill)',header,re.S)
 title=re.sub(r'\s+',' ',hm[1]).strip() if hm else x.get('description') or x['title']
 sm=re.search(r'## Sponsored By\s+###\s+(.+?)\s+\(([^)]+)\)\s+(\d+)(?:st|nd|rd|th) Senate District',t,re.S)
 sponsor=person(sm[1].strip(),sm[3]) if sm else None
 statusm=re.search(r'## Current Bill Status([^\n]+)',wt or t);status=clean(statusm[1]).strip(' -') if statusm else None
 actions=[];currentDate=None
 am=re.search(r'## Actions(.*?)(?:## Votes|## co-Sponsors|## Bill Amendments|## 2025-)',wt,re.S)
 if am:
  for ln in am[1].splitlines():
   ln=clean(ln).strip();dt=re.match(r'([A-Z][a-z]{2} \d{1,2}, \d{4})\s*\|\s*(.*)',ln)
   if dt:currentDate=iso(dt[1]);actions.append({'date':currentDate,'action':dt[2]})
   elif currentDate and ln and not ln.startswith(('#','View','Date of','Senate Actions','---','*')):actions.append({'date':currentDate,'action':ln})
 cos=[]
 for co in re.finditer(r'## co-Sponsors(.*?)(?=## 2025-|$)',wt,re.S):
  coText=clean(co[1])
  for cm in re.finditer(r'###\s+([^\n]+)\s+\(([^)]+)\)\s+(?:(\d+)(?:st|nd|rd|th) )?Senate District',coText,re.S):
   pp=person(cm[1].strip(),cm[3]);
   if pp not in cos:cos.append(pp)
 # Fall back to visible official markdown when its complete list was not exposed by the search renderer.
 if not cos:
  for co in re.finditer(r'## co-Sponsors(.*?)(?=## 2025-|$)',t,re.S):
   for cm in re.finditer(r'###\s+([^\n]+)\s+\(([^)]+)\)\s+(?:(\d+)(?:st|nd|rd|th) )?Senate District',co[1],re.S):
    pp=person(cm[1].strip(),cm[3]);
    if pp not in cos:cos.append(pp)
 votes=[]
 printedVoteBills={}
 for pv in re.finditer(r'### ([A-Z][a-z]{2} \d{1,2}, \d{4}) - ([^\n]+)\s+【\d+†([AS]\d+[A-Z]?)(?:†[^】]+)?】',wt):
  printedVoteBills[(iso(pv[1]),'Floor vote' if 'Floor' in pv[2] else 'Committee vote')]=pv[3]
 for vm in re.finditer(r'### ([^\n]*?Vote): ([A-Z][a-z]{2} \d{1,2}, \d{4})\n(.*?)(?=(?:\s*[*]\s*)?### |\n## |$)',wt,re.S):
  kind,dates,body=vm.groups();group=None;members=[];totals={}
  for ln in body.splitlines():
   ln=ln.strip();g=re.fullmatch(r'(aye wr|aye|nay|absent|excused|abstained) \((\d+)\)',ln,re.I)
   if g:group={'aye wr':'ayeWithReservations'}.get(g[1].lower(),g[1].lower());totals[group]=int(g[2]);continue
   if group:
    n=re.search(r'^\*\s*【\d+†([^†】]+)(?:†[^】]*)?】',ln)
    if n:members.append({**person(n[1]),'vote':group,'nameAsPublished':n[1]})
  if totals:
   voteType='Floor vote' if 'Floor' in kind else 'Committee vote'
   votes.append({'id':billId+'-'+iso(dates)+'-'+('floor' if 'Floor' in kind else 'committee'),'date':iso(dates),'type':voteType,'billIdAsDisplayed':printedVoteBills.get((iso(dates),voteType),active),'billIdNote':'Identifier shown by the official page for this vote; the page may link historical votes to its current amendment.','committee':None if 'Floor' in kind else kind.replace(' Committee Vote','').replace(' Vote',''),
                 'totals':totals,'members':members,'memberListComplete':sum(totals.values())==len(members),'sourceUrl':u,'retrievedAt':NOW,'limitations':[] if sum(totals.values())==len(members) else ['Only the named votes retrieved from the official page are included; missing names are not inferred.']})
 # Latest summary from active amendment, preserving official rather than inferred legal status.
 summary=x.get('description') or title
 legRecord=dict(id='ny-2025-'+billId,billId=active,baseBillId=billId,session='2025–2026',title=title,summary=summary,currentStatus=status,sourceUrl=u,sourceTitle=x['title'],publisher='New York State Senate',
                evidenceType='Official legislative record',retrievedAt=NOW,publishedAt=actions[-1]['date'] if actions else None,latestAction=actions[0] if actions else None,actions=actions,sponsor=sponsor,cosponsors=cos,
                cosponsorListComplete=False,rollCalls=votes,issueIds=issueMap[billId],webRefs=w.get('webRefs',[]),freshlyVerified=True,
                statusNote='Official page status as retrieved. Legislative sponsorship and votes are separate from campaign statements; a passed chamber is not an enactment.',
                limitations=['Cosponsor list includes named official records retrieved, and may be incomplete.'])
 leg.append(legRecord)
 sourceId='NYLEG-'+billId
 data['sources']=[s for s in data['sources'] if s['id']!=sourceId]
 data['sources'].append({'id':sourceId,'title':active+' — '+title,'publisher':'New York State Senate','sourceUrl':u,'publishedAt':None,'retrievedAt':NOW,'evidenceType':'Official bill record','verificationStatus':'Official page retrieved','webRefs':w.get('webRefs',[])})
 def addRecord(p,typ,summ,pub,tag):
  sd=p.get('district') if p else None;nm=p.get('name') if p else None
  matching=[]
  if sd and nm:
   family=norm(nm.split()[-1]);matching=[c['name'] for c in elections[sd]['candidates'] if norm(c['name'])==norm(nm) or family in norm(c['name'].split()[-1])]
  rr=dict(id=sourceId+'-'+tag,district=sd,candidate=matching[0] if len(matching)==1 else nm,candidates=matching,personName=nm,
       title=active+' · '+typ,summary=summ,evidenceType=typ,recordType='official_legislation',sourceUrl=u,sourceUrls=[u],sourceIds=[sourceId],publishedAt=pub,retrievedAt=NOW,importedAt=NOW,
       freshlyVerified=True,isGap=False,issueIds=issueMap[billId],billId=active,legislationId=legRecord['id'],campaignPosition=False,associationMethod='Named official legislative activity',
       limitations=['This records official legislative activity, not a campaign pledge or district public opinion.'])
  newRecords.append(rr)
 if sponsor:addRecord(sponsor,'Bill sponsorship',sponsor['name']+' is the named sponsor of '+active+'. '+summary,None,'sponsor')
 for k,p in enumerate(cos):addRecord(p,'Bill cosponsorship',p['name']+' is listed as a cosponsor of '+active+'. '+title,None,'cosponsor-'+str(k))
 for vote in votes:
  for k,p in enumerate(vote['members']):
   label={'aye':'Aye','nay':'Nay','ayeWithReservations':'Aye with reservations','absent':'Absent','excused':'Excused','abstained':'Abstained'}[p['vote']]
   voteBill=vote['billIdAsDisplayed']
   addRecord(p,'Recorded '+vote['type'].lower(),p['name']+' — '+label+' on '+voteBill+(' (related '+active+')' if voteBill!=active else '')+' ('+vote['date']+', '+vote['type'].lower()+((', '+vote['committee']) if vote['committee'] else '')+').',vote['date'],vote['id']+'-'+str(k))
   newRecords[-1]['vote']=p['vote'];newRecords[-1]['voteType']=vote['type'];newRecords[-1]['votedBillIdAsDisplayed']=voteBill;newRecords[-1]['rollCallId']=vote['id']
data['legislation']=leg
freshAgency=[
 {'id':'NYDOL-WAGE','issueIds':[14,5],'title':'Minimum wage schedule and announced 2027 rates','sourceUrl':'https://dol.ny.gov/minimum-wage','publisher':'New York State Department of Labor','publishedAt':None,'summary':'The official schedule lists $17 per hour for New York City, Long Island and Westchester, and $16 for the remainder of the state. The page says the general rates will remain unchanged on January 1, 2027 because a statutory off-ramp applies. Home-care and tipped-worker schedules differ.','evidenceType':'Official wage schedule','scope':'Statewide and regional; not a district estimate'},
 {'id':'COELIG-2026-JULAUG','issueIds':[1,18],'title':'Preliminary July–August 2026 lobbying report','sourceUrl':'https://ethics.ny.gov/news/preliminary-lobbying-spending-july-august-2026-totaled-645-million-41-last-year','publisher':'NYS Commission on Ethics and Lobbying in Government','publishedAt':'2026-10-27','summary':'COELIG reports preliminary July–August 2026 lobbying compensation and expenses of $64.5 million. The responsible data-centre bills S10642/A11560 had 101 combined filings, the highest bill total for that period. These are lobbying disclosures, not candidate donations or evidence that lobbying determined a vote.','evidenceType':'Official preliminary lobbying disclosure','scope':'Statewide reported lobbying activity'},
 {'id':'COELIG-PORTAL','issueIds':[18],'title':'Official lobbying disclosure datasets','sourceUrl':'https://ethics.ny.gov/lobbying-data-0','publisher':'NYS Commission on Ethics and Lobbying in Government','publishedAt':None,'summary':'The Commission provides current-filings search and Open NY datasets for lobbying registrations, bi-monthly reports, client reports and related disclosed activity.','evidenceType':'Official data portal','scope':'Statewide'},
 {'id':'NYSDEC-STAMP-2021','issueIds':[20,16],'title':'STAMP wastewater permit application — historical official record','sourceUrl':'https://dec.ny.gov/news/environmental-notice-bulletin/2021-08-04/completed-application/science-technology-advanced-manufacturing-park-stamp','publisher':'New York State Department of Environmental Conservation','publishedAt':'2021-08-04','summary':'The DEC notice describes the STAMP site and proposed wastewater infrastructure near the Tonawanda Seneca Nation reservation. It records the application and public-review process as of August 4, 2021. It does not establish the current permit or litigation outcome, or community opinion.','evidenceType':'Historical official permit notice','scope':'STAMP project vicinity; historical record'}]
for x in freshAgency:
 x.update(retrievedAt=NOW,freshlyVerified=True,verificationStatus='Official source retrieved')
 data['sources']=[s for s in data['sources'] if s['id']!=x['id']];data['sources'].append(x)
 newRecords.append(dict(id=x['id'],district=None,candidate=None,candidates=[],title=x['title'],summary=x['summary'],evidenceType=x['evidenceType'],recordType='official_policy_context',sourceUrl=x['sourceUrl'],sourceUrls=[x['sourceUrl']],sourceIds=[x['id']],publishedAt=x['publishedAt'],retrievedAt=NOW,importedAt=NOW,freshlyVerified=True,isGap=False,issueIds=x['issueIds'],scope=x['scope'],limitations=[]))
# Preserve raw handoff evidence while linking newly verified legislative records into every issue filter.
rawEvidence=[r for r in data['evidence'] if r.get('recordType') not in ('official_legislation','official_policy_context')]
data['evidence']=rawEvidence+newRecords
for issue in data['issues']:
 issue['records']=[r for r in issue['records'] if r.get('recordType') not in ('official_legislation','official_policy_context')]+[r for r in newRecords if issue['id'] in r['issueIds']]
 issue['officialSources']=[{'id':s['id'],'title':s['title'],'sourceUrl':s['sourceUrl'],'publisher':s['publisher'],'retrievedAt':NOW} for s in data['sources'] if s.get('id','').startswith(('NYLEG-','NYDOL-','COELIG-','NYSDEC-')) and ((s.get('id','').startswith('NYLEG-') and issue['id'] in issueMap.get(s['id'].replace('NYLEG-',''),[])) or issue['id'] in s.get('issueIds',[]))]
 issue['legislationIds']=[l['id'] for l in leg if issue['id'] in l['issueIds']]
 issue['coverage']={'totalRecords':len(issue['records']),'candidatePositionRecords':sum(r.get('evidenceCode')=='C' for r in issue['records']),'researchGapRecords':sum(r.get('isGap',False) for r in issue['records']),
   'freshOfficialRecords':sum(r.get('freshlyVerified',False) for r in issue['records']),'districtsWithEvidence':sorted(set(r['district'] for r in issue['records'] if r.get('district') and not r.get('isGap',False)))}
for dc in data['districtCoverage']:
 fresh=[r for r in newRecords if r['district']==dc['district']]
 dc['freshlyVerifiedEvidenceCount']=len(fresh);dc['officialLegislativeRecordCount']=sum(r['recordType']=='official_legislation' for r in fresh)
 dc['coveredIssueIds']=sorted(set(dc['coveredIssueIds']+[i for r in fresh for i in r['issueIds']]))
data['meta'].update(freshLegislativeRecords=len(leg),freshOfficialEvidenceRecords=len(newRecords),totalEvidenceRecords=len(data['evidence']),officialIssuesCovered=sum(bool(i['officialSources'])for i in data['issues']),
 status='Imported district evidence plus newly retrieved official bill, roll-call, profile and policy records; source and event dates remain distinct',
 rollCallEvents=sum(len(x['rollCalls']) for x in leg),namedRollCallEntries=sum(len(v['members'])for l in leg for v in l['rollCalls']))
(P/'normalized.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(P/'official_legislation.json').write_text(json.dumps({'meta':{'retrievedAt':NOW,'count':len(leg),'note':'Official status is retained as shown; missing member votes and cosponsors are never inferred.'},'legislation':leg},ensure_ascii=False,indent=2))
print(json.dumps(data['meta'],ensure_ascii=False,indent=2))
print('BILLS',[(x['billId'],x['currentStatus'],len(x['actions']),len(x['cosponsors']),[(v['date'],v['totals'],len(v['members']),v['memberListComplete'])for v in x['rollCalls']])for x in leg])
print('No official issue sources:',[i['id'] for i in data['issues'] if not i['officialSources']])
