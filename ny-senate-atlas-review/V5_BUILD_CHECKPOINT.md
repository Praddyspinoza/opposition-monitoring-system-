# The Sixty-Three — v5 build checkpoint

Updated 23 November 2026. **The redesigned application has not been published.** The execution environment and browser became unavailable during final verification and before the application commit. This document preserves the exact implementation state and recovery steps; it is not the new dashboard.

## Destination and preserved baseline

- Repository: Praddyspinoza/opposition-monitoring-system-
- Publish only the review directory: `ny-senate-atlas-review/`.
- Existing review URL: https://praddyspinoza.github.io/opposition-monitoring-system-/ny-senate-atlas-review/index.html
- Preserve `ny-senate-trial/index.html`; verified baseline blob: `a2e103b65da30a62918c9408694c037de347083f`.
- Last inspected branch head before interruption: `0bdd2b6d9fb7d107d35d8412c0d894398ac6ac17`. Refresh main before committing; unrelated automated updates exist.
- Application files last existed under `/workspace/scratch/17c1ffd12fdb/senate_v5/`. Their continued availability cannot be confirmed while the environment is unavailable.

## Visual and interaction requirements

Use the uploaded 1536×864 reference image as the exact visual composition: black/carbon frame, champagne-gold and silver, Capitol/skyline left rail, raised official NY Senate map in the center, district dossier on the right, and three lower intelligence panels. Use real names and records instead of the reference image's sample facts.

Ordinary HTTPS access on Mac/Safari is required. Internal views remain in the same page. No `window.open`, `target=_blank`, print-window export or popup-dependent navigation.

## Implemented application files

The buildless app is in `senate_v5/dist/`:

- `index.html`: reference-style shell, header, left navigation, command search and footer.
- `app.css`: black/gold/chrome design, responsive layouts, gradients, motion and reduced-motion mode.
- `app.js`: Command Center, district dossier, candidate profiles, twenty issue tracks, candidate/district/evidence filters, finance and shared-name network, Census tables, legislative records, media, comparison, migration, all24 layer catalog, source registry,98-page plan reader and downloads.
- `map3d.js`: actual Three.js extrusion of the official district polygons, hole preservation, lighting, gold selection, rotation, pan, zoom, focus, labels and cleanup.
- `mapsvg.js`: completed CPU-rendered SVG extrusion fallback. **Still needs importing and connecting in app.js's WebGL failure path.**
- `export.js`: synchronous `createDistrictPDF(data,id)`, returning a jsPDF document with embedded fonts, pagination, district map, candidates, donors, all issue records, all49 ACS metrics, legislative activity, sources and methods.
- `data.js`: losslessly gzipped/base64 runtime dataset, decoded by vendored fflate. Last size4,207,522bytes. The unpacked QA snapshot is `senate_v5/data-unpacked.json` (approximately21MB).
- `assets/reference-command-center.jpg`, seventeen supplied research chart PNGs, and vendored Three.js/jsPDF/fflate with licenses.
- `build_data.py`, `build_map.py`, `map-data.json` and `publish_manifest.json` are in the project parent.

`app.js` already uses `doc.output('blob')` and an ordinary download anchor; it does not call jsPDF's FileSaver `save()` fallback.

## Collected data

### Official geometry

All63 Senate shapes use official NYS GIS geography. The mesh contains823 polygon outers and4 holes. The map retains New York's recognizable outline and Long Island.

NYC detail in `v5_data/handoff/district_overlays.json` uses matching NYC26c geography, updated2November2026: all4,214 election-district polygons and all262 NTAs, with408 Senate/neighborhood intersections and no unassigned source features. Detail covers28 NYC Senate districts (10–34,36,47,59). SD34 and36 detail is explicitly NYC-only; statewide shapes retain their Westchester portions. No precinct vote totals were inferred.

### Elections and finance

Existing audited files:
- `election_research/senate_elections_2026.json`
- `election_research/district_counties_official.json`
- `finance_research/atlas_finance_normalized.json`

They include63 districts/112 general-election candidates, BOE unofficial21November2026 returns, certified2024 history, collected certified primaries and documented nonparticipation. The current snapshot has48DEM/15REP leaders; it is not labeled certified. SD43's340-vote lead and SD12's vacancy are preserved.

Finance covers103 of112 candidates. Nine missing records remain gaps, not zeros. Totals are gross monetary donations from1January2025 through22November2026; matching funds, loans, transfers and non-donation receipts are excluded, while refunds are not netted. Rankings are collected top-ten name/type groups, not all donors or confirmed shared identities.

### Fresh Census collection

`v5_data/census/normalized.json` contains38ACS2024five-year tables for all63 districts,49 headline indicators and26 groups per district, with original/derived90% margins of error and source universes. `household_cross_tabs.json` has additional income/family/tenure cross-tabs.

All partitions and percentage ranges passed validation. An independent official Census summary-file check matched1,386 estimate/MOE fields for population, median household income and household composition, with zero mismatches. Survey period2020–2024 is shown distinctly from retrieval23November2026. No demographic vote preference is inferred.

### Issues, legislation and profiles

`v5_data/issues/normalized.json` contains:
-20issue definitions.
-848unique evidence records:241imported records (145substantive and96explicit gaps), plus607fresh official records.
-16bills,13roll-call events,466named votes.
-99sources and63official member profiles.
-63official portraits cached in `portraits/`;62biographies and63committee lists.

Each issue has a freshly retrieved official source. Imported candidate statements retain the20Novemberhandoff status. Votes preserve the actual historical member and companion bill IDs (A11560,A9349,A10006 where applicable). The web app currently loads verified remote official portraits, with initials fallback. It maps by name/incumbency rather than assigning a serving senator's face to an opposing challenger.

### Handoff and migration

`v5_data/handoff/normalized.json`:98PDFpages,24layers,20issues,72tables,65historical media records,195source records,17chart objects and institutional/community catalogs.

`fresh_migration.json`: six IRS vintages2018–2019through2023–2024,372county totals,62county population series,1,994NYC county-pair records and county-context links for63districts. County flows are never allocated to districts. IRS matching-method change2022–2023 remains explicit; mover AGI is income, not tax revenue. Property figures retain their archival status.

## Completed validation

Browser preview successfully rendered the reference-style shell, accurate statewide2D fallback, SD44dossier, finance donor lists, Census/MOE bars, SD28NYCdetail,20issue tracks and district/person filters. A filtered James Tedisco data-centre record correctly displayed his Nay onA11560 and linked the official S10642record. Portrait, missing-transaction, source-ID deduplication, bill-ID and source-date presentation issues were corrected.

The managed browser disables WebGL, so the GPU3D renderer was not visually verified. CPU SVG fallback was subsequently implemented but not connected or browser-verified before interruption. Its structural tests passed:63clickable caps,827rings,316SVGpaths, all finite, full shoreline fit at1100×740,680×410and430×510, and all public control/cleanup methods.

PDF validation produced24pages forSD44and26pages forSD12, with all49ACSmetrics, every corresponding district evidence summary and every collected donor name. They have100/104clickable URL annotations, embedded fonts and no text outside page bounds. First/middle/last pages were visually inspected. Files and report are in `v5_data/handoff/pdf_validation/`.

## Exact remaining work when the workspace returns

1. Confirm the listed files are still present. Do not claim recovery before checking.
2. Import `createAtlasSVG` from `./mapsvg.js` and use it when Three.js context creation fails. Keep3D selected and hide the flat SVG only after fallback succeeds. Distinguish projection renderer in its small caption if useful.
3. Verify the raised SVG map, district selection, NYC/Long Island focus, heatmap controls and mobile/responsive layout in managed browser. Do not use an alternative browser process to bypass the unavailable managed preview.
4. Complete remaining UI checks: comparisons, migration, source reader, JSON/CSV and browser PDF download. The PDF generator itself is already content/layout validated.
5. Rebuild data only if inputs changed. Keep original source dates and all methodology.
6. Regenerate the publish manifest. Upload all finalized app assets and create an atomic tree based on fresh main, changing only the review directory. Preserve the trial baseline SHA.
7. Verify deployment and the actual public review URL before presenting it as the new build.

## Interrupted upload

A Git blob upload was attempted for compressed `data.js` (expected blob SHA `ff26d831d3c21bd9b4129dffc628523cae9e469f`). The execution runtime disappeared before a result. A later read did not find that blob, so **do not assume the upload or any new application publication completed**.

A fallback durable-file save also failed because no primary execution environment was available. This checkpoint is durable; the local build and data are not yet confirmed durable outside their execution workspace.
