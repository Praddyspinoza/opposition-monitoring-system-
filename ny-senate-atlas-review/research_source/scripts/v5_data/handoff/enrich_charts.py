
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import json,re,math
BASE=RESEARCH_ROOT;OUT=BASE/'v5_data/handoff';RAW=OUT/'raw'
p=json.loads((OUT/'normalized.json').read_text());fresh=json.loads((OUT/'fresh_migration.json').read_text());tables=p['migration']['tables']
charts={c['id']:c for c in p['migration']['charts']}
def series(label,unit,points):return {'label':label,'unit':unit,'points':points}
def hist(r):return r.get('vintage')!='2324'
def rows(r):return [{'period':x['period'],'value':x['net'][r]} for x in fresh['nyc'] if hist(x)]
c1={'geography':'New York City, five boroughs combined','geographicUnit':'five-county aggregation','measure':'Net domestic tax-return migration, excluding inter-borough moves','series':[series('Net domestic tax returns','returns',rows('returns')),series('Net AGI of movers','USD',rows('agiUsd'))],'sourceIds':['IRS_'+x['vintage'] for x in fresh['nyc'] if hist(x)],'status':'Reproduced from freshly retrieved official IRS files; archival chart stops at2022–2023'}
charts['c01_nyc_net_movers']['data']=c1
charts['c01_nyc_net_movers']['freshData']={**c1,'series':[series('Net domestic tax returns','returns',[{'period':x['period'],'value':x['net']['returns']} for x in fresh['nyc']]),series('Net AGI of movers','USD',[{'period':x['period'],'value':x['net']['agiUsd']} for x in fresh['nyc']])],'status':'Extended to official2023–2024 vintage','sourceIds':['IRS_'+x['vintage'] for x in fresh['nyc']]}
def partner(y):
 rr=sorted([x for x in fresh['statePartners'] if x['vintage']==y],key=lambda x:x['net']['agiUsd'])[:10]
 return {'geography':'New York State','geographicUnit':'state','period':rr[0]['period'],'measure':'Ten partner states with largest net AGI outflow','rows':[{'state':x['stateName'],'stateAbbreviation':x['stateAbbreviation'],'netReturns':x['net']['returns'],'netAgiUsd':x['net']['agiUsd'],'inflow':x['inflow'],'outflow':x['outflow']} for x in rr],'sourceIds':['IRS_'+y],'status':'Freshly retrieved official IRS data'}
charts['c02_nys_partner_states']['data']=partner('2223');charts['c02_nys_partner_states']['freshData']=partner('2324')
def partner_trend(new):
 return {'geography':'New York State','geographicUnit':'state','measure':'Net AGI of movers between NYS and selected partner states','series':[series(st,'USD',[{'period':x['period'],'value':x['net']['agiUsd']} for x in fresh['statePartners'] if x['stateAbbreviation']==st and (new or hist(x))]) for st in ['FL','NJ','CT','CA','TX','NC']],'sourceIds':['IRS_'+y for y in ['1819','1920','2021','2122','2223']+(['2324'] if new else [])],'status':'Official IRS data freshly retrieved'}
charts['c03_nys_destination_trends']['data']=partner_trend(False);charts['c03_nys_destination_trends']['freshData']=partner_trend(True)
def pairs(y):
 rr=sorted([x for x in fresh['nycCountyPairs'] if x['vintage']==y and x['publishedOutflow'] is not None],key=lambda x:-x['publishedOutflow']['returns'])[:14]
 return {'geography':'New York City to or from named counties','geographicUnit':'county-pair aggregation of NYC boroughs','period':rr[0]['period'],'measure':'14 largest destinations by published return outflow','rows':[{'county':x['countyName'],'state':x['stateAbbreviation'],'countyFips':x['countyFips'],'inReturns':x['publishedInflow']['returns'] if x['publishedInflow'] else None,'outReturns':x['publishedOutflow']['returns'],'netReturns':x['netPublished']['returns'] if x['netPublished'] else None} for x in rr],'sourceIds':['IRS_'+y],'status':'Published flows are lower bounds where smaller borough-pair flows are suppressed. Missing is not zero.'}
charts['c04_nyc_county_pairs']['data']=pairs('2223');charts['c04_nyc_county_pairs']['freshData']=pairs('2324')
charts['c05_components_nyc']['data']={'geography':'New York City, five boroughs combined','geographicUnit':'five-county aggregation','measure':'Components of population change','series':[series(label,'persons',[{'period':str(r['year']),'value':r[key],'estimateVintage':r['estimateVintage']} for r in fresh['nycPopulationComponents']]) for key,label in [('domesticMigration','Domestic migration'),('internationalMigration','International migration'),('naturalChange','Natural change')]],'sourceIds':['PEP_2019','PEP_2025'],'status':'Official PEP data freshly retrieved. Different vintages either side of2020; partial2020 omitted.'}
county_names=['New York','Kings','Queens','Bronx','Richmond','Nassau','Suffolk','Westchester','Rockland','Orange','Dutchess','Saratoga','Albany','Erie','Monroe','Onondaga','Tompkins']
charts['c06_county_domestic_heatmap']['data']={'geography':'17 selected New York counties','geographicUnit':'county','measure':'Net domestic migration per1,000 population','unit':'persons per1,000 population','years':list(range(2021,2026)),'rows':[{'countyName':r['countyName'],'countyFips':r['countyFips'],'values':[x['domesticMigrationRatePer1000'] for x in r['series']]} for n in county_names for r in fresh['countyPopulationChanges'] if r['countyName']==n+' County'],'sourceIds':['PEP_2025'],'status':'Freshly retrieved Census PEP Vintage2025'}
# Census-origin estimates delivered through the same public Census Reporter mirror used by the handoff.
acs_meta=json.loads((RAW/'acs_mirror_downloads.json').read_text());G=acs_meta['geographies']
mob=json.loads((RAW/'migration_acs_mobility.json').read_text());housing=json.loads((RAW/'migration_acs_housing_ancestry.json').read_text())
def val(data,g,t,c):return data['data'][G[g]][t]['estimate'][c]
def moe(data,g,t,c):return data['data'][G[g]][t]['error'][c]
def ratio(data,g,nt,nc,dt,dc):
 n=val(data,g,nt,nc);d=val(data,g,dt,dc);nm=moe(data,g,nt,nc);dm=moe(data,g,dt,dc)
 if n is None or d is None or not d:return {'percent':None,'moe90':None,'numerator':n,'denominator':d,'numeratorMoe90':nm,'denominatorMoe90':dm}
 v=n/d;var=nm*nm-v*v*dm*dm if nm is not None and dm is not None else None
 # ACS subset proportion approximation; fallback to ratio formula when the subtraction is negative.
 m=100*math.sqrt(var if var is not None and var>=0 else nm*nm+v*v*dm*dm)/d if var is not None else None
 return {'percent':round(v*100,3),'moe90':round(m,3) if m is not None else None,'numerator':n,'denominator':d,'numeratorMoe90':nm,'denominatorMoe90':dm}
mr=[]
for g in ['Manhattan','Brooklyn','Queens','Bronx','Staten Island','Nassau','Suffolk','Westchester']:
 for t,label in [('B07004H','White, not Hispanic'),('B07004B','Black'),('B07004D','Asian'),('B07004I','Hispanic, any race')]:
  for col,origin in [('005','Different US state'),('006','Abroad')]:mr.append({'place':g,'geoid':G[g],'group':label,'origin':origin,**ratio(mob,g,t,t+col,t,t+'001')})
charts['c07_acs_mobility_by_race']['data']={'geography':'Eight NY counties','geographicUnit':'county','measure':'Current residents who lived in another state or abroad one year ago, share of group','estimateVintage':'ACS2020–2024 five-year','rows':mr,'sourceIds':['ACS_MIGRATION_2024'],'status':'Freshly retrieved Census-origin estimates with90% MOEs. Arrivals only, not net flows; race and ethnicity are aggregate statistics.'}
ancestry_groups=[('Italian',[51]),('Irish',[49]),('German',[42]),('English, Scottish and Scotch-Irish',[36,67,66]),('Russian, Polish and Ukrainian',[64,61,92])]
ar=[]
for g in ['Manhattan','Brooklyn','Queens','Nassau','Suffolk','Westchester','Bergen NJ','Palm Beach FL','Broward FL','Miami-Dade FL','East Hampton town','Southampton town']:
 for label,codes in ancestry_groups:
  values=[val(housing,g,'B04006','B04006'+str(c).zfill(3)) for c in codes];count=sum(values);den=val(housing,g,'B01003','B01003001')
  ar.append({'place':g,'geoid':G[g],'ancestry':label,'reportedAncestries':count,'population':den,'reportsPer100Residents':round(count/den*100,3),'cells':['B04006'+str(c).zfill(3) for c in codes]})
charts['c08_ancestry_proxy']['data']={'geography':'Selected counties and East End towns','geographicUnit':'county or county subdivision','measure':'Ancestry reports per100 residents','estimateVintage':'ACS2020–2024 five-year','rows':ar,'sourceIds':['ACS_HOUSING_ANCESTRY_2024'],'status':'These are ancestry reports, not religious identity. People may report multiple ancestries. The PDF’s religious proxy labels should not be reused as religious population estimates.'}
charts['c08_ancestry_proxy']['interpretationWarning']='The original archival image contains religious proxy labels. ACS ancestry does not measure religion; the normalized data uses ancestry labels only.'
charts['c11_manhattan_rent_vacancy']['data']['comparison']={'period':'Oct2026','publisher':'Corcoran','medianMonthlyRentUsd':5279,'listingVacancyPercent':1.31,'sourceIds':['M12'],'status':'Separate broker method; partly verified in supplied handoff; do not splice into Elliman trend'}
season=[]
for g in ['East Hampton town','Shelter Island town','Southampton town','Southold town','Riverhead town','Suffolk','Westchester','Manhattan','New York State']:
 season.append({'place':g,'geoid':G[g],'geographicUnit':'state' if g=='New York State' else 'county subdivision' if g.endswith('town') else 'county',**ratio(housing,g,'B25004','B25004006','B25002','B25002001')})
charts['c15_seasonal_housing_share']['data']={'geography':'East End towns, comparison counties, New York State','measure':'Seasonal, recreational or occasional-use units as share of all housing units','estimateVintage':'ACS2020–2024 five-year','rows':season,'sourceIds':['ACS_HOUSING_ANCESTRY_2024'],'status':'Freshly retrieved Census-origin estimates with90% MOEs. Vacant seasonal units are not necessarily second homes owned by out-of-state voters.'}
def sf(new):
 return {'geography':'Whole Suffolk County and NYC','geographicUnit':'county-pair aggregation','measure':'Two-way tax-return migration; Suffolk is not synonymous with SD1 or the East End','series':[series(label,unit,[{'period':r['period'],'value':r[k][measure]} for r in fresh['suffolkNyc'] if new or hist(r)]) for k,label,measure,unit in [('fromNyc','NYC to Suffolk, returns','returns','returns'),('toNyc','Suffolk to NYC, returns','returns','returns'),('fromNyc','NYC to Suffolk, AGI','agiUsd','USD'),('toNyc','Suffolk to NYC, AGI','agiUsd','USD')]],'sourceIds':['IRS_'+r['vintage'] for r in fresh['suffolkNyc'] if new or hist(r)],'status':'Freshly retrieved official IRS county-pair data'}
charts['c16_nyc_suffolk_flows']['data']=sf(False);charts['c16_nyc_suffolk_flows']['freshData']=sf(True)
charts['c17_senate_link_scatter']['data']={'type':'historicalExploratoryTable','geographicUnit':'Senate district','sampleSizeInOriginalModel':23,'availableDistrictRows':tables[9]['rows'],'districtColumns':tables[9]['headers'],'correlations':{'columns':tables[10]['headers'],'rows':tables[10]['rows']},'sourceIds':['M6','M23'],'status':'Historical model from supplied handoff, using unofficial2026 snapshot and secondary2022 election returns. Full23-row underlying scatter data absent from handoff; the11 printed district rows and six correlations are preserved. Not refreshed or treated as causal.'}
charts['c17_senate_link_scatter']['interpretationWarning']='Historical exploratory analysis only. Do not present these correlations or original unofficial outcomes as fresh verified election evidence.'
for c in p['migration']['charts']:
 c['dataAvailable']=c['data'] is not None
 c['archiveImageAsOf']='2026-11-20'
 c['numericDataRetrievedAt']='2026-11-23' if c['id'] in ['c01_nyc_net_movers','c02_nys_partner_states','c03_nys_destination_trends','c04_nyc_county_pairs','c05_components_nyc','c06_county_domestic_heatmap','c07_acs_mobility_by_race','c08_ancestry_proxy','c15_seasonal_housing_share','c16_nyc_suffolk_flows'] else None
p['migration']['freshDataFile']='fresh_migration.json';p['migration']['latestIrsVintage']='2023–2024'
p['migration']['dataCoverage']={'chartsWithStructuredData':17,'chartsWithFreshPrimaryOrCensusOriginData':10,'archivalRealEstateAndComptrollerSeries':6,'archivalExploratoryModelWithIncompleteRawScatter':1}
sources=fresh['sources'][:]
for name,id,title in [('migration_acs_mobility.json','ACS_MIGRATION_2024','ACS2020–2024 geographical mobility by race and Hispanic origin'),('migration_acs_housing_ancestry.json','ACS_HOUSING_ANCESTRY_2024','ACS2020–2024 housing and ancestry')]:
 d=next(x for x in acs_meta['downloads'] if x['file']==name)
 sources.append({'id':id,'title':title,'publisher':'U.S. Census Bureau; delivered by Census Reporter API mirror','sourceUrl':d['url'],'publishedAt':'ACS2020–2024 five-year release','retrievedAt':'2026-11-23','verificationStatus':'Census-origin estimates freshly retrieved; raw estimates and90% margins of error retained','officialTableUrl':'https://data.census.gov/table/ACSDT5Y2024.'+('B07004H' if 'MIGRATION' in id else 'B25004')})
for s in sources:
 if 'url' in s:s['sourceUrl']=s['url']
p['sources'].extend(sources)
p['meta']['freshDataNote']='This import now includes newly retrieved IRS migration through2023–2024, Census PEP2019/2025 and ACS2020–2024 county/town estimates. Original PDF pages and images remain archival and dated.'
(OUT/'normalized.json').write_text(json.dumps(p,separators=(',',':'),ensure_ascii=False))
(OUT/'migration_charts_data.json').write_text(json.dumps({'charts':p['migration']['charts'],'sources':sources,'coverage':p['migration']['dataCoverage']},separators=(',',':'),ensure_ascii=False))
# Minimal proof against the archival PDF: all five old IRS net return totals reproduced exactly.
expected=[-47831,-114282,-125118,-73677,-41684]
assert [r['net']['returns'] for r in fresh['nyc'][:5]]==expected
assert len(p['pages'])==98 and len(p['layers'])==24 and len(p['issueCatalog'])==20
assert len(p['migration']['charts'])==17 and all(x['dataAvailable'] for x in p['migration']['charts'])
assert len(fresh['districtCountyContext'])==63 and len(fresh['countyPopulationChanges'])==62
report={'pdfPages':98,'layers':24,'issues':20,'tables':72,'media':len(p['media']),'sources':len(p['sources']),'chartCoverage':p['migration']['dataCoverage'],'oldIrsNetReturnsReproducedExactly':True,'freshLatestIrsVintage':'2023–2024','counties':62,'countyMigrationRows':372,'districtCountyContext':63,'normalizedBytes':(OUT/'normalized.json').stat().st_size,'chartDataBytes':(OUT/'migration_charts_data.json').stat().st_size,'limitations':['Six real estate/Comptroller series retain archival verification status; they were imported, not newly validated with broker reports.','The historical Senate correlation chart lacks its complete23-row raw scatter dataset;11 printed rows and six correlations were preserved.','Ancestry data does not measure religion.','County migration is not district migration.']}
(OUT/'import_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
