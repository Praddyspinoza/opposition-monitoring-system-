
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

import ast, collections, hashlib, json, pathlib, re, unicodedata

ROOT=RESEARCH_ROOT
OUT=ROOT/'v5_data/issues'
HANDOFF=ROOT/'v5_reference/handoff/The_Sixty_Three_handoff'
NOW='2026-11-23'
src=(HANDOFF/'src/dash.tsx').read_text()
def const(name):
    m=re.search(r'const '+name+r'\s*:[^\n=]+?\s*=\s*',src)
    return json.JSONDecoder().raw_decode(src[m.end():])[0]
v2={x.targets[0].id:ast.literal_eval(x.value) for x in ast.parse((HANDOFF/'v2/issues_v2.py').read_text()).body if isinstance(x,ast.Assign)}
elections=json.loads((ROOT/'election_research/senate_elections_2026.json').read_text())['districts']
by_sd={x['district']:x for x in elections}
corrected={x['id']:x for x in json.loads((ROOT/'dossier_research/issues_corrected.json').read_text())}
sources=[]
for row in const('SRC'):
    sid,title,pub,date,url,scope,topic,typ=row
    sources.append(dict(id=sid,title=title,publisher=pub,publishedAt=date,sourceUrl=url,districtScope=scope,topics=topic.split(','),evidenceType=typ,verificationStatus='Imported source reference; not independently reopened during this extraction',importedAt=NOW))
for row in v2['W']:
    sid,title,pub,date,url,typ=row
    sources.append(dict(id=sid,title=title,publisher=pub,publishedAt=date,sourceUrl=url,evidenceType=typ,verificationStatus='Imported v2 source reference; not independently reopened during this extraction',importedAt=NOW))
source_by_id={s['id']:s for s in sources}
source_by_id['S54']['limitation']='Compilation homepage URL. Original questionnaire/campaign permalinks were not preserved in the handoff; candidate statements below retain that limitation.'
def norm(s):
    return re.sub(r'[^a-z0-9 ]',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
def candidates(sd,text):
    t=' '+norm(text)+' '
    found=[]
    for c in by_sd[sd]['candidates']:
        n=c['name'];parts=norm(n).split();tail=parts[-1] if parts else ''
        if tail in ('jr','sr','ii','iii'):tail=parts[-2]
        if len(tail)<=2:
            if re.search(r'(?<!\w)'+re.escape(parts[-1].capitalize())+r'(?=\s*(?:\(|:|supports|promised|would|said))',text):found.append(n)
        elif tail and re.search(r'\b'+re.escape(tail)+r'\b',t):found.append(n)
        elif n=='April N. McCants-Baskin' and 'baskin' in t:found.append(n)
        elif n=='Stephen T. Chan' and re.search(r'\bchan\b',t):found.append(n)
    return found
patterns={
 1:r'data.cent|morator|stamp',2:r'higher.ed|suny|cuny|college|universit|tuition|\bTAP\b|student.vot',
 3:r'immigra|sanctuar|\bICE\b|migrant',4:r'housing|zoning|\brent(?:s|er|ers|al|als)?\b|evict|home.buy|homeowner|\bCOPA\b|homeless',
 5:r'affordab|cost.of.liv|everyday.cost|grocery|grocer|costs|inflation',6:r'bail|discover|safety|\bpolice\b|policing|crime|criminal|\bHALT\b|prison|domestic.violence',
 7:r'nuclear|gas|\bCLCPA\b|climate.law|renewable|Indian.Point|energy|NY.HEAT',8:r'utilit|ratepay|grid|Con.Edison|National.Grid|electric',
 9:r'congestion|transit|\bMTA\b|transport|subway',10:r'tax|budget|state.spending',11:r'K.?12|school|pre.?K|Foundation.Aid|yeshiva|parent.*education',
 12:r'health|hospital|Medicaid|Medicare|single.payer|home.care',13:r'child.?care|pre.?K',14:r'labou?r|union|minimum.wage|1199|NYSUT|working.families.party|endorse',
 15:r'agricultur|farm|dairy',16:r'environment|water|nitrat|pollut|wetland|\bPFAS\b|waste|conservation',
 17:r'vot.*access|voting|election.law|redistrict|ballot|absentee|campaign.financ|public.match',18:r'ethic|corrupt|lobby|accountab|transparen|audit|reform.Albany',
 19:r'gun|firearm|2nd.amend|second.amend',20:r'Tonawanda|Seneca.Nation|Indigenous|tribal|Native.American|\bSTAMP\b'}
codes={'dc':1,'edu':2,'imm':3,'aff':5,'safety':6}
types={'C':'Candidate position','N':'Local reporting','D':'Demographic context','P':'Regional or statewide polling','X':'Documented research gap'}
def classify(code,text):
    found=[i for i,p in patterns.items() if re.search(p,text,re.I)]
    base=codes[code]
    if base==2 and re.search(r'K.?12|nonpublic|pre.?K|school.meal',text,re.I) and re.search(r'no.higher|no.SUNY|higher.ed.specifics',text,re.I):
        found=[x for x in found if x!=2]
        found.append(11)
    elif base not in found:found.insert(0,base)
    return sorted(set(found))
def source_ids(text):
    ids=[]
    for a,b,tail in re.findall(r'\b([SW])(\d+)(?:[–-](?:[SW])?(\d+))?',text):
        ids.extend(a+str(x) for x in range(int(b),int(tail or b)+1))
    return list(dict.fromkeys(x for x in ids if x in source_by_id))
raw=[];seen=set()
for block in ['EV','EV2','EV3','EV4','EV5','EV6']:
    for sd,sections in const(block).items():
        for code,items in sections.items():
            for typ,txt,sids in items:
                sd=int(sd);key=(sd,code,typ,txt,tuple(sids))
                if key in seen:continue
                seen.add(key)
                urls=list(dict.fromkeys(source_by_id[x]['sourceUrl'] for x in sids if x in source_by_id))
                names=candidates(sd,txt)
                isgap=typ=='X'
                rec=dict(id='ev-'+hashlib.sha256(repr(key).encode()).hexdigest()[:12],district=sd,candidate=names[0] if len(names)==1 else None,candidates=names,
                         title=txt.split('. ')[0][:150],summary=txt,evidenceType=types[typ],evidenceCode=typ,recordType='research_gap' if isgap else 'district_evidence',
                         sourceUrl=urls[0] if urls else None,sourceUrls=urls,sourceIds=sids,publishedAt=None,
                         sourceDates=[{'sourceId':x,'publishedAt':source_by_id[x]['publishedAt']} for x in sids if x in source_by_id],
                         retrievedAt=None,importedAt=NOW,handoffSnapshotAt='2026-11-20',freshlyVerified=False,isGap=isgap,originalIssueCode=code,
                         issueIds=classify(code,txt),associationMethod='Topic tagging of explicit text from supplied district evidence; candidate matching restricted to names in the same district general-election record',
                         provenance={'file':'src/dash.tsx','block':block},limitations=[])
                if 'S54' in sids:rec['limitations'].append(source_by_id['S54']['limitation'])
                if len(names)>1:rec['limitations'].append('The source paragraph mentions several candidates; read the named clauses before attributing a particular position.')
                if typ=='P':rec['limitations'].append('Regional/statewide polling is not district public opinion.')
                if typ=='D':rec['limitations'].append('Demographic context is not measured political opinion or voting behavior.')
                raw.append(rec)
issues=[]
for row in v2['IB']:
    no,title,definition,why,where,metrics,srcs,tags,blocs,gaps=row
    iid=int(no);sids=source_ids(srcs);urlrefs=[source_by_id[x]['sourceUrl'] for x in sids]
    assoc=corrected.get(iid,{}).get('district_mentions',[])
    item=dict(id=iid,title=title,definition=definition,description=definition,whyItMattered=why,regionsAndDistricts=where,metrics=metrics,sourceReferenceText=srcs,sourceIds=sids,
              sourceUrls=urlrefs,evidenceLabels=tags,communityContext=blocs,knownGaps=gaps,handoffSnapshotAt='2026-11-20',freshlyVerified=False,
              districtAssociations=assoc,districtAssociationMethod='Master-plan contextual mentions; not a candidate position or measured district opinion',
              records=[r for r in raw if iid in r['issueIds']],officialSources=[],legislationIds=[])
    if not item['records']:
        item['records'].append(dict(id=f'context-issue-{iid}',district=None,candidate=None,candidates=[],title='Master-plan context',summary=where,evidenceType='Supplied research context',recordType='plan_context',sourceUrl=urlrefs[0] if urlrefs else None,sourceUrls=urlrefs,sourceIds=sids,publishedAt=None,retrievedAt=None,importedAt=NOW,handoffSnapshotAt='2026-11-20',freshlyVerified=False,isGap=False,issueIds=[iid],limitations=['Imported research context; underlying claims and links are not all independently refreshed.']))
    issues.append(item)
coverage=[]
for sd in range(1,64):
    rs=[r for r in raw if r['district']==sd]
    ev=[r for r in rs if not r['isGap']]
    coverage.append(dict(district=sd,recordCount=len(rs),evidenceCount=len(ev),gapCount=sum(r['isGap'] for r in rs),candidatePositionCount=sum(r['evidenceCode']=='C' for r in rs),
        coveredIssueIds=sorted(set(i for r in ev for i in r['issueIds'])),candidateNames=sorted(set(c for r in ev for c in r['candidates'])),freshlyVerifiedEvidenceCount=0,
        note='Counts distinguish preserved district evidence from explicit research gaps. Evidence freshness is separately recorded.'))
data=dict(meta=dict(title='NY Senate issue and legislative evidence',builtAt=NOW,handoffSnapshotAt='2026-11-20',issuesCount=len(issues),districtsCount=63,
         rawDistrictRecords=len(raw),districtEvidenceCount=sum(not r['isGap'] for r in raw),explicitGapCount=sum(r['isGap'] for r in raw),
         candidatePositionRecords=sum(r['evidenceCode']=='C' for r in raw),freshLegislativeRecords=0,
         status='District evidence imported with original provenance; official legislation enrichment in progress',
         methodology='Candidate names match the independently refreshed district general-election dataset. Imported evidence retains handoff dates. No demographic proxy or regional poll is treated as district sentiment. Legislative activity is distinct from campaign position.',
         limitations=['S54 is a compilation homepage, not an exact original questionnaire permalink.','No inference is made about public opinion from issue-evidence counts.','2026 election totals remain in the independent BOE dataset and are not overwritten by the handoff.']),
         issues=issues,evidence=raw,sources=sources,legislation=[],districtCoverage=coverage,profiles=[])
(OUT/'normalized.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(OUT/'raw_candidate_evidence.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2))
print(json.dumps(data['meta'],indent=2));print('Issue record counts:',[(x['id'],len(x['records'])) for x in issues])
