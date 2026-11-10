# Chhattisgarh Opposition Monitoring Console — V11 Social Intelligence

## Why this release exists

V10 displayed 20 Facebook/Instagram account slots but no verified original Meta posts. The interface appeared empty even though the pre-existing press archive already contained original X status URLs and newspaper reports about social-media statements. V11 puts **attributable evidence and coverage first**, not blank platform placeholders.

## What is in the interface

- **Social Intelligence · X / Facebook / Instagram** tab at `#meta`; existing Command Centre, geographic map, 10 leaders, all five topics, original 182-record news archive and V10 Meta import remain intact.
- **11 publisher-linked direct X status URLs**, including 5 retained from the original archive and 6 additional publisher-corroborated items. They relate to Bhupesh Baghel (8), Deepak Baij (2), and Charan Das Mahant (1). They have original X status links and corroborating press links. They are **not** incorrectly labeled as directly API-verified X text.
- **14 separate press-reported social references** across the monitoring interval, including Facebook-referenced debate reporting, X references, and reporting about social-media controversy. These are publisher reports, **not** original FB/IG/X posts unless the original permalink is separately indexed.
- A compact expandable **30-profile directory** (10 names × X, Facebook, Instagram). Uncertified candidate profile links remain clearly marked.
- Filters: evidence class, politician, platform, five-category topic, date range from 5 Aug 2026, text search; show more; source links and verification details. Native first-party Facebook/Instagram count remains **0 verified originals**, not a fictional corpus.
- Static no-JavaScript fallback with source links.

## Twice-daily permitted-source collection

`.github/workflows/social-source-collector.yml` targets 07:00 and 17:00 IST (GitHub schedule delays are possible). The Python 3.12 script `scripts/collect_social_sources.py`:

1. Searches a public Google News RSS endpoint for **attributable reported social-media activity** for all ten figures. It queries English and Hindi names within the historical monitoring period and uses modest polite request jitter (2.3–4.2 seconds) to avoid unnecessary load. This is *not* stealth access or evasion.
2. Preserves publisher and original indexed link, dates, names, provisional topic matches, deduplicated IDs. Discovery records are explicitly `unverified_press_discovery`, never represented as first-party posts.
3. Commits `data/social_updates.json` through normal GitHub Actions repository permissions. The UI requests that file from GitHub Pages but also works from the embedded seed if the feed is unreachable.
4. Optionally uses the official X API v2 `/2/tweets/search/all` when an authorized `X_BEARER_TOKEN` repository secret and historical API tier are available. **Only three publisher-backed X handles** are eligible by default. The API collector validates returned author IDs and usernames, excludes retweets, and retains only posts with five-topic keyword indications. It writes `data/verified_x_posts.json`. Full-archive search depends on the account's X tier and pricing; a run may be partial. No access tier or token is provided by the project.
5. Never attempts third-party Meta account export without authorization, identity spoofing, CAPTCHA bypass, unauthorized scraping, credential circumvention or evasion of platform restrictions.

### Actual run status

- One successful initial public RSS run was observed on 10 November 2026: ten RSS requests completed and **zero new eligible social leads** were found.
- **No X bearer token** connected: zero API-retrieved X posts. Historical X seed contains eleven publisher-corroborated original permalink references; this is not a complete 90-day post inventory.
- No verified Facebook/Instagram posts have been obtained.
- These numbers mean this is an operational *source-discovery system*, **not complete historic post scraping**. Absence is a coverage gap, not proof the person was silent.

## Correct way to obtain complete X and Meta records

For X, supply an authorized X API bearer token with full-archive search access as a GitHub Actions secret `X_BEARER_TOKEN`, then confirm additional leader handles with reliable source evidence before adding them to the acquisition allowlist. The current allowlist is strictly publisher-linked handles for Bhupesh Baghel, Deepak Baij and Charan Das Mahant. For Facebook and Instagram, supply rights-cleared first-party original exports with post URL, author, timestamp, media, exact text, and source. Third-party Facebook/Instagram organic posts generally cannot be bulk retrieved through standard APIs without access rights.

## Verification

`qa/social-smoke.mjs` validates eleven X URLs, 14 press leads, 30 profile slots, filter combinations, timeline search, no fabricated Meta posts, and no uncaught errors. `tests/social-browser-smoke.cjs` verifies browser controls and layout in desktop, iPad, iPhone, and no-JavaScript mode. Existing V7–V10 tests remain.

Important: There is no undocumented background job outside GitHub Actions, and GitHub Actions schedule execution may run later than the configured cron. Source coverage should be treated as evolving and incomplete.

## V11 source expansion and user-interface update

Six additional X status links were found in ANI-syndicated reporting and Pradesh Khabar publisher articles. The original status IDs allow a cross-check of UTC creation dates via X Snowflake encoding, but full first-party text remains unverified through official X API. Statements about PMAY housing, state advertising, elections, political rallies and festivals are **attributed to the authors/reports, not independently established facts**. See `data/social_research_2026.json` for each direct source URL and its corroborating article.

The earlier long list of unverified Facebook/Instagram account placeholders is collapsed by default. The top of the social tab shows the actionable evidence cards, with press/X/Meta status clearly distinguished. RSS discovery supports both Hindi and English leader names, but has no guarantee of complete coverage.
