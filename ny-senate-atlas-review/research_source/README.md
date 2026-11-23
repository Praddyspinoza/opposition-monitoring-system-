# The Sixty-Three: research source package

This compact package preserves the collectors, normalizers, reviewed mapping inputs, source metadata and audit reports behind the **23 November 2026** terminal edition. It contains **copies** of the research code; original application and collection files were not edited while assembling it.

The complete normalized tables remain in the application runtime. They are not duplicated here. Raw transaction rows, raw table downloads, profile captures, portraits, PDFs, rendered charts, third-party binary libraries and cached finance address samples are excluded.

## Recover the complete normalized snapshot

The preferred local checkpoint is `data-unpacked.json`. A published app instead contains `data-00.js`, `data-01.js`, and the remaining numbered parts plus a small `data.js` decoder. **All numbered parts are required.** The loader produces `window.SENATE_DATA` at runtime; the small `data.js` file alone does not contain the data.

From this package directory, point the restore tool at the unpacked checkpoint or at the directory containing the runtime files:

```sh
python3 restore_runtime.py --runtime ../dist --output ./work
# Alternatively, when the app files are beside research_source/:
python3 restore_runtime.py --runtime .. --output ./work
# Or use the complete local checkpoint:
python3 restore_runtime.py --runtime ../data-unpacked.json --output ./work
```

The tool decodes base64 and gzip with the Python standard library. It does **not** execute JavaScript, visit the network or run a collector. It supports the current split payload and the earlier single-file formats. It restores the original normalized filenames, derives the standalone historical/primary election files from their identical embedded district objects, retains already merged media records, and seeds small reviewed inputs and dated audit files. `work/restore_manifest.json` records input checksums and coverage. Existing differing files require `--overwrite` or a new output directory.

The runtime contains all application-normalized tables, including the full handoff text, ACS groups/cross-tabs present in the integrated Census dataset, issue evidence, finance rankings, official geometry and fresh migration records. It does **not** contain every underlying raw upstream row or every original source capture. Recovering the runtime and repeating an original raw-source normalization are different operations.

## Directory layout

| Path | Contents |
|---|---|
| `scripts/` | Adapted copies, retaining their original relative filenames |
| `audits/` | Original coverage, validation and fetch-provenance reports, with original dates |
| `metadata/snapshot_metadata.json` | Original normalized-file metadata, original filenames, sizes and SHA-256 hashes |
| `metadata/finance/` | Socrata source/schema metadata with all cached examples, owner/contact records and address samples removed |
| `metadata/copy_manifest.json` | Source-to-copy mapping, original and copied hashes, and declared adaptations |
| `inputs/` | Reviewed public candidate/committee ID mappings, selected filer IDs, official authorization mappings and minimal transaction-exclusion IDs/categories |
| `docs/` | Original Census and issue-data READMEs; their original folder-relative paths describe the source workspace |
| `validators/` | Optional PDF smoke-check script compatible with split runtime parts |
| `work/` | Default isolated working root; ignored by Git and absent from the committed package |

Every copied Python script finds `research_paths.py`, which defaults to `research_source/work/`. To use another isolated research root:

```sh
export SENATE_RESEARCH_ROOT="/absolute/path/to/research-work"
```

No copied script points at the original temporary workspace. Normalizers still use the edition's historical survey periods, election windows and fixed snapshot labels. Do not describe a future rerun as a newly dated release without reviewing those choices. Adapted fetch scripts record their actual execution-time retrieval timestamp; their data vintages remain explicit.

## Runtime keys and recovered source filenames

| Runtime key | Recovered file |
|---|---|
| `geometry` | `senate_v5/map-data.json`; also `geography/atlas_geometry.json` |
| `elections` | `election_research/senate_elections_2026.json` |
| `elections.districts[].history2024` | `election_research/senate_elections_2024.json` |
| `elections.districts[].primaryElections` | `election_research/senate_primaries_2026.json` |
| `finance` | `finance_research/atlas_finance_normalized.json` |
| `directory` | `election_research/district_counties_official.json` |
| `research` / `issuePlan` | `dossier_research/district_enrichment_compact.json` / `issues_corrected.json` |
| `handoff` | `v5_data/handoff/normalized.json` |
| `census` | `v5_data/census/normalized.json` |
| `issueEvidence` | `v5_data/issues/normalized.json` |
| `profiles` | `v5_data/issues/official_profiles.json` |
| `overlays` | `v5_data/handoff/district_overlays.json` |
| `migrationFresh` | `v5_data/handoff/fresh_migration.json` |

## Collection and reproduction routes

Use **Python 3.12** where possible. Most collectors and normalizers use only the standard library. Geometry and legacy PDF extraction need the packages in `requirements.txt`; Shapely 2.x is required by the integer-index `STRtree` queries. `pdftotext` from Poppler is needed to extract the original PDF text before a new handoff import. Network access to the named public sources is required for recollection.

### ACS: a complete collection route

```sh
python3 scripts/v5_data/census/pull_census.py
python3 scripts/v5_data/census/normalize_census.py
python3 scripts/v5_data/census/check_official_summary.py
```

This collects 38 Census-origin ACS 2020–2024 tables for all 63 Senate districts, retains raw estimates and 90% margins of error, and produces 49 headline metrics plus detailed groups. The optional official summary-file cross-check compares three tables against Census Bureau files. The retained original audit reports **1,386 estimate/MOE comparisons and zero mismatches**. See `docs/v5_data/census/README.md` and `audits/v5_data/census/`.

### IRS migration, PEP and county/town ACS

Restore the runtime first so the official district/county directory is available, then:

```sh
python3 scripts/v5_data/handoff/fetch_migration.py
python3 scripts/v5_data/handoff/build_migration.py
python3 scripts/v5_data/handoff/fetch_county_acs_mirror.py
python3 scripts/v5_data/handoff/enrich_charts.py
```

The migration collector covers six IRS vintages, 2018–2019 through 2023–2024, plus Census Population Estimates 2019 and 2025. The separate `fetch_county_acs.py` preserves the initial direct Census API attempt; its retained manifest records the failure. The Census Reporter mirror supplied Census-origin tables and original MOEs. The importer keeps archival images and real-estate series dated; `freshData` extends relevant numerical IRS charts. To rerun `enrich_charts.py`, begin from the restored edition or a fresh handoff import; it appends source entries and should not be repeatedly applied to its own enriched output without resetting that input.

### Geographic drilldown

```sh
python3 -m pip install -r requirements.txt
python3 scripts/v5_data/handoff/fetch_geography.py
python3 scripts/v5_data/handoff/build_overlays.py
```

The packaged geography fetcher includes the matching official NYC Senate polygons, which were downloaded separately in the original session. `build_overlays.py` also needs the raw official statewide Senate and shoreline GeoJSON files, plus the normalized statewide projection. Their source service URLs, original metadata and original hashes are retained in `metadata/` and the geometry audits. The restored runtime supplies the normalized projection and display paths; it does not recreate the raw GeoJSON. Obtain the exact raw files or repeat the documented official service query before rebuilding intersections.

The retained coverage is 4,214 EDs, 262 NTAs and 28 NYC Senate districts. SD34 and SD36 have only their NYC portion in the detailed NYC overlay. No precinct election returns or district migration estimates are inferred.

### Elections, finance, issues and original handoff

These normalizers preserve the original logic but have additional source-input requirements:

| Scripts | Inputs required beyond the recovered runtime |
|---|---|
| `election_research/normalize.py` | `official_enr_2026.md` and `roster_raw_0.json`, captured from the official BOE/roster pages |
| `normalize_history.py`, `enrich_elections.py` | Original `archive2024_raw.json` / `archive2026_raw.json` CSV capture wrappers |
| `audit_elections.py` | Recovered normalized election/history/primary/directory files; can run without raw captures |
| `finance_research/fetch_donations.py` | Reviewed selected/extra filer ID lists in `inputs/`, seeded by restoration |
| `aggregate_finance.py` | Downloaded contribution rows plus the reviewed mappings; the exact 22 reviewed exclusion IDs/categories and source timestamps are retained, while transaction narratives are excluded |
| `prepare_mapping.py` | Original active-filer register capture; the reviewed result is already retained as an input |
| `v5_data/issues/build_normalized.py` | User-supplied handoff source directory plus corrected issue definitions |
| `enrich_legislation.py`, `enrich_profiles.py` | Preserved official text/page captures, including fallback text files; these are not an independent fetch pipeline |
| `v5_data/handoff/import_handoff.py` | Original v5 PDF, extracted text and original handoff ZIP contents |
| `dossier_research/*.py` | Original v4 PDF and its embedded page snapshot; retained for legacy provenance |

Full raw-source reproduction therefore requires the original captures or a deliberate new source collection. Current official pages can change. Hashes and original retrieval dates support comparison; they do not make an omitted raw file recoverable. The finance source windows and deduplication/exclusion choices must be reviewed before any new edition. The packaged minimal exclusion file preserves the exact original normalizer behavior; it omits transaction names, amounts, dates and explanatory narratives. It should not be replaced with an empty file.

To repeat the finance fetch using the retained reviewed filer lists after restoration (shown for the default `work/` root):

```sh
python3 scripts/finance_research/fetch_donations.py work/finance_research/selected_filer_ids.json senate
python3 scripts/finance_research/fetch_donations.py work/finance_research/extra_filer_ids.json extra
python3 scripts/finance_research/fetch_donations.py work/finance_research/extra2_filer_ids.json extra2
python3 scripts/finance_research/fetch_donations.py work/finance_research/extra3_filer_ids.json extra3
python3 scripts/finance_research/aggregate_finance.py
```

Recollected raw finance files contain original disclosure fields and belong only in the isolated, ignored working directory. The submitted source package includes schema metadata and the reviewed mappings but no contributor-address data.

Source PDFs expected by the original code are `NY_State_Senate_Terminal_Master_Plan_v4.pdf` and `NY_State_Senate_Terminal_Master_Plan_v5.pdf`. The v5 source directory is `v5_reference/handoff/The_Sixty_Three_handoff/`; the v5 PDF belongs at `v5_reference/master-plan/`. These copyrighted/supplied files are not redistributed in this package.

### Application data build

The copied root build scripts are `scripts/senate_v5/build_map.py` and `build_data.py`. The latter writes to the isolated research root's `senate_v5/dist/`, including numbered packed data parts and the decoder. It needs a copied `index.html` there; it does not supply the rest of the application or its assets. `build_map.py` needs the raw official geometry. Do not point a research rebuild at a production directory until its outputs have been reviewed.

The optional PDF validator reads `data-unpacked.json` first, or decodes all runtime parts. It uses the app's existing vendored jsPDF and `export.js`:

```sh
node validators/validate_export.cjs ../dist ./work/pdf_validation
```

It generates local sample PDFs without opening windows. Original visual/content-validation reports are retained; the PDFs and font binaries themselves are not included here.

## Evidence boundaries retained

- 2026 general-election returns are unofficial; 2024 general results and collected primaries retain their certified labels.
- Donation rankings are gross disclosed monetary contributions within the stated window, not cash on hand. Nine candidate collection gaps remain gaps.
- ACS values describe the 2020–2024 survey period. Ancestry, race, language and birthplace do not establish religion or political preference.
- County migration stays at county or state geography. There is no invented population crosswalk into Senate districts.
- IRS matching changed beginning in 2022–2023; mover AGI is income associated with movers, not tax revenue.
- Issue-record counts measure collection coverage, not public sentiment. Imported campaign statements and newly retrieved legislative activity remain distinct.
- Archival chart 17 lacks its complete original 23-point scatter dataset; the printed eleven district rows and six correlations are preserved with that limitation.

The audit reports are historical evidence about this edition, not assertions that a future recollection will have the same coverage or results.

## Package verification

`metadata/package_validation.json` records local verification of this package: all Python and Node helper syntax checks passed; the nine published data parts decoded byte-for-byte to the 20,957,704-byte complete snapshot; restoration recovered 82 files; and the recovered election audit passed 1,769 checks with zero errors. The original two source-counter warnings remain disclosed. No live collector rerun is implied by those checks.

An independent read-only privacy audit checked all packaged files, every copied-file checksum, and 43 known original finance street-address samples. It found no raw transaction objects, cached financial examples, source financial addresses, portraits, PDFs or other prohibited binaries. `FILE_MANIFEST.json` lists SHA-256 hashes and byte sizes for every package file except the manifest itself.
