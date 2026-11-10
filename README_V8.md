# Chhattisgarh Opposition Monitoring Console — V8 verified research timeline

This release extends V7; it does **not** replace the 182-record Aug–Nov 2026 archive, the 10 leader dossiers, the 50 orbit-topic controls, or other V6/V7 modules.

## Live research atlas

- Geographic district heat map with **33 Chhattisgarh polygons** and 33 accessible district choices. Boundaries originate from Vardhan Maps (OSM-derived), attribution shown in the interface; not survey-grade boundaries.
- Source-linked district references and **reported public events only** are separate selectable evidence modes. Heat colour represents an indexed record count, not popularity, ideology, intensity of violence, public sentiment or confirmed development.
- New monthly timeline spanning **January 2023 to November 2026**, with Play/Pause and cumulative/month-only views. The date inputs remain editable. Playback is historical and never tracks real-time whereabouts.
- Dossiers expose the original publisher/date/URL, explicit action classification and **outcome status** for every curated historical item.
- Empty map districts indicate missing research coverage and must not be interpreted as leader inactivity.
- Historical content now comprises **19** separately source-linked district records, including 5 new legislative interventions from 2024–2025. The existing 182 contemporary-window records remain unchanged.
- The 19 historical entries include media reports and parliamentary demands; they are **not** 19 completed public projects. Where completed works cannot be independently verified, the interface explicitly says so.
- Some places are the district discussed or represented in a parliamentary intervention, not where a person traveled or spoke. Constituency affiliation is not evidence of physical presence or completed work.

## New sourced items

- 2024-07-29 — Jyotsna Charandas Mahant: requested Korba–Gevra train services and infrastructure. Source: PRS Legislative Research, Lok Sabha MP profile.
- 2025-02-11 — Jyotsna Charandas Mahant: sought improvements to Korba ESIC Hospital. Source: PRS.
- 2024-07-31 — Phulo Devi Netam: special mention on Kirandul floods and call for relief, compensation and investigation. Source: Rajya Sabha Secretariat synopsis (not final verbatim debate record).
- 2024-07-29 — Phulo Devi Netam: raised Sirpur's heritage recognition, district Mahasamund. Source: PRS and Mahasamund District administration for geography. **Not** connected by this dataset to later UNESCO tentative listing.
- 2024-08-02 — Phulo Devi Netam: demanded direct Delhi–Jagdalpur air service. Source: PRS Rajya Sabha index.

The individual links, evidence method and outcome disclaimers live in `data/district_activity_2023_2026.json` and inline in `index.html`.

## Regression testing

The `.github/workflows/qa-district-atlas.yml` workflow verifies original dataset preservation, 33 SVG polygons and roster entries, leader and date filters, timeline monthly/cumulative behavior and non-crashing JavaScript. Run with Node 22 and `jsdom@26` using `node qa/smoke.mjs`.

## Known limits / next collection requirements

Historical records before the August 2026 monitoring window are **not exhaustive**. No district should be assigned a "development achievement" on the basis of a protest, interview, request, constituency association or speculative attribution. Additional official MPLADS completion records, parliamentary and assembly questions, sanctioned orders and district administration records are needed for comprehensive "what they achieved" histories, especially 2023–2025.

No user-supplied custom records are deleted; the map also includes local browser-stored user imports when present.
