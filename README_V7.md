# Chhattisgarh Opposition Monitoring Console — V7 District Activity Atlas

## New map

The Command Centre embeds an inline SVG with **33 real Chhattisgarh district polygons** from the open-source [Vardhan Maps](https://github.com/Vardhan-Systems/vardhan-maps) dataset, originally derived from OpenStreetMap. It is not an official survey-grade boundary map. **Data © OpenStreetMap contributors, ODbL 1.0.** Vardhan Maps source code is MIT licensed; its geographic data is ODbL.

Polygons are embedded in the HTML: no external map tiles, third-party JavaScript CDN, map API key, or image are needed. JavaScript enables district selection, responsive panel updates, filtered categories and log-scaled choropleth colouring; the static map still displays if JavaScript is disabled. A 33-name district roster offers accessible alternative navigation. Motion is subtle: a low-opacity scan, selected-district border pulse and colour transitions, with reduced-motion accessibility support.

### Five filters
- Leader: all ten or one named leader
- Issue: Tribal Issues, Religion/Hinduism, Governance, Minerals, Mining
- Evidence type: all source-linked records or reported public events
- From date and To date: 2023-01-01 to 2026-11-10
- Reset control

Click a district on the map or its label in the roster to open a district dossier with counts, associated electoral figures (explicitly **not evidence of work**), dated source records, public-event labels, publisher names and original URLs. Click a listed leader to filter the district.

**Heat colours measure the number of indexed source-linked district references** (logarithmic scale). They are *not* voter sentiment, district popularity, achievements, completed development projects, or verified physical movements. A Raipur press dateline may refer to a statewide statement rather than work in Raipur. For some historical records, the district is the **subject** of a parliamentary question or press statement, not where the leader was physically present.

## Data scopes

- `index.html` retains the **182 source-linked items from 5 Aug–5 Nov 2026** plus the full V6 archive, all ten political profiles, their five-category orbit navigators, YouTube/video and X link library, and publisher/source registry.
- `data/district_activity_2023_2026.json` contains **14 separately sourced historical district items** spanning 2023 through 2026. All ten leaders occur at least once; selected events have been differentiated from parliamentary demands or reporting. No claim of comprehensive historical coverage is made.
- Historical records are embedded in `index.html` in a `cgMapHistoricData` JSON script for offline/static viewing. They are intentionally **not counted in the 182-record August–November archive**. They affect the map only.
- Imported source-linked user records in the existing dashboard browser storage are also reflected in the district heat map when the tab is reactivated.
- Some leaders' areas of political association may not have reported activity; do not convert electoral affinity or press mentions into evidence of public projects.

### Geographic normalisation

The map groups selected city/constituency references into their containing district: Bhilai/Risali → Durg, Kharsia → Raigarh, Jagdalpur → Bastar, Ambikapur → Surguja, Kasdol → Baloda Bazar, Kanker → Uttar Bastar Kanker and several other named aliases. Ambiguous labels (e.g., `Raipur / statewide`, `Chhattisgarh`, `New Delhi`) are excluded from district heat calculations. More aliases require source-by-source verification.

## How to review

The page is entirely self-contained. Open `index.html` in a JavaScript-enabled browser or via GitHub Pages.

Run smoke tests (Node.js 22+):

```sh
npm install --no-save --no-package-lock jsdom@26
node qa/smoke.mjs
```

The `qa-district-atlas.yml` workflow runs smoke tests on the feature branch and pull requests. Tests check 33 map polygons, all ten political profiles/50 topic nodes, 182 historical-window records, 14 earlier district records, district clicks, leader filtering and 2024 date filtering.

## Interpretation and future collection

The requested multi-year district-level activity collection is **incomplete**, particularly outside the existing Aug–Nov 2026 study interval. For 2023–2025 there are 14 curated records, not an exhaustive feed. Expand one leader/district/year at a time, and preserve dated official records or direct source links. Districts with zero indexed records represent **collection gaps**, not political inactivity.

All records concern public political activity and official duties. Do not use the map to infer real-time whereabouts or undisclosed private movements. Pending promises, allocated funding, completed works, political criticism and allegations must remain distinct evidence types.

**Previous V6 docs** are available in this conversation and in earlier packaged artifacts.
