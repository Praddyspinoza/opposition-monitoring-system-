# Chhattisgarh Opposition Monitoring System — V9 district-by-leader intelligence

This iteration addresses the main research requirement: click **any of 33 real district polygons** (or the district roster) to open an evidence dossier that displays **all ten monitored leaders × all five original topics**.

## Research experience

- Clicking a district opens the detailed research panel below the map and scrolls to its heading; existing V8 map, motion flow, time playback, sidebar, leader dossiers and archive modules remain.
- Each dossier always shows the ten named leaders and the exact topic headings **Tribal Issues, Religion / Hinduism, Governance, Minerals, Mining** as a **10×5 matrix**. A cell is a count of indexed, dated, source-linked reports satisfying that leader, topic and district. A report may count for multiple leaders/topics; one report does not prove each named person was quoted.
- Selecting a leader, topic or matrix cell filters the dated news cards. Each source card shows original title and publisher link, date, credited leaders, issue tags, summary, evidence classification and explicit outcome/proof limitation.
- A search box filters the source text; a 'Show more' button loads records beyond the first 20. Source counts are not capped.
- The date range and 2023–2026 playback controls above the map also constrain the dossier. The dossier has an independent leader/topic filter so one can still compare all ten, even when a narrower map heat filter is active.
- A 'District relevance' switch separates **direct district-linked articles** from **venue-only indexed reporting**. A direct link means the title/summary explicitly references the district or mapped city/constituency, or the record was separately curated as a district-subject historical item. It does not prove the politician visited that district, the article quotes each named person, or any project was completed.
- When no item is indexed for a cell, the panel displays a collection gap and an external **unverified discovery search**, not a fabricated activity. This can occur in any of 1,650 potential district×leader×topic intersections.
- The map heat counts direct indexed references by topic and leader filters. Some records can relate to more than one district; there is no unique statewide event total implied by summing district counts. Bastar *region/division* is not automatically the same as Bastar *district*. References to 'Hasdeo Arand' alone cannot safely be assigned to a specific district.
- 33 boundaries are best-effort OSM-derived, not official survey-grade polygons. Sources and licensing are credited on the original map.

## Sources and coverage

The 182 original August–November 2026 media records have **not** been modified. Earlier historical material is in `data/district_activity_2023_2026.json`: **32** dated source-linked reports, parliamentary questions and proceedings, local meetings and press-covered demands across 2023–2026, up from the original 19 historical items.

The 13 newly indexed records concern:

- Mohan Markam / Kondagaon: 2023 Assembly allegation of DMF irregularities (The Indian Express).
- Bhupesh Baghel / Durg–Patan: August 2024 cattle-management protest and September 2024 farmers' power-transmission grievances (CG Mitan).
- Devendra Yadav / Durg–Bhilai: 2024 eviction-representation and three 2025 local utilities, roads, resident grievances and BSP township meetings (Bhilai Times).
- Sandeep Sahu / Baloda Bazar: 2025 Assembly employment question around cement factories (CG Mitan).
- Charan Das Mahant / Sakti: 2025 district mineral trust governing council meeting (Aaj Ki Jandhara).
- Jyotsna Charandas Mahant / Korba: 2024 Coal, Mines and Steel committee memorandum about SECL displaced families (Industrial Punch).
- Umesh Patel / Raigarh: February 2026 Assembly questions about fly-ash dumping and coal transport (PTI via Awaz the Voice).
- Deepak Baij / Uttar Bastar Kanker: 2025 Hahaladi mine-leasing concern mentioned in his Bastar-region memorandum. The public march took place in Dantewada, NOT Kanker (PTI via The Week).
- T. S. Singh Deo / Surguja: 2024 NDTV profile on Ambikapur health facilities; achievement claims are attributed to the broadcaster, not independently proven.

All corresponding source URLs, actionType and outcomeStatus fields are retained in the JSON and embedded in `index.html` for static hosting.

## Integrity boundaries

- No record can turn a parliamentary **request**, media allegation, proposed works, appointment or event announcement into a **completed development project** without additional official documents.
- A news outlet may mention a leader without quoting them; summaries therefore do not invent personal statements.
- The collection is *not* an exhaustive history for all ten leaders or every district from 2023; many empty cells remain valid research gaps.
- A source's dateline or event location can be different from the substantive district discussed.
- Source attribution, evidence freshness and district assignment should be checked before treating a record as the basis for a public claim.

## Automated QA

The GitHub Actions `qa-district-atlas.yml` smoke suite checks:
- 33 geographic polygons and 33 district options
- 50 preserved leader-topic orbit navigation controls
- 182 preserved 2026 archive records and 32 historical district records
- 10 matrix rows and 50 topic intersections
- district selection, source links, leader/topic selection, evidence relevance, keyword search, empty-district handling, reset
- date range / historical playback and no unhandled JavaScript exceptions.

`npm install --no-save --no-package-lock jsdom@26 && node qa/smoke.mjs`
