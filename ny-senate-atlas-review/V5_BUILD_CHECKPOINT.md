# The Sixty-Three — v5 review build

Build date: 23 November 2026 (IST).

## Current status

The application and collected research snapshot are complete in this directory and configured for the repository's existing GitHub Pages deployment. This replaces the interrupted-build checkpoint.

Review URL: https://praddyspinoza.github.io/opposition-monitoring-system-/ny-senate-atlas-review/index.html

## Delivered

- Reference-style command center, official New York district geography, raised map with a CPU SVG fallback, selectable districts, heatmaps and a right-side dossier.
- 63 district records, 112 general-election candidates, certified 2024 history and explicitly unofficial 2026 results.
- 103 candidates with collected finance disclosure coverage; nine collection gaps remain visible. Gross monetary contributions are not cash on hand or net receipts.
- 20 issue workspaces, 848 dated evidence records including 96 explicit gaps, 63 official directory profiles, bill sponsorship and named roll-call evidence.
- 49 ACS metrics per district, source periods, universes and 90% margins of error; geography-specific NYC overlays and county-level migration context.
- 24-layer catalog, the dated v5 research handoff, source registry, comparison views, structured exports and real paginated PDF dossiers.
- Ordinary same-page navigation and direct downloads. The application does not call window.open, launch a print window or require popup permission.

## Validation

- All nine data parts decode byte-for-byte to the normalized research snapshot.
- Official geometry preserves all 63 district polygons, islands and holes; renderer area checks passed.
- Election audit: 1,769 checks passed, zero errors, with original source-counter warnings retained.
- Local browser review verified district selection, heatmap changes, dossier routes and a completed district PDF download.
- Independently generated SD44 and SD12 PDFs passed layout, source-link and content checks.
- The reproducible research_source package includes collectors, normalization scripts, original provenance/audit reports, a runtime restoration tool and a sealed file manifest.

## Interpretation limits

Election results remain unofficial until certification. Research-source dates, current incumbent profiles and incoming candidates are distinct. Missing collections remain missing rather than zero. Migration is a county measure, not an allocated Senate-district estimate; community demographics are not political preferences. Archived research figures and media references are dated in the interface. The deployed application is a collected research snapshot, not an unattended live data feed.

Only ny-senate-atlas-review/ is updated. The ny-senate-trial/index.html baseline is preserved.
