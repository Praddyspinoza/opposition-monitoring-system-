
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import json,re,logging
logging.getLogger('pdfminer').setLevel(logging.ERROR)
import pdfplumber
ROOT=(RESEARCH_ROOT / 'dossier_research')
PDF=(RESEARCH_ROOT / 'reference/US mid term/NY_State_Senate_Terminal_Master_Plan_v4.pdf')
DATA=json.loads((ROOT/'masterplan_embedded.json').read_text())
PAGES=DATA['pages']
registry={}
with pdfplumber.open(PDF) as doc:
 for page_no,prefix in [(67,'S'),(68,'S'),(69,'S'),(70,'S'),(77,'W'),(78,'R'),(79,'R'),(80,'V'),(81,'V')]:
  words=doc.pages[page_no-1].extract_words()
  anchors=sorted([w for w in words if re.fullmatch(prefix+r'\d+',w['text']) and w['x0']<80],key=lambda w:w['top'])
  url_words=[w for w in words if w['text'].startswith(('https://','http://'))]
  if not url_words:continue
  ux=min(w['x0'] for w in url_words)
  for ai,a in enumerate(anchors):
   low=a['top']-2; high=anchors[ai+1]['top']-2 if ai+1<len(anchors) else 807
   rows=sorted([w for w in words if w['top']>=low and w['top']<high],key=lambda w:(round(w['top'],1),w['x0']))
   u=''.join(w['text'] for w in rows if w['x0']>=ux-1)
   title=' '.join(w['text'] for w in rows if 63<w['x0']<245)
   registry[a['text']]={'id':a['text'],'url':u,'citation':title,'pdf_page':page_no,'verification':'Reference preserved from supplied master plan; not independently refreshed'}
(ROOT/'source_registry.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2))

def clean(s): return re.sub(r'\s+',' ',s).strip()
def field(body,start,end):
 m=re.search(start+r'([\s\S]*?)(?:'+end+r'|$)',body)
 return clean(m.group(1)) if m else ''
def refs(s):
 result=[]
 for m in re.finditer(r'\b([SW])(\d+)(?:[–-](?:[SW])?(\d+))?',s):
  pre,num,last=m.groups()
  for x in range(int(num),int(last or num)+1):
   tag=pre+str(x)
   if tag in registry and tag not in result:result.append(tag)
 return result

base={i:{'district':i,'region':None,'demographics':None,'issues':[],'campuses':[],'profession_highlights':[],'finance_references':[],'reference_pages':[62,63,64,76]} for i in range(1,64)}
pat=re.compile(r'^\s*(\d+)\s+(Suburbs|NYC|Upstate)\s+(Party [AB]|Uncalled \(recount\))\s+([\d,]+)\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%\s*$')
for page in [46,47]:
 for line in PAGES[page-1].splitlines():
  m=pat.match(line)
  if not m:continue
  sd,reg,seat,pop,*pct=m.groups();d=base[int(sd)];d['region']=reg
  d['demographics']={'population':int(pop.replace(',','')),
  **dict(zip(['white_non_hispanic_pct','non_white_pct','hispanic_pct','black_non_hispanic_pct','asian_non_hispanic_pct'],map(float,pct))),
  'source':{'pdf_page':page,'original':'ACS 2020–2024 five-year estimates, B03002; supplied PDF republishes Census Reporter data','collected':'2026-11-19','source_url':'https://censusreporter.org/profiles/61000US36'+sd.zfill(3)+'-state-senate-district-'+sd+'-ny/','table':'B03002','evidence':'Demographic estimate; not voting preference','limitations':'Rounded percentages from the supplied plan. Margins of error are not reproduced in this table.'}}
  d['reference_pages'].append(page)
assert all(d['demographics'] for d in base.values()),'Missing demographic rows'
for i in DATA['issues']:
 b=i['body']
 region=field(b,'REGIONS AND DISTRICTS','METRICS AND')
 source=field(b,'DATA SOURCES','EVIDENCE LABEL')
 labels=field(b,'EVIDENCE LABEL','VOTER BLOCS')
 gap=field(b,'GAPS / UNVERIFIED','NEVERMATCH')
 ids=refs(source)
 item={'id':i['id'],'title':i['title'],'pdf_page':i['pdf_page'],'district_context':region,'source_ids':ids,
 'source_links':[registry[r] for r in ids if r in registry],'source_note':source,'evidence':labels,
 'gaps':gap,'body':b,'snapshot':'2026-11-19','status':'Supplied master-plan record; candidate positions and policy assertions need source freshness review'}
 for sd in i['district_mentions']:
  if sd in base:base[sd]['issues'].append(item)
# Campuses here are the master plan's geographic references, not fresh boundary validation.
campus_map={43:['RPI','Hudson Valley Community College'],44:['Skidmore College','Union College'],45:['SUNY Plattsburgh'],46:['University at Albany'],48:['Syracuse University','SUNY Upstate Medical University','SUNY ESF'],50:['SUNY Oswego'],51:['SUNY Oneonta','SUNY Cobleskill','Hartwick College'],52:['Cornell University','Ithaca College','Binghamton University'],56:['University of Rochester'],61:['University at Buffalo — North Campus'],41:['SUNY New Paltz'],27:['New York University'],47:['New York University','Columbia University']}
for sd,names in campus_map.items():base[sd]['campuses']=[{'name':x,'pdf_page':8,'status':'Campus association documented in supplied plan; campus presence is not voter opinion'} for x in names]
# Profession context contains exact published broad ACS groups, not claims of occupations or voter behavior for named people.
prof=[
 ('Healthcare practitioners and technical occupations',[(7,11.7),(2,9.5),(9,9.3)],'C24010',56,'Share of civilian employed residents age 16+; includes doctors and nurses together.'),
 ('Healthcare support occupations',[(32,15.5),(19,13.1),(33,12.0)],'C24010',56,'Share of civilian employed residents age 16+; broad group, not a count of home health aides alone.'),
 ('Health care and social assistance industry',[(36,31.0),(19,28.5),(32,27.9)],'C24030',56,'Share of civilian employed residents age 16+.'),
 ('Computer and mathematical occupations',[(59,8.6),(27,7.2),(47,6.7)],'C24010',56,'Share of civilian employed residents age 16+; does not isolate AI engineers.'),
 ('Educational instruction and library occupations',[(52,12.3),(38,11.4),(8,11.0)],'C24010',56,'Share of civilian employed residents age 16+; broad group, not teachers alone.'),
 ('Public administration industry',[(43,10.8),(46,10.8),(45,8.1)],'C24030',57,'Share of civilian employed residents age 16+.'),
 ('Real estate and rental industry',[(28,3.6),(33,3.4),(31,3.3)],'C24030',57,'Share of civilian employed residents age 16+.'),
 ('Information industry',[(20,7.4),(59,7.3),(25,6.9)],'C24030',57,'Share of civilian employed residents age 16+.'),
 ('Arts, design, entertainment, sports and media occupations',[(59,10.0),(20,9.9),(25,9.8)],'C24010',57,'Share of civilian employed residents age 16+.'),
 ('Accommodation and food services industry',[(13,16.5),(17,11.1),(12,9.3)],'C24030',57,'Share of civilian employed residents age 16+.'),
 ('Transportation occupations',[(13,7.3),(19,7.2),(32,7.0)],'C24010',57,'Share of civilian employed residents age 16+; does not isolate gig or app delivery workers.'),
 ('Construction and extraction occupations',[(13,11.8),(3,6.7),(17,6.6)],'C24010',57,'Share of civilian employed residents age 16+.'),
 ('Professional, scientific and technical services industry',[(28,25.1),(59,23.5),(27,22.9)],'C24030',57,'Share of civilian employed residents age 16+; not a measure of small-business owners.'),
 ('Community and social service occupations',[(30,3.5),(31,3.2),(10,3.1)],'C24010',57,'Share of civilian employed residents age 16+; does not isolate clergy.'),
 ('Veterans',[(49,9.7),(58,8.3),(57,7.6)],'B21001',57,'Share of residents age 18+.'),
 ('Households with retirement income',[(60,35.1),(45,33.0),(54,33.0)],'B19059',57,'Share of households; not all retirees.'),
 ('Finance and insurance industry',[(28,17.5),(47,16.2),(27,15.9)],'C24030',58,'Share of civilian employed residents age 16+.'),
 ('Legal occupations',[(28,7.7),(47,6.2),(37,4.9)],'C24010',58,'Share of civilian employed residents age 16+.'),
 ('Age 65 and over',[(11,23.4),(41,23.2),(1,22.8)],'B01001',58,'Share of total population.')]
for name,rows,table,page,universe in prof:
 for sd,share in rows:base[sd]['profession_highlights'].append({'label':name,'value':share,'unit':'%','table':table,'universe':universe,'pdf_page':page,'collected':'2026-11-19','period':'ACS 2020–2024 five-year estimates','evidence':'Demographic estimate; not voting preference'})
# Preserve money facts exactly as reported, distinguish independent spending and public matching from candidate donations.
base[13]['finance_references'].append({'type':'Independent expenditure','text':'The plan records $781,000 in primary spending by Progress for New York. This is outside spending, not a ranked list of donations to a candidate.','amount_usd':781000,'pdf_page':16,'source_urls':['https://nysfocus.com/2026/06/24/ny-primary-election-results-dsa-state-legislature-2026','https://www.cityandstateny.com/politics/2026/06/cheat-sheet-super-pacs-2026-new-york-primaries/414191/'],'status':'Master-plan report, not refreshed'})
base[27]['finance_references'].append({'type':'Independent expenditure reference','text':'Downtown for Change IE is named in the supplied plan; no district total or donor ranking is reproduced.','pdf_page':16,'source_urls':['https://www.cityandstateny.com/politics/2026/06/cheat-sheet-super-pacs-2026-new-york-primaries/414191/'],'status':'Master-plan report, not refreshed'})
base[22]['finance_references'].append({'type':'Public matching funds','text':'The supplied plan records $375,000 in public matching funds for Caller. Public matching money is distinct from private donor contributions.','amount_usd':375000,'pdf_page':16,'source_urls':['https://pcfb.ny.gov/system/files/documents/2026/09/commissioner-report-for-the-approval-to-disburse-public-matching-funds-09.17.2026.pdf'],'status':'Master-plan report, not refreshed'})
for sd,id in [(9,74508),(38,74477),(39,74478)]:base[sd]['finance_references'].append({'type':'Campaign finance source','text':'District finance source in the supplied plan; coverage through 19 October 2026. Donor ranking is not printed in the PDF.','pdf_page':71,'source_urls':[f'https://www.transparencyusa.org/ny/race/new-york-state-senate-district-{sd}-{id}'],'status':'Reference link, not a retrieved donor dataset'})
for d in base.values():d['reference_pages']=sorted(set(d['reference_pages']+[i['pdf_page'] for i in d['issues']]+[x['pdf_page'] for x in d['profession_highlights']]))
result={'metadata':{'source':'NY_State_Senate_Terminal_Master_Plan_v4.pdf','snapshot':'2026-11-19','pages':81,'district_map_spec_pages':[59,60,61,62],'scope':'Documented master-plan evidence. Election snapshot is historical; use refreshed official election feed in preference to PDF results.','acs_status':'Direct Census 2024 ACS data query redirects to missing API key; Census Reporter API returned 403. Numeric fields below are the supplied PDF values, not a fresh data pull.','source_url':'https://censusreporter.org/','notes':['No complete ranked donor lists in PDF.','Household tables are specified but values not pulled in PDF.','No 2026 ED results or candidate media collected in PDF.','Demographics describe residents, not votes.']},'districts':list(base.values())}
(ROOT/'district_enrichment.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
requirements={'reference':'Master Plan v4, 81 pages; Section 18 is the district-map specification','right_panel':[{'tab':'Result','required':['Candidates','Votes','Margin','Called or uncalled','Source and pull date'],'pdf_page':62},{'tab':'Money','required':['Campaign receipts and expenditures','Public matching funds separately','Independent expenditures separately','Ranked donor records on explicit drill-down from public filings','Source, period and pull date'],'pdf_pages':[24,34,36,62]},{'tab':'Issues','required':['20 policy dossiers','Candidate positions','Source-backed local facts','Issue pins only with verified geocoding','Evidence label per item'],'pdf_pages':[6,7,62]},{'tab':'People','required':['Households/life stage Layer16','Race/ethnicity/ancestry/language Layer19','Professions Layer21','ACS table, universe, period and uncertainty labels'],'pdf_pages':[26,27,45,46,47,48,49,50,56,57,58,62]},{'tab':'Legislature','required':['Bill and vote records','Open Legislation source','Freshness'],'pdf_pages':[4,62]},{'tab':'Media','required':['Same slots for every candidate','Official photo with attribution/rights','Last five posts','Last floor speech','Debate link','Explicit empty state'],'pdf_pages':[63,64]},{'tab':'Sources','required':['Source per claim','Pull date','Evidence type','Gap labels','Unofficial election labels until certification'],'pdf_pages':[36,62,76]}],'geography':{'statewide':['63 real districts','North-up recognizable state outline','Selectable quantitative layer (margin, swing, ACS share)','District click opens right panel; preserve overview','63-tile index'],'district':['District outline','Election districts where available','Neighborhood/landmark names where verified','Issue pins','Public 311 counts and points where available','Compare district maps'],'pdf_pages':[59,60,61,62]},'current_gaps':{'households':'PDF lists table IDs but has no values; needs fresh pull.','donors':'No complete public-filing donor ranking in PDF; SD43/44 money specifically missing.','media':'No 2026 debate videos verified; no candidate X feed or official photos collected.','legislative_votes':'PDF marks pending.','precinct_returns':'No ED results loaded.','geocoded_pins':'No geocoded issue/Reddit points for SD17; do not fabricate.'}}
(ROOT/'requirements.json').write_text(json.dumps(requirements,ensure_ascii=False,indent=2))
print(json.dumps({'districts':len(base),'demographic_rows':sum(bool(d['demographics']) for d in base.values()),'issue_entries':sum(len(d['issues']) for d in base.values()),'profession_entries':sum(len(d['profession_highlights']) for d in base.values()),'registry_entries':len(registry),'output':str(ROOT/'district_enrichment.json')}))
print({k:registry[k] for k in ['S1','S19','S21','S54','W1','W12'] if k in registry})
