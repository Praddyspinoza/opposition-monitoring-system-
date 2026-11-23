# NY Senate v5 issue, legislation and profile data

Retrieved/imported **23 November 2026**. All deliverables are in this folder; no UI or repository files were changed.

## Runtime data

- `normalized.json`: primary integration file. `issues[20]`, `evidence[848]`, `sources[99]`, `legislation[16]`, `districtCoverage[63]`, `profiles[63]`.
- `official_profiles.json`: all 63 official directory profiles, exact names and district IDs, 62 available office-authored biographies, 63 committee lists, official newsroom links, exact headshot URLs and local filenames.
- `official_legislation.json`: 16 official bill records, source-page statuses, action histories, named sponsors/cosponsors, and 13 retrieved roll-call events containing 466 named votes.
- `portraits/` and `portraits_manifest.json`: 63 official headshots, 24,626,703 bytes total. All fetched successfully as image content. Manifest preserves source URL, profile URL, name, district, file, MIME type, SHA256, attribution and license.
- `audit.json`: checks issue/district uniqueness, complete retrieved floor roll calls, matching named-vote district IDs, source ID resolution and local portrait availability.

## Evidence semantics

The 241 supplied district entries were retained with their handoff provenance: **145 substantive evidence paragraphs**, including **112 candidate-position paragraphs**, plus **96 explicit research gaps**. Original `EV` through `EV6` block names, source IDs and exact source URLs are preserved. These are imported 17–20 November research, not newly verified campaign statements.

The newly retrieved official material contributes **607 records**: legislative sponsorship, cosponsorship, named floor and committee votes, and official policy/context records. Every issue has at least one newly retrieved official source. Every district has official legislative evidence. Counts describe evidence coverage, never public sentiment or candidate popularity.

`evidence` is the unique flat record list. `issues[].records` contains references expanded as complete objects for easy independent rendering, so do not sum issue record counts as if they were unique. `issueIds` can associate one record with several topics. `district` may be `null` for statewide or historical policy context. `candidates[]` contains current general-election ballot names matched in the same district. `candidate` is a single label where available; `personName` preserves the official legislator's name for legislative records.

Filter campaign claims using `evidenceCode === 'C'`; filter newly retrieved official records with `freshlyVerified`. Show `isGap` entries separately. Distinguish `publishedAt`/event date from `retrievedAt`. Legislative evidence has `campaignPosition: false`.

The S54 source is the handoff's The Gist/VOTE411 compilation homepage, not an original candidate-response permalink. Each affected record carries that limitation. The data does not silently upgrade those campaign statements to independently verified facts.

## Bill and vote identifiers

Bills retain the current official status as retrieved: a chamber passage is not a signed law. `billId` is the currently displayed amendment; `baseBillId` is stable. Individual votes include `votedBillIdAsDisplayed`, `rollCallId`, `voteType` and `vote`. This separates assembly companions A11560, A9349 and A10006 from their related Senate bill records. Official pages sometimes link a historical vote to the currently displayed amendment; `billIdNote` records this limitation. Only retrieved named votes are included. All retrieved floor roll calls contain 63 distinct district members and match the published totals. The 13 events are a collected set, not a promise of exhaustive bill vote history.

Cosponsor lists contain named official entries retrieved and are marked potentially incomplete. A sponsor or cosponsor is not assumed to have voted aye. Votes, absences and excusals are individually recorded.

Official policy sources cover the minimum wage schedule, COELIG July–August preliminary lobbying disclosure and its portal, and a historical DEC STAMP permit notice. The DEC source is dated 4 August 2021; retrieving it today does not make it the current permit or litigation outcome. Lobbying filings are not candidate donations.

## Profile and portrait integration

Match portraits by **name and district**, not district alone. A serving senator's photo must not be assigned to a different leading challenger. Official profile cards and current general-election candidate cards are distinct. SD12's Aber Kawas page is explicitly marked incoming; it is not evidence that she was incumbent at the election. That official page says the biography will be released soon, and no biography is invented.

Use `headshotFilename` after copying `portraits/` into the app's local asset directory. Keep `headshotSourceUrl`, `headshotAttribution` and `imagePolicyUrl` accessible. The official Senate copyright policy licenses pictures/graphics under CC BY-NC-ND 3.0 US with CC+ permissions, including broader derivative and commercial use unrelated to political fundraising: https://www.nysenate.gov/policies-and-waivers . No challenger portraits were guessed or generated.

## Rebuilding

Run `build_normalized.py`, then `enrich_legislation.py`, then `enrich_profiles.py`. These use preserved source captures. `enrich_profiles.py` reattaches already downloaded portrait manifest paths. Do not run `download_portraits.py` again unless a fresh asset download is actually needed. Raw official captures and handoff extraction code remain alongside these outputs for review.
