# Chhattisgarh Opposition Intelligence — V10 Facebook & Instagram research tab

## Collection scope and integrity

The **Meta post archive** is a dedicated tab, separate from the X/Meta source chronicle and the existing newspaper/documentary archive. Its defined historical window is **5 August–5 November 2026 inclusive** (Asia/Kolkata), covering the same ten named politicians and five substantive issue labels (Tribal Issues, Religion/Hinduism, Governance, Minerals, Mining).

**Status at creation (10 Nov 2026): 0 first-party Meta posts independently retrieved and timestamp-verified.** The absence of indexed posts is **not** evidence that the politician did not post. This is a functional research platform and an explicit collection gap, **not** a completed 90-day Facebook/Instagram scrape.

The account registry has ten names × two platform slots. Several candidate profile links were found in publicly indexed references, but none were authenticated against a complete original Meta historical feed. Entries marked `externally_referenced` identify **candidate** profiles, not certified official handles. Source URLs and caveats reside in `data/meta_2026_aug_nov.json`. Unknown handles intentionally remain unknown.

### Access and source limitations

- Attempts to access public Facebook pages encountered a temporary block, and public Instagram search results did not yield a complete attributable post corpus with permalinks and timestamps.
- This build does **not** ignore robots.txt, use login/session evasion, disguise browser fingerprints, rotate identities, defeat CAPTCHAs, or run randomized evasion retries.
- Meta Graph API and approved exports may be used in future when a relevant account and permissions are authorized. Third-party organic-post access is not implied by connected analytics for the operator's own accounts. Meta Ad Library is a **different** archive, mainly of advertising creative and its running dates, and must not be mislabelled as an archive of organic posts.
- Reports in newspapers attributing a statement to a Meta post are **discovery leads** until a first-party original post permalink and timestamp are independently established. They are not counted as verified posts.

## What the standalone tab does

1. Dedicated navigation entry `Meta post archive` and direct page anchor `#meta`.
2. All ten leaders, each with Facebook and Instagram candidate-account fields and external provenance links, with unverified identities clearly identified.
3. Original-post ledger with filters for person, platform, one of the five topics, dates, and caption/location search. The site-shipped ledger starts empty rather than claiming coverage.
4. Local-only import of documented post permalinks via JSON text, JSON file or CSV; strict validation of the ten names, original-post URL structure, platform-domain consistency, date window, five-topic vocabulary and duplicates. Generic profile links and unrelated domains are rejected. Imported records are always labeled **user-supplied/unverified**.
5. JSON and CSV export of the combined site dataset plus local records. No upload to GitHub occurs from the browser. Clearing the local archive needs confirmation and does not affect other users.
6. Distinct section for third-party discovery leads that are not first-party Meta post records.

### Import format

A JSON array or object `{"posts":[...]}`, with:

```json
[
  {
    "leader": "Bhupesh Baghel",
    "platform": "Instagram",
    "published_at": "2026-09-01",
    "url": "https://www.instagram.com/p/REPLACE_WITH_ORIGINAL_POST_ID/",
    "text": "Original caption, transcribed accurately",
    "topics": ["Governance"],
    "districts": ["Raipur"],
    "post_type": "photo"
  }
]
```

The example above is a **schema illustration only** and not an actual observed post. CSV uses the columns `leader,platform,published_at,url,text,topics,districts,post_type` and `|` between multiple topics or districts.

### Security and future integration

All imported text and links are HTML-escaped and original URLs are checked for approved Meta domains and post permalink patterns. Data is saved only to `localStorage` at `cg_meta_public_posts_local_v10`. This is client-local storage, not a shared team database and not a verified public corpus.

For a shared, audited archive, the next approved step is to acquire an authorized export or first-party permitted source with **original URL, author ID, created timestamp, exact caption, visual/media reference, source/provenance and issue tags**, review the evidence, then commit verified records to the checked-in JSON dataset.

## Regression tests

- `node qa/meta-smoke.mjs` uses jsdom to check navigation, 20 profile slots, zero-fabrication baseline, local import and proper rejection of out-of-window dates, profile links and non-Meta URLs.
- `node tests/meta-browser-smoke.cjs` exercises desktop/iPad/iPhone/no-JS Chromium displays, filters, valid and invalid fixtures, and mobile overflow.
- The existing district atlas, 182-item original archive, 32 historical district items and previous browser tests remain intact.

