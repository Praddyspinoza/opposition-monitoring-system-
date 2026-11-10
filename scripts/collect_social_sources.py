#!/usr/bin/env python3
"""Collect public RSS discovery leads and optionally authorized X API posts.

Never disguises automated access, bypasses login, CAPTCHAs, robots.txt or
platform rate limits. News headlines are discovery leads, NOT original posts.
"""
from __future__ import annotations
import datetime as dt
import email.utils
import hashlib
import html
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SOCIAL = ROOT / "data" / "social_research_2026.json"
LEADS_FILE = ROOT / "data" / "social_updates.json"
X_POSTS_FILE = ROOT / "data" / "verified_x_posts.json"
HEADERS = {"User-Agent": "ChhattisgarhPublicNewsResearch/1.0 (public-source monitoring; no login)"}
TODAY = dt.datetime.now(dt.timezone.utc)
TODAY_IST = TODAY.astimezone(ZoneInfo("Asia/Kolkata")).date()
START = dt.date(2026, 8, 5)
SOCIAL_WORDS = re.compile(r"\b(tweet|twitter|facebook|instagram|social media|posted on x|x post|posted|viral post|social-media)\b|सोशल मीडिया|ट्वीट|फेसबुक|इंस्टाग्राम|पोस्ट|वायरल|एक्स पर|सोशल साइट|साझा किया", re.I)
HINDI_NAMES = {
    "Charan Das Mahant": "चरणदास महंत",
    "Deepak Baij": "दीपक बैज",
    "Bhupesh Baghel": "भूपेश बघेल",
    "T. S. Singh Deo": "टी एस सिंहदेव",
    "Phulo Devi Netam": "फूलो देवी नेताम",
    "Jyotsna Charandas Mahant": "ज्योत्स्ना महंत",
    "Mohan Markam": "मोहन मरकाम",
    "Sandeep Sahu": "संदीप साहू",
    "Devendra Yadav": "देवेंद्र यादव",
    "Umesh Patel": "उमेश पटेल",
}
TOPIC_RE = {
    "Tribal Issues": r"\b(tribal|adivasi|indigenous|pesa|forest rights|scheduled tribe)\b|आदिवासी|जनजाति|वनाधिकार",
    "Religion / Hinduism": r"\b(religion|hindu|temple|hareli|dussehra|religious|ram temple|durga)\b|हिंदू|धर्म|मंदिर|दुर्गा",
    "Governance": r"\b(government|governance|assembly|minister|scheme|policy|election|hospital|housing|farmers|paddy|school|education|employment|police)\b|सरकार|विधानसभा|चुनाव|योजना|किसान|धान|रोजगार|स्वास्थ्य|स्कूल",
    "Minerals": r"\b(mineral|iron ore|bauxite|steel|dmf|district mineral|ore lease)\b|खनिज|लौह अयस्क",
    "Mining": r"\b(mining|coal|mines|mine lease|hasdeo|secl|nmdc|fly ash)\b|खनन|कोयला|खदान|फ्लाई ऐश",
}
MAX_RECORDS = 350

def read_json(path: Path, fallback: dict) -> dict:
    try:
        x = json.loads(path.read_text(encoding="utf-8"))
        return x if isinstance(x, dict) else fallback
    except (OSError, ValueError):
        return fallback

def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def clean(v: str, maxchars: int = 480) -> str:
    v = re.sub(r"<[^>]*>", " ", v or "")
    return re.sub(r"\s+", " ", html.unescape(v)).strip()[:maxchars]

def topics(text: str) -> list[str]:
    return [topic for topic, pattern in TOPIC_RE.items() if re.search(pattern, text, re.I)]

def platform(text: str) -> str:
    if re.search(r"facebook|फेसबुक", text, re.I):
        return "Facebook"
    if re.search(r"instagram|इंस्टाग्राम", text, re.I):
        return "Instagram"
    if re.search(r"twitter|tweet|posted on x|x post|ट्वीट", text, re.I):
        return "X"
    return "Social / unconfirmed"

def request_text(url: str, token: str | None = None) -> str:
    headers = HEADERS.copy()
    if token:
        headers["Authorization"] = "Bearer " + token
        headers["Accept"] = "application/json"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as res:
        return res.read(1_800_000).decode("utf-8", "replace")

def to_date(raw: str) -> str | None:
    try:
        date = email.utils.parsedate_to_datetime(raw)
        if date.tzinfo is None:
            date = date.replace(tzinfo=dt.timezone.utc)
        return date.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat()
    except (TypeError, ValueError, OverflowError):
        return None

def discover_news(config: dict) -> tuple[list[dict], int, list[str]]:
    leads, successes, failures = [], 0, []
    accounts = config.get("x_accounts", [])
    for n, account in enumerate(accounts):
        leader = account["leader"]
        if n:
            # Polite jitter to spread requests, not to evade platform controls.
            time.sleep(random.uniform(2.3, 4.2))
        q = ('("' + leader + '" OR "' + HINDI_NAMES.get(leader, leader) + '") '
             '(tweet OR twitter OR facebook OR instagram OR "social media" OR सोशल OR पोस्ट OR ट्वीट) '
             'after:2026-08-04')
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
        try:
            root = ET.fromstring(request_text(url))
            successes += 1
        except (urllib.error.URLError, TimeoutError, ValueError, ET.ParseError) as error:
            failures.append(leader + ": " + type(error).__name__)
            continue
        for item in root.findall("./channel/item")[:45]:
            title = clean(item.findtext("title") or "", 200)
            description = clean(item.findtext("description") or "", 400)
            source = clean(item.findtext("source") or "Google News indexed publisher", 90)
            link = (item.findtext("link") or "").strip()
            date = to_date(item.findtext("pubDate") or "")
            if not (date and START.isoformat() <= date <= TODAY_IST.isoformat()):
                continue
            parsed = urllib.parse.urlparse(link)
            if parsed.scheme != "https" or not parsed.netloc or not re.search(r"news|google", parsed.netloc, re.I):
                continue
            text = title + " " + description
            if not SOCIAL_WORDS.search(text):
                continue
            # Name must be present, so another politician with a similar query doesn't get misattributed.
            pieces = [s for s in leader.split() if len(s) > 3]
            complete_english = leader.casefold() in text.casefold()
            full_hindi = HINDI_NAMES.get(leader, "") in text
            if not complete_english and not full_hindi and not (len(pieces)>1 and all(p.casefold() in text.casefold() for p in pieces)):
                continue
            rid = "RSS-" + hashlib.sha256((leader + "|" + link).encode("utf-8")).hexdigest()[:16]
            leads.append({
                "id": rid,
                "date": date,
                "leaders": [leader],
                "platform": platform(text),
                "topics": topics(text),
                "title": title,
                "summary": description[:350] or "Indexed news report; open publisher to inspect original",
                "url": link,
                "publisher": source,
                "source_type": "google_news_rss_discovery",
                "status": "unverified_press_discovery",
                "review_note": "RSS publisher link, not an authenticated original X/Meta post",
            })
    return leads, successes, failures

def confirmed_x_handles(config: dict) -> dict[str, str]:
    """Three identities with original X status URLs backed by the 2026 news archive."""
    found = {}
    for post in config.get("x_posts", []):
        m = re.fullmatch(r"https://x\.com/([A-Za-z0-9_]+)/status/\d+", (post.get("url") or "").rstrip("/"))
        if m and post.get("corroboration_url"):
            found[post["leader"]] = m.group(1)
    return found

def collect_authorized_x(config: dict, old: dict) -> dict:
    token = os.environ.get("X_BEARER_TOKEN", "").strip()
    records = {str(r.get("id")): r for r in old.get("posts", []) if r.get("id") and r.get("url")}
    handles = confirmed_x_handles(config)
    problems = []
    successful_requests = 0
    if not token:
        return {
            "schema_version": "1.0",
            "last_checked_utc": TODAY.isoformat(),
            "collection_status": "X_BEARER_TOKEN not connected; no direct API acquisition",
            "permission_requirement": "Approved X API v2 full-archive search access and verified account identities required; historical access depends on X tier",
            "confirmed_publisher_linked_handles": handles,
            "posts": list(records.values()),
        }
    # Use only publisher-backed X handles; unverified candidate account links never enter the API query.
    for leader, handle in handles.items():
        next_token = None
        for page in range(5):
            params = {
                "query": "from:" + handle + " -is:retweet",
                "max_results": "100",
                "start_time": "2026-08-04T18:30:00Z",
                "end_time": TODAY.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "tweet.fields": "created_at,author_id,lang,public_metrics",
                "expansions": "author_id",
                "user.fields": "username",
            }
            if next_token:
                params["next_token"] = next_token
            url = "https://api.x.com/2/tweets/search/all?" + urllib.parse.urlencode(params)
            try:
                data = json.loads(request_text(url, token))
                successful_requests += 1
            except (urllib.error.URLError, TimeoutError, ValueError) as error:
                problems.append(handle + ": " + type(error).__name__)
                break
            usernames = {str(u.get("id")): str(u.get("username", "")) for u in data.get("includes", {}).get("users", [])}
            for row in data.get("data", []):
                if usernames.get(str(row.get("author_id")), "").casefold() != handle.casefold():
                    continue
                if not row.get("created_at"):
                    continue
                date = row["created_at"][:10]
                if date < START.isoformat():
                    continue
                text = str(row.get("text", ""))[:8500]
                category = topics(text)
                if not category:
                    continue  # The research dashboard has only the original five subjects.
                ident = str(row.get("id", ""))
                if not ident.isdigit():
                    continue
                records[ident] = {
                    "id": ident,
                    "date": date,
                    "leaders": [leader],
                    "platform": "X",
                    "topics": category,
                    "title": "Author-posted X statement: " + clean(text, 110),
                    "summary": text,
                    "url": "https://x.com/" + handle + "/status/" + ident,
                    "publisher": "X API v2",
                    "source_type": "authenticated_x_api",
                    "verification": "Authenticated publisher-linked author_id and created_at; topic tags are keyword suggestions",
                }
            next_token = data.get("meta", {}).get("next_token")
            if not next_token:
                break
            time.sleep(1.3)
    return {
        "schema_version": "1.0",
        "last_checked_utc": TODAY.isoformat(),
        "collection_status": "partial_authenticated_api_run" if successful_requests else "x_api_unavailable_or_no_access",
        "permission_requirement": "Full archive API access required; no claim of exhaustive coverage",
        "confirmed_publisher_linked_handles": handles,
        "successful_requests": successful_requests,
        "errors": problems[:10],
        "posts": sorted(records.values(), key=lambda x: x["date"], reverse=True)[:1000],
    }

def main() -> int:
    config = read_json(SOCIAL, {})
    if not config.get("x_accounts"):
        print("ERROR: social research seed not found", file=sys.stderr)
        return 2
    old = read_json(LEADS_FILE, {"leads": []})
    fresh, successes, issues = discover_news(config)
    seen = {}
    for rec in list(old.get("leads", [])) + fresh:
        if not isinstance(rec, dict) or rec.get("status") != "unverified_press_discovery":
            continue
        link = rec.get("url")
        if not link or urllib.parse.urlparse(link).scheme != "https":
            continue
        seen[link] = rec
    total = sorted(seen.values(), key=lambda x: x.get("date", ""), reverse=True)[:MAX_RECORDS]
    save_json(LEADS_FILE, {
        "schema_version": "1.0",
        "last_checked_utc": TODAY.isoformat(),
        "collection_status": "partial" if issues else "complete_rss_discovery_run",
        "queries_attempted": len(config["x_accounts"]),
        "requests_succeeded": successes,
        "issues": issues[:15],
        "limitations": "Google News publisher discovery only. It does not authenticate individual X, Facebook, or Instagram posts. RSS links may redirect to publisher.",
        "leads": total,
    })
    x = collect_authorized_x(config, read_json(X_POSTS_FILE, {"posts": []}))
    save_json(X_POSTS_FILE, x)
    print(json.dumps({"rss_successes": successes, "rss_new": len(fresh), "rss_total": len(total), "api_status": x["collection_status"], "api_posts": len(x["posts"])}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
