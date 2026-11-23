# Fresh ACS data for all 63 New York Senate districts

The collection contains **38 ACS 2024 five-year detailed tables**, covering the
**2020–2024 survey period**, freshly retrieved for all 63 New York State Senate
districts. No demographic values from the supplied project handoff were imported.

## Application files

- `normalized.json`: 63 district records, each with 49 headline metrics and 26
  detailed groups. Every metric includes its table, cell derivation, universe,
  estimate, unit, 90% margin of error, source URL, retrieval time, and evidence type.
- `terminal_summary.json`: the same headline metrics as a key/value object plus
  a parallel `moes` object and compact detailed groups. Intended for the front end.
- `household_cross_tabs.json`: householder age by income, family type and own
  children by income, tenure by housing structure, and tenure by residential mobility.
- `coverage.json`: coverage, validation results, and dimensions that these tables
  cannot establish.
- `fetch_report.json`: source URL, release, retrieval time, size and SHA-256 for
  each downloaded table.
- `raw/`: the original 38 table responses, including all published cells and MOEs.

```js
const district = data.districts.find(d => d.district === 17);
const population = district.metrics.find(m => m.key === 'population');
const occupations = district.groups.occupation.items;
// Occupation item: {key, label, count, countMoe90, share, shareMoe90, cells, quality}
```

The compact file instead uses `district.metrics.population` and
`district.moes.population`. Share values are percentages (e.g. 34.06 means
34.06%, not 0.3406). Percentage MOEs are percentage points.

## Source and reproducibility

The underlying publisher is the **United States Census Bureau**. The current
public Census API requires a key; none was configured in this environment. The
documented Census Reporter API republished the Census-origin ACS estimates and
their margins of error, and supplied these table responses:

`https://api.censusreporter.org/1.0/data/show/acs2024_5yr?table_ids=B01003&geo_ids=610%7C04000US36`

To reproduce:

```sh
python v5_data/census/pull_census.py
python v5_data/census/normalize_census.py
python v5_data/census/check_official_summary.py
```

The optional primary-source check uses ordinary HTTP byte ranges on the Census
Bureau's public table-based summary files. It extracts all 63 New York Senate
rows for population (B01003), median household income (B19013), and household
composition (B11001), then compares every estimate and margin-of-error cell
against the Census Reporter copy. Its result is `official_crosscheck.json`.
The extracted official rows are retained as `raw/official_summary_extract_*.psv`.

**Completed result:** all 63 districts matched in all three checked tables.
The 1,386 estimate/MOE field comparisons had **zero mismatches** against the
official Census files.

Primary documentation:

- [ACS 2024 summary files](https://www.census.gov/programs-surveys/acs/data/summary-file.2024.html)
- [Census 2024 five-year developer guidance](https://www.census.gov/data/developers/data-sets/acs-5year.2024.html)
- [Census Reporter API documentation](https://github.com/censusreporter/census-api/blob/master/API.md)
- [Census guidance for derived margins of error](https://www.census.gov/content/dam/Census/library/publications/2018/acs/acs_general_handbook_2018_ch08.pdf)

## What was validated

Every downloaded table has all 63 district identifiers. All 49 headline metrics
are available for every district. Each of the 26 groups designated as a complete
partition sums to its stated denominator, and all derived percentages are within
0–100. The four detailed cross-tab families also sum to their own denominators.

Direct single-cell MOEs are retained. For a sum or difference, the script uses
the square root of the sum of squared component MOEs. For a percentage with a
subset numerator, it uses the Census proportion approximation; when the term
inside the square root is negative, it uses the ratio approximation. These
derived MOEs are approximate because the full covariance is unavailable.

The high-uncertainty display flag is assigned when the coefficient of variation
exceeds 30%, using standard error = MOE / 1.645. This is a project display rule,
not a Census suppression threshold. Estimated zeros remain zeros with their
uncertainty; missing or suppressed observations remain null.

## Interpretation required in the terminal

These are five-year survey estimates, not live 2026 population measurements.
District geography is the upper-chamber geography represented in ACS 2024.
Dollar figures are in 2024 inflation-adjusted dollars where stated in the table.

- Renter burden uses only units for which rent-to-income was computed. The
  not-computed count is exposed separately.
- Occupation and industry describe employed residents age 16 and over. They do
  not describe a donor's occupation, a local workplace count, or voting behavior.
- Household worker counts are not a count of all income earners. Households
  with no workers may receive retirement, Social Security, or other income.
- Family and household universes differ. Single-parent rates use families with
  own children under 18 as their denominator and retain that definition.
- Retirement-income receipt does not identify all retired persons.
- Ancestry responses overlap and should not be stacked into a population total.
  Race, ancestry, language, and place of birth do not establish religious identity.
- Residential mobility describes the prior home of current residents. It does
  not measure district outflow, net migration, or moves occurring in 2026.
- Seasonal / recreational / occasional-use housing is a Census vacancy category.
  It does not identify second-home voters. Building size does not identify co-ops.

No religious affiliation, political preference, voter eligibility, individual
donor identity, or absence of a community is inferred from these tables.
