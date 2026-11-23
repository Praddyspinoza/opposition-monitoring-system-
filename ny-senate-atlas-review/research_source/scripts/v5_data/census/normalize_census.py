#!/usr/bin/env python3
"""Normalize freshly fetched ACS 2024 five-year NY Senate estimates.

No values from the handoff or prior terminal are used. Preserve source cells,
universes, and 90% MOEs, including for derived percentages.
"""
from __future__ import annotations

# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = (RESEARCH_ROOT / 'v5_data/census')
REPORT = json.loads((ROOT / 'fetch_report.json').read_text())
FETCH = {r['table']: r for r in REPORT if r['status'] == 'downloaded'}
RAW = {t: json.loads((ROOT / 'raw' / f'{t}.json').read_text()) for t in FETCH}
PERIOD = '2020–2024'
EVIDENCE = 'ACS survey estimate'
METHOD_URL = 'https://www.census.gov/content/dam/Census/library/publications/2018/acs/acs_general_handbook_2018_ch08.pdf'

def clean(v):
    # Census negative codes are special/suppressed values, not measurements.
    if v is None or isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
        return None
    return int(v) if v == int(v) else v

def rnd(v, digits=2):
    return None if v is None else round(v, digits)

def cell(t, n):
    return f'{t}{n:03d}'

def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')

def col(t, n):
    return RAW[t]['tables'][t]['columns'][cell(t, n)]['name'].rstrip(':')

def specs(cells):
    if isinstance(cells, int):
        return [(cells, 1)]
    return [(c, 1) if isinstance(c, int) else c for c in cells]

def calculate(geo, t, cells):
    d = RAW[t]['data'][geo][t]
    terms = specs(cells)
    vv = [clean(d['estimate'].get(cell(t, n))) for n, sign in terms]
    mm = [clean(d['error'].get(cell(t, n))) for n, sign in terms]
    value = None if any(v is None for v in vv) else sum(v * sign for v, (_, sign) in zip(vv, terms))
    if value is not None and value < 0:
        value = None
    moe = None if any(m is None for m in mm) else math.sqrt(sum((m * sign) ** 2 for m, (_, sign) in zip(mm, terms)))
    return value, moe

def refs(t, cells):
    return [{'cell': cell(t, n), 'coefficient': sign} for n, sign in specs(cells)]

def quality(v, m):
    if v is None:
        return 'unavailable'
    if m is None:
        return 'margin_of_error_unavailable'
    if v == 0:
        return 'zero_estimate_with_sampling_uncertainty'
    return 'high_sampling_uncertainty' if (m / 1.645 / v) > .30 else 'estimate_with_margin_of_error'

def pct(num, den, nm, dm, subset=True):
    if num is None or den is None or den <= 0:
        return None, None, None
    p = num / den
    if nm is None or dm is None:
        return 100 * p, None, None
    term = nm * nm - p * p * dm * dm if subset else nm * nm + p * p * dm * dm
    method = 'subset proportion approximation' if subset and term >= 0 else 'ratio approximation'
    if term < 0:
        term = nm * nm + p * p * dm * dm
    return 100 * p, 100 * math.sqrt(term) / den, method

def shared(t):
    return {
        'table': t, 'universe': RAW[t]['tables'][t]['universe'],
        'period': PERIOD, 'sourceUrl': FETCH[t]['sourceUrl'],
        'officialSourceUrl': f'https://data.census.gov/table/ACSDT5Y2024.{t}?g=040XX00US36$6100000',
        'retrievedAt': FETCH[t]['retrievedAt'], 'evidenceType': EVIDENCE,
    }

def metric(geo, key, label, t, cells, unit='people', denominator=None, denominator_table=None, universe=None, note=None):
    value, moe = calculate(geo, t, cells)
    out = {'key': key, 'label': label, 'value': rnd(value), 'unit': unit,
           'moe': rnd(moe), 'moeConfidence': 90, 'cells': refs(t, cells),
           'quality': quality(value, moe), **shared(t)}
    if universe:
        out['universe'] = universe
    if denominator is not None:
        dt = denominator_table or t
        den, dm = calculate(geo, dt, denominator)
        rate, rm, method = pct(value, den, moe, dm)
        out.update(value=rnd(rate), unit='percent', moe=rnd(rm), count=value, countMoe90=rnd(moe),
                   denominator=den, denominatorMoe90=rnd(dm), denominatorCells=refs(dt, denominator),
                   moeMethod=method)
        if dt != t:
            out['denominatorSourceUrl'] = FETCH[dt]['sourceUrl']
    if len(specs(cells)) > 1:
        out['countMoeMethod'] = 'root sum of squared component margins of error (approximate)'
    if note:
        out['note'] = note
    return out

def group(geo, title, t, categories, denominator=1, denominator_table=None, note=None, partition=True):
    dt = denominator_table or t
    den, dm = calculate(geo, dt, denominator)
    out = {'title': title, **shared(t), 'denominator': den, 'denominatorMoe90': rnd(dm),
           'denominatorCells': refs(dt, denominator), 'partition': partition, 'items': []}
    if dt != t:
        out['denominatorUniverse'] = RAW[dt]['tables'][dt]['universe']
        out['denominatorSourceUrl'] = FETCH[dt]['sourceUrl']
    if note:
        out['note'] = note
    for key, label, cells in categories:
        value, moe = calculate(geo, t, cells)
        rate, rm, method = pct(value, den, moe, dm)
        out['items'].append({'key': key, 'label': label, 'count': value, 'countMoe90': rnd(moe),
                             'share': rnd(rate), 'shareMoe90': rnd(rm), 'moeMethod': method,
                             'cells': refs(t, cells), 'quality': quality(value, moe)})
    return out

def leaves(t, minimum=2):
    columns = list(RAW[t]['tables'][t]['columns'].items())
    result=[]
    for i, (code, info) in enumerate(columns):
        if not re.fullmatch(re.escape(t) + r'\d{3}', code):
            continue  # Some distributor metadata contains non-data section headers.
        n=int(code[-3:])
        if n < minimum:
            continue
        if i == len(columns)-1 or columns[i+1][1]['indent'] <= info['indent']:
            label=info['name'].rstrip(':')
            result.append((slug(label),label,n))
    return result

AGE = [
    ('under_18','Under 18',list(range(3,7))+list(range(27,31))),
    ('age_18_34','18–34',list(range(7,13))+list(range(31,37))),
    ('age_35_49','35–49',list(range(13,16))+list(range(37,40))),
    ('age_50_64','50–64',list(range(16,20))+list(range(40,44))),
    ('age_65_plus','65 and over',list(range(20,26))+list(range(44,50))),
]
OCC = [5,6,8,9,10,12,13,14,15,17,18,20,22,23,24,25,26,28,29,31,32,33,35,36,37]
IND = [4,5,6,7,8,9,11,12,13,15,16,18,19,20,22,23,25,26,27,28]
RACE = [('white_non_hispanic','White, non-Hispanic',3),('black_non_hispanic','Black, non-Hispanic',4),
        ('aian_non_hispanic','American Indian / Alaska Native, non-Hispanic',5),
        ('asian_non_hispanic','Asian, non-Hispanic',6),('pacific_islander_non_hispanic','Pacific Islander, non-Hispanic',7),
        ('other_race_non_hispanic','Other race, non-Hispanic',8),('multiracial_non_hispanic','Two or more races, non-Hispanic',9),
        ('hispanic','Hispanic / Latino, any race',12)]
LANG = [(slug(v['name']),v['name'].rstrip(':'),int(k[-3:])) for k,v in RAW['C16001']['tables']['C16001']['columns'].items() if v['indent']==1]
BIRTH_IDS = [8,42,44,50,52,54,58,60,64,74,92,112,121,124,145,147,148,157,160,169,170,171,177]
HOUSEHOLDS=[('married_couple','Married-couple family',3),('male_householder_other_family','Male householder, no spouse present',5),
            ('female_householder_other_family','Female householder, no spouse present',6),('living_alone','Householder living alone',8),
            ('nonfamily_shared','Nonfamily, not living alone',9)]
FAMILY_CHILDREN=[('married_with_children','Married-couple family with own children under 18',3),
                 ('married_without_children','Married-couple family without own children under 18',7),
                 ('male_with_children','Male householder, no spouse, with own children under 18',10),
                 ('male_without_children','Male householder, no spouse, without own children under 18',14),
                 ('female_with_children','Female householder, no spouse, with own children under 18',16),
                 ('female_without_children','Female householder, no spouse, without own children under 18',20)]
WORKERS=[('no_workers','No workers',2),('one_worker','One worker',3),('two_workers','Two workers',4),('three_plus_workers','Three or more workers',5)]
FAMILY_WORKERS=[('no_workers','No workers',[4,14,19,25,35,40]),('one_worker','One worker',[5,15,20,26,36,41]),
                ('two_workers','Two workers',[6,16,21,27,37,42]),('three_plus_workers','Three or more workers',[9,17,22,30,38,43])]
EDUCATION=[('below_high_school','Less than high school',list(range(2,17))),('high_school','High school / GED',[17,18]),
           ('some_college','Some college, no degree',[19,20]),('associate','Associate degree',21),('bachelors','Bachelor’s degree',22),
           ('graduate','Graduate / professional degree',[23,24,25])]
RENT_BURDEN=[('below_20','Below 20%',[2,3,4]),('20_to_29_9','20–29.9%',[5,6]),('30_to_49_9','30–49.9%',[7,8,9]),('50_plus','50% or more',10)]
COMMUTE=[('drive_alone','Drive alone',3),('carpool','Carpool',4),('public_transit','Public transportation',10),
         ('taxi','Taxi / ride-hailing',16),('motorcycle','Motorcycle',17),('bicycle','Bicycle',18),('walk','Walk',19),
         ('other','Other means',20),('work_from_home','Work from home',21)]
MOBILITY=[('same_home','Same home one year earlier',4),('within_county','Moved within county',7),
          ('other_county_in_state','Moved from another New York county',10),('other_state','Moved from another state',13),
          ('abroad','Moved from abroad',16)]
INCOME=[(f'bracket_{n-1}',col('B19001',n),n) for n in range(2,18)]

def build_district(n):
    geo=f'61000US36{n:03d}'
    ms=[]
    def m(*args,**kwargs):
        ms.append(metric(geo,*args,**kwargs))
    m('population','Population','B01003',1)
    m('median_age','Median age','B01002',1,'years')
    m('median_household_income','Median household income','B19013',1,'USD',note='2024 inflation-adjusted dollars.')
    m('per_capita_income','Per-capita income','B19301',1,'USD',note='2024 inflation-adjusted dollars.')
    m('households','Households','B11001',1,'households')
    m('families','Families','B11003',1,'families')
    m('housing_units','Housing units','B25002',1,'housing units')
    m('median_gross_rent','Median gross rent','B25064',1,'USD per month')
    m('median_owner_home_value','Median owner-occupied home value','B25077',1,'USD')
    m('bachelors_or_higher_pct','Bachelor’s degree or higher','B15003',[22,23,24,25],denominator=1)
    m('foreign_born_pct','Foreign-born residents','B05002',13,denominator=1)
    m('naturalized_foreign_born_pct','Naturalized among foreign-born residents','B05002',14,denominator=13,
      universe='Foreign-born population')
    m('poverty_rate_pct','Below poverty threshold','B17001',2,denominator=1)
    for k,label,c in RACE:
        m(k+'_pct',label,'B03002',c,denominator=1)
    for k,label,c in AGE:
        m(('age_'+k if k=='under_18' else k)+'_pct',label,'B01001',c,denominator=1)
    m('owner_share_pct','Owner-occupied households','B25003',2,denominator=1)
    m('renter_share_pct','Renter-occupied households','B25003',3,denominator=1)
    m('severe_rent_burden_pct','Rent is 50% or more of household income','B25070',10,denominator=[(1,1),(11,-1)],
      universe='Renter-occupied housing units for which gross rent as a percentage of household income is computed',
      note='Excludes not-computed rent-to-income cases. Denominator MOE is an approximate root-sum-square difference MOE.')
    m('rent_burden_30_plus_pct','Rent is 30% or more of household income','B25070',[7,8,9,10],denominator=[(1,1),(11,-1)],
      universe='Renter-occupied housing units for which gross rent as a percentage of household income is computed',
      note='Excludes not-computed rent-to-income cases.')
    m('rent_burden_not_computed','Rent-to-income not computed','B25070',11,'housing units')
    m('household_living_alone_pct','Households living alone','B11001',8,denominator=1)
    m('married_couple_households_pct','Married-couple family households','B11001',3,denominator=1)
    m('families_with_children_pct','Families with own children under 18','B11003',[3,10,16],denominator=1)
    m('single_parent_among_families_with_children_pct','Single-parent families among families with own children under 18','B11003',[10,16],denominator=[3,10,16],
      universe='Families with own children under 18',note='Male or female householder with no spouse present. This does not count every child or caregiver arrangement.')
    for k,label,c in WORKERS:
        m('households_'+k+'_pct',label+' in household','B08202',c,denominator=1,note='Workers are not the same as all income earners.')
    m('both_spouses_worked_pct','Both spouses worked among married-couple families','B23009',[7,10,28,31],denominator=[3,24],
      universe='Married-couple families',note='Both spouses worked in past 12 months; additional workers may be present.')
    m('households_retirement_income_pct','Households receiving retirement income','B19059',2,denominator=1,
      note='Retirement income receipt does not identify all retired persons.')
    m('veteran_pct','Veterans among civilian adults','B21001',2,denominator=1)
    m('vacancy_rate_pct','Vacant housing units','B25002',3,denominator=1)
    m('seasonal_housing_share_pct','Seasonal / recreational / occasional-use units','B25004',6,denominator=1,denominator_table='B25002',
      universe='All housing units',note='ACS vacancy category; not a count of second-home voters.')
    m('work_from_home_pct','Workers working from home','B08301',21,denominator=1)
    m('public_transit_commute_pct','Workers using public transportation','B08301',10,denominator=1)
    m('non_english_home_language_pct','Language other than English at home','C16001',[(1,1),(2,-1)],denominator=1)
    m('limited_english_pct','Speak English less than very well','C16001',list(range(5,39,3)),denominator=1,
      note='Includes residents who speak another language at home and report speaking English less than very well.')
    m('same_home_one_year_pct','Same home one year earlier','B07003',4,denominator=1,
      note='Current residents age 1+; not net migration or a measure of 2026 moves.')
    groups={
        'race':group(geo,'Race and Hispanic origin','B03002',RACE),
        'hispanic_origins':group(geo,'Hispanic / Latino specific origins','B03001',leaves('B03001',4),denominator=3,
            note='Shares of Hispanic / Latino residents. Labels preserve the Census table categories.'),
        'asian_groups':group(geo,'Asian-alone groups','B02015',leaves('B02015'),
            note='Shares of Asian-alone residents. Self-reported Census categories are not religious affiliation.'),
        'ancestry':group(geo,'Reported ancestry','B04006',leaves('B04006'),partition=False,
            note='Ancestry responses may overlap. People can report more than one ancestry; do not sum these categories to estimate a population. Ancestry does not establish religion or political views.'),
        'birthplace':group(geo,'Selected foreign-born places of birth','B05006',[(slug(col('B05006',c)),col('B05006',c),c) for c in BIRTH_IDS],
            partition=False,note='Selected places; shares of foreign-born residents excluding those born at sea. Country of birth is not religion, ethnicity, citizenship, or political preference.'),
        'language':group(geo,'Language spoken at home','C16001',LANG,
            note='Population age 5+. Several published categories combine languages; no unreported language breakdown is inferred.'),
        'occupation':group(geo,'Resident occupations','C24010',[(slug(col('C24010',c)),col('C24010',c),[c,c+36]) for c in OCC],
            note='Civilian employed residents age 16+; male and female table cells combined. Not workplaces, campaign donors, or voting blocs.'),
        'industry':group(geo,'Resident employment industries','C24030',[(slug(col('C24030',c)),col('C24030',c),[c,c+27]) for c in IND],
            note='Industry of civilian employed residents age 16+; male and female table cells combined. Not donor industries.'),
        'age':group(geo,'Resident age','B01001',AGE),
        'education':group(geo,'Educational attainment','B15003',EDUCATION),
        'nativity':group(geo,'Nativity and citizenship','B05002',[('native','Native-born',2),('naturalized','Foreign-born, naturalized citizen',14),('noncitizen','Foreign-born, not a citizen',21)]),
        'households':group(geo,'Household composition','B11001',HOUSEHOLDS),
        'family_children':group(geo,'Families and own children','B11003',FAMILY_CHILDREN,
            note='Own children under age 18. Universe is families, not all households.'),
        'household_workers':group(geo,'Workers in household','B08202',WORKERS,
            note='Worker counts are not a count of all income recipients; retirement or other income may exist in a zero-worker household.'),
        'family_workers':group(geo,'Workers in family','B23009',FAMILY_WORKERS,
            note='Workers in past 12 months. Universe is families, not all households.'),
        'marital':group(geo,'Marital status','B12001',[('never_married','Never married',[3,12]),('now_married','Now married, including separated',[4,13]),
            ('widowed','Widowed',[9,18]),('divorced','Divorced',[10,19])],note='Population age 15+. Current marriage includes separated residents.'),
        'householder_age':group(geo,'Age of householder','B25007',[(slug(col('B25007',c)),col('B25007',c),[c,c+10]) for c in range(3,12)]),
        'housing_structure':group(geo,'Housing units by structure','B25024',[(slug(col('B25024',c)),col('B25024',c),c) for c in range(2,12)],
            note='Building structure does not identify cooperative ownership or condo status.'),
        'housing_tenure':group(geo,'Occupied housing tenure','B25003',[('owner','Owner occupied',2),('renter','Renter occupied',3)]),
        'rent_burden':group(geo,'Gross rent as share of income','B25070',RENT_BURDEN,denominator=[(1,1),(11,-1)],
            note='Shares exclude cases where rent-to-income was not computed.'),
        'household_income':group(geo,'Household income distribution','B19001',INCOME,note='2024 inflation-adjusted dollars.'),
        'mobility':group(geo,'Residence one year earlier','B07003',MOBILITY,
            note='Current population age 1+. This is residential mobility, not net migration; it omits those who moved out of the district.'),
        'commute':group(geo,'Travel to work','B08301',COMMUTE),
        'vacancy':group(geo,'Vacant housing categories','B25004',[(slug(col('B25004',c)),col('B25004',c),c) for c in range(2,9)]),
        'retirement_income':group(geo,'Household retirement income','B19059',[('with_retirement_income','With retirement income',2),('no_retirement_income','No retirement income',3)]),
        'veterans':group(geo,'Veteran status','B21001',[('veteran','Veteran',2),('nonveteran','Nonveteran',3)]),
    }
    return {'district':n,'geoId':geo,'name':f'New York Senate District {n}',
            'status':'freshly_retrieved','metrics':ms,'groups':groups}

def detailed_cross_tabs(n):
    geo=f'61000US36{n:03d}'
    age=[]
    for label,total,start in [('Under 25',2,3),('25–44',19,20),('45–64',36,37),('65 and over',53,54)]:
        age.append(group(geo,label,'B19037',[(f'bracket_{i+1}',col('B19037',c),c) for i,c in enumerate(range(start,start+16))],denominator=total,
            note='Householder age. 2024 inflation-adjusted household income.'))
    family=[]
    for label,total,start in [('Married couple, own children under 18',3,4),('Married couple, no own children under 18',20,21),
                              ('Male householder, no spouse, own children under 18',39,40),('Male householder, no spouse, no own children under 18',56,57),
                              ('Female householder, no spouse, own children under 18',74,75),('Female householder, no spouse, no own children under 18',91,92)]:
        family.append(group(geo,label,'B19131',[(f'bracket_{i+1}',col('B19131',c),c) for i,c in enumerate(range(start,start+16))],denominator=total,
            note='2024 inflation-adjusted family income.'))
    structure=[]
    for label,total,start in [('Owner occupied',2,3),('Renter occupied',13,14)]:
        structure.append(group(geo,label,'B25032',[(slug(col('B25032',c)),col('B25032',c),c) for c in range(start,start+10)],denominator=total))
    mobility=[]
    for label,total,offset in [('Owner-occupied household residents',2,1),('Renter-occupied household residents',3,2)]:
        mobility.append(group(geo,label,'B07013',[(key,title,c+offset) for key,title,c in MOBILITY],denominator=total,
            note='Population age 1+ in households. Mobility among current residents, not net migration.'))
    return {'district':n,'householder_age_by_income':age,'family_type_children_by_income':family,
            'tenure_by_structure':structure,'tenure_by_mobility':mobility}

def main():
    ds=[build_district(n) for n in range(1,64)]
    tables={t:{**shared(t),'title':RAW[t]['tables'][t]['title'],'columns':RAW[t]['tables'][t]['columns'],
               'rawFile':f'raw/{t}.json','sha256':FETCH[t]['sha256'],
               'officialSummaryFileUrl':f'https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-{t.lower()}.dat'} for t in sorted(RAW)}
    meta={'schemaVersion':'1.0','publisher':'United States Census Bureau','distributor':'Census Reporter',
          'release':'acs2024_5yr','period':PERIOD,'retrievedAt':max(r['retrievedAt'] for r in FETCH.values()),
          'generatedAt':datetime.now(timezone.utc).isoformat(),'districtCount':63,'tableCount':len(RAW),
          'evidenceType':EVIDENCE,'moeConfidence':90,'handoffValuesImported':0,
          'geography':'New York state legislative districts, upper chamber, in ACS 2024 geography',
          'sourceUrl':'https://www.census.gov/programs-surveys/acs/data/summary-file.2024.html',
          'methodologyUrl':METHOD_URL,
          'notes':[
             'Freshly retrieved Census-origin estimates, not values copied from the project handoff.',
             'The five-year survey period is 2020–2024. These are not a live 2026 population count.',
             'The official API requires a key; the documented Census Reporter API supplied the Census-origin tables and their original margins of error.',
             'Single-cell estimates and margins of error are published values. Summed/differenced counts use approximate root-sum-square margins of error.',
             'Derived percentages use the Census subset-proportion MOE approximation; a negative variance term falls back to the ratio formula. Derived MOEs are approximate and do not include full covariance.',
             'High sampling uncertainty means a coefficient of variation greater than 30% using SE = MOE / 1.645. This is a presentation flag, not a Census suppression rule.',
             'Null is missing/suppressed; an estimated zero is retained with its margin of error. No missing value is filled with zero.',
             'No demographic table establishes religious affiliation, political preferences, individual eligibility to vote, or donor identity.',
          ]}
    normalized={'meta':meta,'tables':tables,'districts':ds}
    (ROOT/'normalized.json').write_text(json.dumps(normalized,ensure_ascii=False,separators=(',',':')))
    (ROOT/'household_cross_tabs.json').write_text(json.dumps({'meta':meta,'districts':[detailed_cross_tabs(n) for n in range(1,64)]},ensure_ascii=False,separators=(',',':')))
    slim=[]
    for d in ds:
        metrics={m['key']:m['value'] for m in d['metrics']}
        moes={m['key']:m['moe'] for m in d['metrics']}
        groups={k:{'title':g['title'],'table':g['table'],'universe':g['universe'],'denominator':g['denominator'],
                   'items':[{key:i[key] for key in ['key','label','count','countMoe90','share','shareMoe90','quality']} for i in g['items']]}
                for k,g in d['groups'].items()}
        slim.append({'district':d['district'],'geoId':d['geoId'],'metrics':metrics,'moes':moes,'groups':groups})
    (ROOT/'terminal_summary.json').write_text(json.dumps({'meta':meta,'districts':slim},ensure_ascii=False,separators=(',',':')))
    checks=[]
    for d in ds:
        assert len(d['metrics'])==len({m['key'] for m in d['metrics']})
        for key,g in d['groups'].items():
            if g['partition'] and g['denominator'] is not None and all(i['count'] is not None for i in g['items']):
                total=sum(i['count'] for i in g['items'])
                if abs(total-g['denominator'])>1:
                    checks.append({'district':d['district'],'group':key,'sum':total,'denominator':g['denominator']})
        for m in d['metrics']:
            if m['unit']=='percent' and m['value'] is not None and not 0<=m['value']<=100:
                checks.append({'district':d['district'],'metric':m['key'],'outOfRange':m['value']})
    metric_coverage={m['key']:sum(any(x['key']==m['key'] and x['value'] is not None for x in d['metrics']) for d in ds) for m in ds[0]['metrics']}
    coverage={'period':PERIOD,'districts':63,'tables':len(RAW),'metricsPerDistrict':len(ds[0]['metrics']),
              'groupsPerDistrict':len(ds[0]['groups']),'metricCoverageDistrictCount':metric_coverage,
              'all63PresentInEveryTable':all(len([g for g in r['data'] if g.startswith('61000US36')])==63 for r in RAW.values()),
              'partitionAndRangeFailures':checks,'retrievalFailures':[r for r in REPORT if r['status']!='downloaded'],
              'handoffValuesImported':0,'crossTabs':['B19037 householder age by income','B19131 family type and own children by income',
                                                   'B25032 tenure by structure','B07013 tenure by mobility'],
              'unavailableOrNotInTheseTables':['Religious affiliation','Individual voting behavior or campaign support','Cooperative ownership counts',
                                              'Net district migration outflow','Exact current 2026 population','Donor identities']}
    (ROOT/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))
    assert not checks, json.dumps(checks[:5])
    print(json.dumps({k:coverage[k] for k in ['districts','tables','metricsPerDistrict','groupsPerDistrict','all63PresentInEveryTable','partitionAndRangeFailures']},indent=2))
    for n in [1,11,16,17,59,63]:
        d=slim[n-1]
        print('SD',n,{k:d['metrics'][k] for k in ['population','median_household_income','households','renter_share_pct','bachelors_or_higher_pct']})

if __name__=='__main__':
    main()
