
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import csv,json,re,collections,math
BASE=RESEARCH_ROOT;OUT=BASE/'v5_data/handoff';RAW=OUT/'raw'
YEARS=['1819','1920','2021','2122','2223','2324']; NYC={'005','047','061','081','085'}
period=lambda y:'20'+y[:2]+'–20'+y[2:]
def rows(name):
 with (RAW/name).open(encoding='utf-8-sig',errors='replace',newline='') as f:return list(csv.reader(f))[1:]
def metrics(r):return {'returns':int(r[-3]),'exemptions':int(r[-2]),'agiUsd':int(r[-1])*1000}
def total(rs):return {k:sum(metrics(r)[k] for r in rs) for k in ['returns','exemptions','agiUsd']}
def diff(a,b):return {k:a[k]-b[k] for k in a}
def flow(inn,out):return {'inflow':inn,'outflow':out,'net':diff(inn,out)}
def clean_county(s):return re.sub(r' Total Migration.*$','',s).strip()
nyc=[];nys=[];state_partners=[];county_pairs=[];county_migration=[];suffolk=[]
for y in YEARS:
 ci=[r for r in rows('countyinflow'+y+'.csv') if r[0].zfill(2)=='36'];co=[r for r in rows('countyoutflow'+y+'.csv') if r[0].zfill(2)=='36']
 for rr in [ci,co]:
  for r in rr:r[:4]=[r[0].zfill(2),r[1].zfill(3),r[2].zfill(2),r[3].zfill(3)]
 si=[r for r in rows('stateinflow'+y+'.csv') if r[0].zfill(2)=='36'];so=[r for r in rows('stateoutflow'+y+'.csv') if r[0].zfill(2)=='36']
 for rr in [si,so]:
  for r in rr:r[:2]=[r[0].zfill(2),r[1].zfill(2)]
 ni=[r for r in ci if r[1] in NYC];no=[r for r in co if r[1] in NYC]
 ii=total([r for r in ni if r[2]=='36' and r[3] in NYC and r[1]!=r[3]])
 io=total([r for r in no if r[2]=='36' and r[3] in NYC and r[1]!=r[3]])
 nius=total([r for r in ni if r[2]=='97' and r[3]=='000']);nous=total([r for r in no if r[2]=='97' and r[3]=='000'])
 nyc.append({'period':period(y),'vintage':y,'geography':'New York City, five counties combined','geographicUnit':'five-county aggregation','measure':'Domestic migration; inter-borough flows removed',**flow(diff(nius,ii),diff(nous,io)),'internalFlowsRemoved':{'inflow':ii,'outflow':io},'methodBreak':y=='2223','sourceIds':['IRS_'+y]})
 nys.append({'period':period(y),'vintage':y,'geography':'New York State','geographicUnit':'state','measure':'Domestic interstate migration',**flow(total([r for r in si if r[1]=='97']),total([r for r in so if r[1]=='97'])),'methodBreak':y=='2223','sourceIds':['IRS_'+y]})
 ii={r[1]:r for r in si if r[1]!='36' and int(r[1])<57};oo={r[1]:r for r in so if r[1]!='36' and int(r[1])<57}
 for fips in sorted(set(ii)&set(oo)):
  state_partners.append({'period':period(y),'vintage':y,'originContext':'New York State','stateFips':fips,'stateAbbreviation':ii[fips][2],'stateName':ii[fips][3],**flow(metrics(ii[fips]),metrics(oo[fips])),'sourceIds':['IRS_'+y]})
 # County totals are direct published rows, not sums of suppressed pair tables.
 c_i={r[1]:r for r in ci if r[2]=='97' and r[3]=='000'};c_o={r[1]:r for r in co if r[2]=='97' and r[3]=='000'}
 for fips in sorted(set(c_i)&set(c_o)):
  county_migration.append({'period':period(y),'vintage':y,'countyFips':'36'+fips,'countyName':clean_county(c_i[fips][5]),'geographicUnit':'county','measure':'Domestic inter-county migration',**flow(metrics(c_i[fips]),metrics(c_o[fips])),'sourceIds':['IRS_'+y]})
 # Published pair sums are lower-bound measured flows; missing cells are not treated as observed zero.
 pair_i=collections.defaultdict(list);pair_o=collections.defaultdict(list)
 for arr,target in [(ni,pair_i),(no,pair_o)]:
  for r in arr:
   if int(r[2])>=57 or r[3]=='000' or (r[2]=='36' and r[3] in NYC):continue
   target[(r[2],r[3])].append(r)
 for key in sorted(set(pair_i)|set(pair_o)):
  ins=pair_i[key];outs=pair_o[key];r=(ins or outs)[0]
  inn=total(ins) if ins else None;out=total(outs) if outs else None
  county_pairs.append({'period':period(y),'vintage':y,'originContext':'New York City','countyFips':key[0]+key[1],'countyName':r[5],'stateAbbreviation':r[4],'publishedInflow':inn,'publishedOutflow':out,'netPublished':diff(inn,out) if inn and out else None,'publishedBoroughPairs':{'inflow':len(ins),'outflow':len(outs)},'coverage':'Published county-pair flows only; suppressed or unpublished flows are not zero','sourceIds':['IRS_'+y]})
 ins=[r for r in ci if r[1]=='103' and r[2]=='36' and r[3] in NYC];outs=[r for r in co if r[1]=='103' and r[2]=='36' and r[3] in NYC]
 suffolk.append({'period':period(y),'vintage':y,'geography':'Suffolk County','geographicUnit':'county','fromNyc':total(ins),'toNyc':total(outs),'netFromNyc':diff(total(ins),total(outs)),'sourceIds':['IRS_'+y],'note':'Whole Suffolk County, not SD1 or the East End alone'})
 print(y,'NYC',nyc[-1]['net'],'NYS',nys[-1]['net'],flush=True)
def dictrows(name):
 with (RAW/name).open(encoding='latin-1',newline='') as f:return list(csv.DictReader(f))
pep25=[r for r in dictrows('coest2025.csv') if r['STATE'].zfill(2)=='36' and int(r['COUNTY'])>0]
pep19=[r for r in dictrows('coest2019.csv') if r['STATE'].zfill(2)=='36' and int(r['COUNTY'])>0]
components=[]
for vintage,rs,yrs,nat in [(2019,pep19,range(2011,2020),'NATURALINC'),(2025,pep25,range(2021,2026),'NATURALCHG')]:
 rr=[r for r in rs if r['COUNTY'].zfill(3) in NYC]
 for y in yrs:
  components.append({'year':y,'estimateVintage':vintage,'geography':'New York City, five counties combined','periodEnd':str(y)+'-07-01','domesticMigration':sum(int(r['DOMESTICMIG'+str(y)]) for r in rr),'internationalMigration':sum(int(r['INTERNATIONALMIG'+str(y)]) for r in rr),'naturalChange':sum(int(r[nat+str(y)]) for r in rr),'unit':'persons','sourceIds':['PEP_'+str(vintage)]})
county_pop=[]
for r in pep25:
 fips='36'+r['COUNTY'].zfill(3)
 series=[{'year':y,'population':int(r['POPESTIMATE'+str(y)]),'domesticMigration':int(r['DOMESTICMIG'+str(y)]),'domesticMigrationRatePer1000':float(r['RDOMESTICMIG'+str(y)]),'internationalMigration':int(r['INTERNATIONALMIG'+str(y)]),'naturalChange':int(r['NATURALCHG'+str(y)])} for y in range(2021,2026)]
 county_pop.append({'countyFips':fips,'countyName':r['CTYNAME'],'geographicUnit':'county','estimateVintage':2025,'series':series,'sourceIds':['PEP_2025']})
def norm(s):return re.sub(r'[^a-z ]','',s.lower()).strip()
county_alias={'Montogermy':'Montgomery','Genesse':'Genesee','Stueben':'Steuben'}
county_context=[]
for d in json.loads((BASE/'election_research/district_counties_official.json').read_text())['districts']:
 s=d['counties']; corrections=[]
 for a,b in county_alias.items():
  if a in s:s=s.replace(a,b);corrections.append({'sourceSpelling':a,'normalizedCounty':b})
 cs=[{'countyFips':c['countyFips'],'countyName':c['countyName']} for c in county_pop if re.search(r'\b'+re.escape(norm(c['countyName'].replace(' County','')))+r'\b',norm(s))]
 assert cs, d
 county_context.append({'district':d['district'],'countyContext':cs,'sourceDescription':d['counties'],'spellingNormalizations':corrections,'geographicCaution':'County figures describe the entire named county, including areas outside this Senate district. No population or migration allocation is inferred.','sourceIds':['SENATE_DIRECTORY_20260901']})
sources=[{'id':'IRS_'+y,'title':'IRS SOI migration '+period(y),'publisher':'Internal Revenue Service','dataVintage':period(y),'retrievedAt':'2026-11-23','url':('https://www.irs.gov/statistics/soi-tax-stats-migration-data-'+('20'+y[:2]+'-20'+y[2:])) if y in ['2223','2324'] else 'https://www.irs.gov/statistics/soi-tax-stats-migration-data','files':['https://www.irs.gov/pub/irs-soi/'+k+y+'.csv' for k in ['stateinflow','stateoutflow','countyinflow','countyoutflow']],'evidenceType':'Administrative tax-return address changes'} for y in YEARS]
sources.extend([{'id':'PEP_2025','title':'County population estimates and components, Vintage2025','publisher':'U.S. Census Bureau','releaseDate':'2026-03-26','retrievedAt':'2026-11-23','url':'https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/counties/totals/co-est2025-alldata.csv','evidenceType':'Model-based population estimates'},{'id':'PEP_2019','title':'County population estimates and components, Vintage2019','publisher':'U.S. Census Bureau','retrievedAt':'2026-11-23','url':'https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/counties/totals/co-est2019-alldata.csv','evidenceType':'Model-based population estimates'},{'id':'SENATE_DIRECTORY_20260901','title':'NYS Senate member directory, September2026','publisher':'Secretary of the New York State Senate','url':'https://www.nysenate.gov/sites/default/files/pdfs/9-2-26-member-directory.pdf','retrievedAt':'2026-11-22','sourceDate':'2026-09-01'}])
obj={'metadata':{'title':'Fresh official migration and population context','retrievedAt':'2026-11-23','latestIrsVintage':'2023–2024','irsVintages':[period(y) for y in YEARS],'geographicUnits':['state','county','five-county aggregation'],'districtCoverage':'County context links for all63 Senate districts; no district migration estimates or crosswalk allocations','definitions':{'returns':'Tax returns; approximate households, not exact household counts','exemptions':'Personal exemptions; approximate individuals covered by returns','agiUsd':'Mover adjusted gross income in year2, converted from published thousands to USD; not tax revenue','net':'Inflow minus outflow; negative means net outflow'},'limits':['IRS enhanced matching beginning2022–2023; series before and after the break are not strictly comparable.','IRS records describe tax filers and do not cover all residents.','Published county-pair flows are suppressed below reporting thresholds; missing or unpublished flows are not observed zero.','PEP2019 and PEP2025 use different census bases;2020 partial-period change is omitted.','County geography never establishes a Senate district migration flow or a migration effect on voting.']},'nyc':nyc,'newYorkState':nys,'statePartners':state_partners,'nycCountyPairs':county_pairs,'countyMigration':county_migration,'suffolkNyc':suffolk,'nycPopulationComponents':components,'countyPopulationChanges':county_pop,'districtCountyContext':county_context,'sources':sources}
(OUT/'fresh_migration.json').write_text(json.dumps(obj,separators=(',',':'),ensure_ascii=False))
print(json.dumps({'vintages':len(YEARS),'countyMigrationRows':len(county_migration),'countyPopulationSeries':len(county_pop),'countyPairs':len(county_pairs),'districtContexts':len(county_context),'bytes':(OUT/'fresh_migration.json').stat().st_size}),flush=True)
