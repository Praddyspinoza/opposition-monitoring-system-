#!/usr/bin/env python3
"""Authorised CM social-post backfill for 05 Aug-05 Nov 2026 (IST).

Uses ONLY official authenticated APIs. Secrets stay in GitHub Actions secrets, never
in this source, the website, logs or the published JSON. No evasion or scraping.

X full archive needs paid/eligible API access.
Facebook needs permitted Page access; Instagram needs professional account access.
The script stores original post permalinks and text without assigning a policy issue
until a researcher has reviewed a URL in cm_post_labels.json.

Output: preview/v12/cm_posts.json (public, source-linked dataset).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "preview" / "v12" / "cm_posts.json"
LABELS = ROOT / "preview" / "v12" / "cm_post_labels.json"
TZ = ZoneInfo("Asia/Kolkata")
START = dt.datetime(2026, 8, 5, tzinfo=TZ)
END = dt.datetime(2026, 11, 6, tzinfo=TZ)   # exclusive
ISSUES = {
    "Tribal Issues", "Religion / Hinduism", "Governance", "Minerals", "Mining",
    "Agriculture & Farmers", "Internal Security & Bastar",
    "Infrastructure & Development", "Education, Healthcare & Employment",
    "Environment & Forests",
}
MAX_PAGES = 100

def parse_time(value):
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(TZ)
    except (ValueError, TypeError):
        return None

def in_scope(stamp):
    d = parse_time(stamp)
    return d is not None and START <= d < END

def request_json(url, bearer=None, allowed_hosts=None):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or (allowed_hosts and parsed.hostname not in allowed_hosts):
        raise RuntimeError("Refusing nonapproved API URL")
    headers = {"User-Agent": "ChhattisgarhResearchV12/1.0", "Accept": "application/json"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=35) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        # Never print response bodies or request URLs: they may contain tokens.
        raise RuntimeError("API HTTP status " + str(ex.code)) from None
    except Exception as ex:
        raise RuntimeError("API request failed (" + type(ex).__name__ + ")") from None
    if isinstance(payload, dict) and payload.get("error"):
        raise RuntimeError("API returned error (details suppressed to protect secrets)")
    return payload

def graph_page(path, fields, token, query=None):
    host = "graph.facebook.com"
    version = os.environ.get("META_GRAPH_VERSION", "v26.0").strip()
    if not version.startswith("v") or not version[1:].replace(".", "").isdigit():
        raise ValueError("Invalid META_GRAPH_VERSION")
    params = dict(query or {})
    params.update({"fields": fields, "access_token": token, "limit": "100"})
    url = "https://" + host + "/" + version + "/" + path + "?" + urllib.parse.urlencode(params)
    for page in range(MAX_PAGES):
        data = request_json(url, allowed_hosts={host})
        if not isinstance(data, dict) or not isinstance(data.get("data"), list):
            raise RuntimeError("Unexpected Meta page response")
        yield data["data"]
        url = (data.get("paging") or {}).get("next")
        if not url:
            return
    raise RuntimeError("Pagination limit reached; data may be incomplete")

def collect_x(token):
    root = "https://api.x.com/2"
    actor = request_json(root + "/users/by/username/vishnudsai?user.fields=username",
                         bearer=token, allowed_hosts={"api.x.com"})
    uid = str((actor.get("data") or {}).get("id", ""))
    if not uid or str((actor.get("data") or {}).get("username", "")).lower() != "vishnudsai":
        raise RuntimeError("Unable to verify X user ownership")
    params = {
        "query": "from:vishnudsai -is:retweet",
        "start_time": START.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "end_time": END.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "tweet.fields": "created_at,author_id,referenced_tweets",
        "max_results": "100",
    }
    seen = []
    for index in range(MAX_PAGES):
        uri = root + "/tweets/search/all?" + urllib.parse.urlencode(params)
        response = request_json(uri, bearer=token, allowed_hosts={"api.x.com"})
        for item in response.get("data", []):
            if str(item.get("author_id")) != uid or not in_scope(item.get("created_at")):
                continue
            if any(ref.get("type") == "retweeted" for ref in item.get("referenced_tweets", [])):
                continue
            post_id = str(item.get("id", ""))
            if not post_id.isdigit():
                continue
            seen.append({
                "id": "X-" + post_id,
                "date": parse_time(item["created_at"]).date().isoformat(),
                "timestamp": str(item["created_at"]),
                "platform": "X", "handle": "@vishnudsai",
                "url": "https://x.com/vishnudsai/status/" + post_id,
                "text": str(item.get("text", ""))[:5000],
                "api_verified": True, "collection_method": "authorised_x_api",
            })
        nxt = (response.get("meta") or {}).get("next_token")
        if not nxt:
            return seen
        params["next_token"] = nxt
    raise RuntimeError("X pagination limit reached; results not published as complete")

def collect_facebook(token, page_id):
    result = []
    for batch in graph_page(page_id + "/posts",
        "id,message,created_time,permalink_url,from{id}",
        token, {"since": str(int(START.timestamp())), "until": str(int(END.timestamp()))}):
        for item in batch:
            if not in_scope(item.get("created_time")):
                continue
            author_id = str((item.get("from") or {}).get("id", ""))
            if author_id and author_id != page_id:
                continue
            permalink = str(item.get("permalink_url", ""))
            if not permalink.startswith("https://"):
                continue
            result.append({
                "id": "FB-" + str(item.get("id", "")),
                "date": parse_time(item["created_time"]).date().isoformat(),
                "timestamp": item["created_time"], "platform": "Facebook",
                "handle": "Authorised CM Facebook Page",
                "url": permalink, "text": str(item.get("message", ""))[:5000],
                "api_verified": True, "collection_method": "authorised_meta_page_api",
            })
    return result

def collect_instagram(token, user_id):
    result = []
    for batch in graph_page(user_id + "/media",
        "id,caption,media_type,permalink,timestamp", token,
        {"since": str(int(START.timestamp())), "until": str(int(END.timestamp()))}):
        for item in batch:
            if not in_scope(item.get("timestamp")):
                continue
            permalink = str(item.get("permalink", ""))
            if not permalink.startswith("https://www.instagram.com/") and not permalink.startswith("https://instagram.com/"):
                continue
            result.append({
                "id": "IG-" + str(item.get("id", "")),
                "date": parse_time(item["timestamp"]).date().isoformat(),
                "timestamp": item["timestamp"], "platform": "Instagram",
                "handle": "Authorised CM Instagram Professional Account",
                "url": permalink, "text": str(item.get("caption", ""))[:5000],
                "api_verified": True, "collection_method": "authorised_meta_ig_api",
            })
    return result

def main():
    settings = [
        ("x", os.getenv("X_BEARER_TOKEN")),
        ("facebook", os.getenv("META_PAGE_TOKEN") and os.getenv("META_PAGE_ID")),
        ("instagram", os.getenv("META_IG_TOKEN") and os.getenv("META_IG_USER_ID")),
    ]
    if not any(value for _, value in settings):
        print("No authorised API credentials present. Existing public data unchanged.")
        return 0
    existing = {}
    if OUTPUT.exists():
        try:
            old = json.loads(OUTPUT.read_text(encoding="utf-8"))
            existing = {item["platform"] + "|" + item["url"]: item
                        for item in old.get("posts", [])
                        if item.get("api_verified") is True and item.get("url")}
        except (ValueError, OSError):
            existing = {}
    labels = {}
    if LABELS.exists():
        try:
            labels = json.loads(LABELS.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            raise RuntimeError("Invalid cm_post_labels.json")
    status = {key: {"state": "not_connected", "retrieved": 0} for key, _ in settings}
    collectors = [
        ("x", os.getenv("X_BEARER_TOKEN"), lambda: collect_x(os.environ["X_BEARER_TOKEN"])),
        ("facebook", os.getenv("META_PAGE_TOKEN") and os.getenv("META_PAGE_ID"),
            lambda: collect_facebook(os.environ["META_PAGE_TOKEN"], os.environ["META_PAGE_ID"])),
        ("instagram", os.getenv("META_IG_TOKEN") and os.getenv("META_IG_USER_ID"),
            lambda: collect_instagram(os.environ["META_IG_TOKEN"], os.environ["META_IG_USER_ID"])),
    ]
    for name, enabled, collect in collectors:
        if not enabled:
            continue
        try:
            received = collect()
            status[name] = {"state": "connected", "retrieved": len(received)}
            for item in received:
                key = item["platform"] + "|" + item["url"]
                existing[key] = item
        except Exception as ex:
            status[name] = {"state": "collection_error", "retrieved": 0, "error": str(ex)}
    for item in existing.values():
        item.pop("issue", None)
        item.pop("review_status", None)
        tag = labels.get(item["url"], {})
        if isinstance(tag, dict) and tag.get("issue") in ISSUES and tag.get("approved") is True:
            item["issue"] = tag["issue"]
            item["review_status"] = "human_approved"
        else:
            item["issue"] = "Unclassified"
            item["review_status"] = "needs_issue_review"
    payload = {
        "schema_version": "1.0",
        "window": {"start": "2026-08-05", "end": "2026-11-05", "timezone": "Asia/Kolkata"},
        "as_of_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provenance": "Official authenticated X / Meta API retrieval. Issue tags require human approval.",
        "status": status,
        "posts": sorted(existing.values(), key=lambda p: (p.get("date", ""), p.get("timestamp", "")), reverse=True),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote CM archive: " + str(len(payload["posts"])) + " posts, " +
          ", ".join(name + "=" + info["state"] for name, info in status.items()))
    return 0

if __name__ == "__main__":
    sys.exit(main())
