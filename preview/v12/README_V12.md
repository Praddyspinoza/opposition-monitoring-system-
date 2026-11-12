# Chhattisgarh Political Intelligence Terminal — V12 Preview

Preview: https://praddyspinoza.github.io/opposition-monitoring-system-/preview/v12/

Download one HTML file for your Mac: https://praddyspinoza.github.io/opposition-monitoring-system-/preview/v12/download.html

## Preservation

- Original V11 root `index.html` has **not** been replaced.
- V12 lives only in `preview/v12/` and retains the original V11 interface, 33-district SVG, data and underlying historical explorer.
- The single downloadable `preview/v12/index.html` contains CSS, scripts and an embedded source-data snapshot. The original automated external JSON fetches still depend on the parent repository when hosted alone.

## User-specified BJP roster (in display order, not an evaluative ranking)

1. Vishnu Deo Sai — Chief Minister
2. Kiran Singh Deo — BJP State President
3. Arun Sao — Deputy Chief Minister
4. Vijay Sharma — Deputy Chief Minister
5. O. P. Choudhary — Cabinet Minister
6. Deepak Mhaskey — BJP National Social Media Convenor (appointed August 2026)
7. Dr. Raman Singh — Assembly Speaker
8. Brijmohan Agrawal — Raipur MP
9. Bhavna Bohra — Pandariya MLA (also spelt Bhawna)
10. Kedar Kashyap — Cabinet Minister

The original ten opposition profiles remain available.

## Issues

Original: Tribal Issues; Religion / Hinduism; Governance; Minerals; Mining.

Added: Agriculture & Farmers; Internal Security & Bastar; Infrastructure & Development; Education, Healthcare & Employment; Environment & Forests.

The historical V11 archive has not been retroactively assigned to the five new categories. This requires source-based retagging.

## Source bases and pie-chart methodology

- V11: 182 original dated opposition reports in 05 August–05 November 2026, plus separate earlier map history.
- V12: expanded *selective* source-linked BJP sample of 112 records covering the same dates; 40 explicitly refer to Vishnu Deo Sai. Of 112 records, some are documented events or organisational activity rather than attributed statements.
- Each pie represents a distribution of **indexed issue-coded items** for that person in the filtered window, not all of their speeches.
- The BJP/Government *statement-only* mode counts only source-attributed reported statements. Its *all* mode includes documented public appearances and reports.
- The opposition charts use the existing V11 archive's five-category labels, which **do not establish that every mention contains an independently verified direct quote**. Do not compare opposition-report pie denominators to BJP-statement denominators as like-for-like measures.
- One primary issue per source record contributes to the pie. Secondary tags are included for search and district filtering but not the pie denominator.
- `0` or an empty chart means “not collected under this filter”, not “no statement was made”.
- Record date may reflect a newspaper's date of publication rather than the exact time a statement was made.
- Policy announcements, aspirations and source-reported claims are not automatically verified project outcomes.
- Bastar-division-wide references are not incorrectly pinned to Bastar district.

## CM X / Facebook / Instagram API collection

The CM profile links to `https://x.com/vishnudsai`, a handle attributed to Vishnu Deo Sai by PIB in 2026. No archived X or Meta originals were fabricated. Initial `cm_posts.json` deliberately contains **zero API-backed posts** until credentials are authorised.

`scripts/collect_cm_social_v12.py` uses only platform APIs:

- X `GET /2/users/by/username/vishnudsai`, then authorised full-archive `GET /2/tweets/search/all` for 2026-08-05 through 2026-11-05 (IST), excluding retweets and checking author ID.
- Facebook authorised Page `/{PAGE_ID}/posts` with permitted Page token and pagination.
- Instagram authorised Professional/Business account `/{IG_USER_ID}/media` with permitted token and pagination.
- Output `preview/v12/cm_posts.json` has the original post URL, date, text and source API status; never store credentials in the public file or commit them to the repository.
- Original posts default to **Unclassified** until a human analyst records an approved `issue` in `preview/v12/cm_post_labels.json`. Example shape: `{"https://x.com/vishnudsai/status/POST_ID":{"issue":"Governance","approved":true}}`. Do not infer issue tags from keywords alone.
- Missing tokens leave the existing archive unchanged, and API errors are reported as collection errors instead of being silently mistaken for a zero-post result.

### Secrets to configure in GitHub repository Settings → Secrets and variables → Actions

```
X_BEARER_TOKEN        # authorised X API full-archive tier
META_PAGE_TOKEN       # authorised Facebook Page access token
META_PAGE_ID          # corresponding Facebook Page ID
META_IG_TOKEN         # authorised Instagram professional-account access
META_IG_USER_ID       # corresponding Instagram account ID
```

Use Actions → **V12 CM X and Meta authorised backfill** → Run workflow. The backfill is intentionally manual, not scheduled: the requested window is fixed and historical API usage may be billed. A successful run commits source-linked `cm_posts.json`; the web preview loads it automatically.

**Permissions**: Facebook Pages and Instagram Professional accounts generally require authorised ownership, delegated permissions, or approved platform access. They cannot be comprehensively collected by bypassing restrictions. The X full-archive endpoint may require paid access; inspect current X API entitlements first.

### Source-backed imports without API credentials

The CM tab supports JSON import in the browser, strictly marked **browser-local / unverified**. These items are not pushed to GitHub and do not increase API-verified counters. Use the JSON export button to save and review them.


## V12.1 motion flow and original social-link recovery

The Command Centre now contains a real animated, interactive **Leader → Issue → District** evidence flow, with political-group, leader and issue selectors. It visualises indexed source links, **not public opinion, voter support, completed government work or physical travel**. Maximum eight SVG connections animate at once using CSS; there are no JavaScript animation intervals. Animations pause off-screen, pause with the browser tab, respect `prefers-reduced-motion`, and can be paused manually. Click a leader or issue node to filter the flow; a district node opens the existing 33-district map when its name matches one of the 33 administrative polygons.

The new `Original X & Meta links` tab and the CM dossier show **24 publisher-embedded original CM X status URLs** together with corroborating article URLs, within 05 Aug–05 Nov 2026. Their dates are derived from X's tweet ID timestamp and checked against the date window. They are **not** authenticated API post text and are not silently added to the 112 BJP research rows.

Original CM/CMO account links were recovered through the CMO-linked directory `https://linktr.ee/chhattisgarhcmo1`:

- CM X: `https://x.com/vishnudsai`
- CM Facebook: `https://www.facebook.com/vishnudeosai1`
- CM Instagram: `https://www.instagram.com/vishnudeosai/`
- CMO Facebook: `https://www.facebook.com/ChhattisgarhCMO`
- CMO Instagram: `https://www.instagram.com/chhattisgarhcmo/`
- CMO X: `https://x.com/ChhattisgarhCMO`

No independently recovered **Meta original post permalinks** have been added; direct account links are not a substitute for post-level evidence. The public-source tab also includes distinct X/Facebook/Instagram **search links** for all 20 leaders, clearly marked as research shortcuts rather than original-post records. Use the authorised Meta/X API workflow if full historical posts are required. Never attempt to evade platform access restrictions.

### Research quality and limitations

- 112 BJP/Government source-indexed items across ten leaders. 24 additional CM X post links are stored separately in `social_discovery.json`, not included in the 112 count. Some entries may be duplicates in real-world subject matter even if URLs are distinct.
- 182 V11 opposition reports retain their original tags; they are not a strictly equivalent population.
- The BJP pie in statement mode counts **source-attributed** items, not individually verified transcript quotations; date, speaker and source need further editorial verification.
- Civic flag ceremonies and universal ration entitlement are not automatically classified as religion or tribal policy.
- `scripts/qa_v12_preview.cjs` checks source integrity, script syntax, embedded JSON, counts, one-leader-one-URL deduplication, and X post ID dates.
- GitHub workflow `.github/workflows/qa-v12-preview.yml` runs static tests on preview edits and a headless Chrome smoke test if Chrome is available on the runner.
- Source-link visibility and original platform-post accessibility depend on the publishing site and platform. Original X posts may ask viewers to sign in.

## Publishing and download

With GitHub Pages publishing from `main` root, open the preview or the dedicated one-click download page URLs above. On the download page, click “Download complete V12 HTML website”. The HTML will save to the Mac Downloads folder; rename to `index.html` when hosting in another repository.

For ongoing automated data updates, keep the collector scripts and `data/` directory in the repository alongside the HTML. A single stand-alone HTML contains the initial data but not a secure API backend.

## Quality status / approval checkpoint

The source sample is **not an exhaustive research archive**. On 12 November 2026, V12.1 expanded the BJP/CM archive from 36 to 112 records and recovered 24 original CM X post permalinks from publisher coverage; these are separate evidence pools and do not justify a combined statement count. Validate all 112 BJP source URLs, dates, quoted positions, geographic associations and primary tags before an executive presentation; no independent browser end-to-end interaction test has been performed in this environment. Inspect both branches of the district map and the CM API status in the published site. Do not merge over V11 without approval.
