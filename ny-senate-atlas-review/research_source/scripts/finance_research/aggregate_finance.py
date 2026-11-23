
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

import pathlib,json,collections,re,decimal,datetime,urllib.parse

BASE=(RESEARCH_ROOT / 'finance_research')
mapping=json.loads((BASE/'candidate_filer_mapping.json').read_text())
elections=json.loads((RESEARCH_ROOT / 'election_research/senate_elections_2026.json').read_text())
Decimal=decimal.Decimal
SOURCE='https://data.ny.gov/Government-Finance/Campaign-Finance-Disclosure-Reports-Data-Beginning/e9ss-239a'
FILER_SOURCE='https://data.ny.gov/Government-Finance/Campaign-Finance-Filer-Data-Beginning-1974/7x2g-h32p'
OFFICIAL_SEARCH='https://publicreporting.elections.ny.gov/ContributionsByRecipient/ContributionsByRecipient'
WINDOW='1 January 2025–22 November 2026'

# Upgrade reviewed name mappings where an official PCFB report gives the committee/candidate link.
auth={}
for filename in BASE.glob('pcfb_authorization*.json'):
    for row in json.loads(filename.read_text()):
        fid=str(row.get('filerId') or row.get('filer_id') or '')
        if fid:auth[fid]=row
for m in mapping:
    if m['committeeFilerId'] in auth:
        a=auth[m['committeeFilerId']]
        assert int(a['district'])==m['district'],(m,a)
        m['mappingStatus']='official_authorization_corroborated'
        m['mappingSource']=a['sourceUrl']
    if m['mappingStatus']=='official_authorization_corrobated':
        m['mappingStatus']='official_authorization_corroborated'

all_rows=[]; fetch_reports=[]
for path in sorted((BASE/'raw').glob('*.json')):
    if '.source.' not in path.name:
        rows=json.loads(path.read_text());assert isinstance(rows,list)
        all_rows.extend(rows)
    else: fetch_reports.append(json.loads(path.read_text()))

def disclosed_name(r):
    n=r.get('flng_ent_name') or ' '.join(r.get(k,'') for k in ['flng_ent_first_name','flng_ent_middle_name','flng_ent_last_name'])
    return re.sub(r'\s+',' ',n).strip()

def donor_key(r):return (disclosed_name(r).casefold(),r.get('cntrbr_type_desc') or {'A':'Individual / partnership','B':'Corporate','C':'Other monetary'}.get(r['filing_sched_abbrev'],'Other'))

def transaction_key(r):
    # UUID transaction identifiers persist through amendments. Legacy numeric identifiers may be reused.
    trans=r.get('trans_number') or r.get('filing_trans_id')
    if re.fullmatch(r'[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}',trans or ''):
        return ('guid',r['filer_id'],trans.upper(),r['filing_sched_abbrev'])
    return ('legacy',r['filer_id'],trans,r['filing_sched_abbrev'],r.get('sched_date'),r.get('org_amt'),donor_key(r))

dedup={}
for r in all_rows:
    k=transaction_key(r)
    if k not in dedup or int(r.get('filing_trans_id',0))>int(dedup[k].get('filing_trans_id',0)):
        dedup[k]=r
unique_rows=list(dedup.values())
reviewed_exclusions={r['filingTransId']:r for r in json.loads((BASE/'reviewed_non_donation_exclusions.json').read_text())}
public_funds=[]; non_donations=[]; by_filer=collections.defaultdict(list)
for r in unique_rows:
    name=disclosed_name(r).upper()
    reviewed=reviewed_exclusions.get(r['filing_trans_id'])
    if (reviewed and reviewed['category']=='public_matching_funds') or re.search(r'(^NYS COMPTROLLER$|^OFFICE OF THE STATE COMPTROLLER$|PUBLIC CAMPAIGN FINANCE BOARD|^NYS BOARD OF ELECTIONS$)',name):
        public_funds.append(r);continue
    if reviewed:
        non_donations.append(r);continue
    by_filer[r['filer_id']].append(r)

def data_url(filer_ids):
    where="filer_id in("+','.join(str(int(x)) for x in filer_ids)+") AND election_year>=2025 AND sched_date >= '2025-01-01T00:00:00' AND sched_date < '2026-11-23T00:00:00' AND filing_sched_abbrev in('A','B','C') AND filing_cat_desc='Itemized'"
    fields='filer_id,cand_comm_name,sched_date,filing_sched_abbrev,cntrbr_type_desc,flng_ent_name,flng_ent_first_name,flng_ent_middle_name,flng_ent_last_name,org_amt,trans_number,filing_trans_id,r_itemized'
    return 'https://data.ny.gov/resource/e9ss-239a.json?'+urllib.parse.urlencode({'$select':fields,'$where':where,'$limit':50000})

candidate_records={}; used_ids=set(); zeros=[]
for m in mapping:
    ids=[f['filer_id'] for f in m['filers']]
    used_ids.update(ids)
    rows=[r for fid in ids for r in by_filer[fid]]
    total=sum((Decimal(r['org_amt']) for r in rows),Decimal(0))
    named=collections.defaultdict(list);unitemized=Decimal(0)
    for r in rows:
        name=disclosed_name(r)
        if r.get('r_itemized')!='Y' or not name or re.search(r'^(unitemized|various|anonymous|not itemized)\b',name,re.I):
            unitemized+=Decimal(r['org_amt']);continue
        named[donor_key(r)].append(r)
    donor_rows=[]
    for key,rr in named.items():
        amt=sum((Decimal(r['org_amt']) for r in rr),Decimal(0))
        if amt<=0:continue
        latest=max(rr,key=lambda r:r['sched_date'])
        donor_rows.append({'name':disclosed_name(latest),'amount':float(amt),'type':key[1],
          'transactions':len(rr),'firstDate':min(r['sched_date'][:10] for r in rr),
          'lastDate':max(r['sched_date'][:10] for r in rr)})
    donor_rows.sort(key=lambda r:(-r['amount'],r['name'].casefold()))
    committees=[{'name':f['filer_name'],'filerId':f['filer_id'],'type':f.get('committee_type_desc') or 'Candidate filer',
        'sourceUrl':FILER_SOURCE} for f in m['filers'] if f['compliance_type_desc']=='COMMITTEE']
    contributing_committees=[c for c in committees if by_filer[c['filerId']]]
    status='Official disclosed contributions' if rows else 'No contribution records integrated'
    if not rows:zeros.append({'district':m['district'],'candidate':m['candidate'],'mappingStatus':m['mappingStatus']})
    excluded_public=sum((Decimal(r['org_amt']) for r in public_funds if r['filer_id'] in ids),Decimal(0))
    excluded_other=sum((Decimal(r['org_amt']) for r in non_donations if r['filer_id'] in ids),Decimal(0))
    notes=[]
    if not rows:
        notes.append('A donor ranking has not been verified for this candidate; this does not mean the candidate received no donations.')
    else:
        notes.append('Gross disclosed monetary contributions in the stated date window. Transfers, loans, in-kind support, independent spending, public matching funds and identified non-donation receipts are excluded; later refunds to contributors are not netted out.')
    if m['mappingStatus']!='official_authorization_corroborated' and committees:
        notes.append('Committee linked by reviewed official filer name; the committee name and ID are shown for audit.')
    if excluded_public:notes.append(f'Excluded ${excluded_public:,.2f} identifiable public matching funds recorded in a contribution schedule.')
    if excluded_other:notes.append(f'Excluded ${excluded_other:,.2f} identified recovered balances, bank credits, expense refunds or reimbursements recorded in contribution schedules.')
    rec={'name':m['candidate'],'committeeName':' / '.join(c['name'] for c in committees) or None,
        'committees':committees,'filerId':m['committeeFilerId'],'candidateFilerIds':m['candidateFilerIds'],
        'period':WINDOW,'windowStart':'2025-01-01','windowEnd':'2026-11-22','currency':'USD',
        'totalContributions':float(total) if rows else None,'transactionCount':len(rows),
        'namedDonorGroups':len(donor_rows),'unitemizedOrUnnamedAmount':float(unitemized) if rows else None,
        'donors':donor_rows[:10],'sourceUrl':data_url(ids) if ids else OFFICIAL_SEARCH,
        'publicSearchUrl':OFFICIAL_SEARCH,'status':status,'available':bool(rows),
        'lastTransactionDate':max((r['sched_date'][:10] for r in rows),default=None),
        'committeeMappingStatus':m['mappingStatus'],'committeeMappingSource':m.get('mappingSource') or FILER_SOURCE,
        'excludedPublicMatchingFunds':float(excluded_public),'excludedNonDonationReceipts':float(excluded_other),
        'excludedReceiptCount':sum(r['filer_id'] in ids for r in public_funds+non_donations),
        'note':' '.join(notes)}
    candidate_records[(m['district'],m['candidate'])]=rec

districts=[]
for d in elections['districts']:
    candidates=[candidate_records[(d['district'],c['name'])] for c in d['candidates']]
    covered=sum(bool(c['available']) for c in candidates)
    districts.append({'district':d['district'],'sourceUrl':SOURCE,'period':WINDOW,
        'totalContributions':round(sum(c['totalContributions'] or 0 for c in candidates),2) if covered else None,
        'coveredCandidates':covered,'candidateCount':len(candidates),'completeCandidateCoverage':covered==len(candidates),
        'note':f'Contribution records integrated for {covered} of {len(candidates)} general-election candidates. Totals cover the displayed committees and stated date window.',
        'candidates':candidates})

api_meta=json.loads((BASE/'base_meta.json').read_text())
updated=api_meta.get('rowsUpdatedAt')
updated_iso=datetime.datetime.fromtimestamp(updated,datetime.timezone.utc).isoformat() if updated else '2026-11-21'
selected_rows=[r for r in unique_rows if r['filer_id'] in used_ids]
meta={'title':'NYS Senate campaign donor snapshot','retrievedAt':'2026-11-22','sourceUpdatedAt':updated_iso,
    'sourceAgency':'New York State Board of Elections','sourceDataset':'e9ss-239a','sourceUrl':SOURCE,
    'filerRegisterUrl':FILER_SOURCE,'windowStart':'2025-01-01','windowEnd':'2026-11-22','period':WINDOW,
    'currency':'USD','districtCount':63,'candidateCount':len(mapping),'candidatesWithData':sum(c['available'] for c in candidate_records.values()),
    'rawRowsFetched':len(all_rows),'duplicateRowsRemoved':len(all_rows)-len(unique_rows),
    'selectedUniqueRowsBeforePublicFundExclusion':len(selected_rows),
    'selectedDonationRows':sum(c['transactionCount'] for c in candidate_records.values()),
    'excludedPublicMatchingFunds':sum(c['excludedPublicMatchingFunds'] for c in candidate_records.values()),
    'excludedNonDonationReceipts':round(sum(c['excludedNonDonationReceipts'] for c in candidate_records.values()),2),
    'excludedReceiptCount':sum(c['excludedReceiptCount'] for c in candidate_records.values()),
    'committeesWithData':len({r['filer_id'] for r in unique_rows if r['filer_id'] in used_ids}),
    'explicitOfficialCommitteeMappings':sum(m['mappingStatus']=='official_authorization_corroborated' for m in mapping),
    'methodology':[
      'Only monetary contribution Schedules A, B and C in itemized disclosure filings; transaction date 2025-01-01 through 2026-11-22, disclosure year at least 2025.',
      'Amended filings are retained. Repeated UUID transaction IDs retain the latest filing_trans_id; legacy numeric transaction IDs are deduplicated only when filer, schedule, date, amount and disclosed donor name/type also agree, since numeric IDs can be reused.',
      'Donor ranks aggregate the same disclosed donor name (case and whitespace normalized) and contributor type within the displayed candidate/committee group. Distinct people with the same disclosed name may be combined; name spelling variants are not inferred to be one person.',
      'Totals are gross disclosed monetary contributions, not net receipts or cash on hand. Unitemized/unnamed contributions are included in the total when reported but excluded from named donor rankings. Subsequent refunds to contributors are not netted out.',
      'Loans, transfers, in-kind support, independent expenditures and public matching funds are outside these donor rankings. Identifiable Comptroller public funds and transaction narratives explicitly describing recovered bank balances, bank verification credits, dividends, expense refunds, payroll-provider balance returns or reimbursements were excluded even when filed in contribution schedules.',
      'Candidate-to-committee identities use official filer names, candidate office/district records and, where available, explicit official PCFB payment-report mappings. The mapping basis is retained per candidate.',
      'No residential addresses, emails, telephone numbers, employer addresses or treasurer personal details are included.',
      'Source filings are reported by campaigns and may be amended. Missing data is not a zero-donation claim.'
    ]}
output={'meta':meta,'districts':districts}
(BASE/'atlas_finance_normalized.json').write_text(json.dumps(output,separators=(',',':'),ensure_ascii=False))
(BASE/'finance_validation.json').write_text(json.dumps({'meta':meta,'missingCandidates':zeros,'districtsWithPartialCoverage':[d['district'] for d in districts if not d['completeCandidateCoverage']]},indent=2))
assert len(districts)==63 and len(candidate_records)==112
assert all(len(c['donors'])<=10 and c['donors']==sorted(c['donors'],key=lambda x:(-x['amount'],x['name'].casefold())) for c in candidate_records.values())
assert all(sum(Decimal(str(x['amount'])) for x in c['donors'])<=Decimal(str(c['totalContributions'] or 0))+Decimal('0.02') for c in candidate_records.values())
assert not any(re.search(r'COMPTROLLER|PUBLIC CAMPAIGN FINANCE BOARD',donor['name'],re.I) for c in candidate_records.values() for donor in c['donors'])
print(json.dumps({'summary':{k:v for k,v in meta.items() if k not in ['methodology']},'output':str(BASE/'atlas_finance_normalized.json'), 'bytes':(BASE/'atlas_finance_normalized.json').stat().st_size,'missingCandidates':zeros},indent=2))
