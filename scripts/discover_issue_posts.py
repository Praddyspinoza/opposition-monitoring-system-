#!/usr/bin/env python3
"""Collect original public X / Facebook / Instagram permalinks from indexed news.

Only public RSS and publisher pages are fetched, using normal HTTP access. No login,
stealth scraping, automated Meta/X access, CAPTCHA evasion or credentials are used.
Publisher-linked posts and context-derived issue tags require human verification.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SOCIAL = ROOT / "preview/v12/social_discovery.json"
OPP = ROOT / "data/social_research_2026.json"
META = ROOT / "data/meta_2026_aug_nov.json"
POSTS = ROOT / "preview/v12/social_intelligence_posts.json"
LEADS = ROOT / "data/issue_post_candidates.json"
STATE = ROOT / "data/issue_discovery_progress.json"
TZ = ZoneInfo("Asia/Kolkata")
NOW = dt.datetime.now(dt.timezone.utc)
DATE_MIN = dt.date(2026, 8, 5)
USER_AGENT = "CGPoliticalSourceIndexer/1.0 (public RSS and publisher HTML; no login)"
QUERY_LIMIT = min(60, max(1,int(os.environ.get("ISSUE_QUERY_BUDGET","32"))))
ALLOWED = ("indianexpress.com","haribhoomi.com","patrika.com","jagran.com",
 "timesofindia.indiatimes.com","pradeshkhabar.in","bharatnewsservice.com",
 "bhaskar.com","bansalnews.com","ndtv.in","tv9hindi.com","abplive.com",
 "etvbharat.com","naidunia.com","aajtak.in","news18.com","oneindia.com",
 "jansatta.com","livehindustan.com","amarujala.com","newsonair.gov.in",
 "indiatoday.in","pib.gov.in","scroll.in","thewire.in","thehindu.com",
 "business-standard.com","hindustantimes.com","apnachhattisgarh.com",
 "ajkinews.com","msn.com","firstpost.com","theweek.in","news24online.com")
ISSUES = {
 "Tribal Issues":("आदिवासी","tribal","pesa","जनजाति","वनाधिकार"),
 "Religion / Hinduism":("मंदिर","religion","धर्म","त्योहार","हिंदू"),
 "Governance":("सरकार","governance","भ्रष्टाचार","नीति","प्रशासन"),
 "Minerals":("खनिज","minerals","बॉक्साइट","royalty"),
 "Mining":("खनन","mining","कोयला","हसदेव","hasdeo"),
 "Agriculture & Farmers":("किसान","farmers","धान","सिंचाई"),
 "Internal Security & Bastar":("नक्सल","bastar","माओवादी","सुरक्षा"),
 "Infrastructure & Development":("सड़क","infrastructure","विकास","आवास"),
 "Education, Healthcare & Employment":("शिक्षा","healthcare","रोजगार","employment"),
 "Environment & Forests":("वन","forest","पर्यावरण","environment")}
NAMES = {
 "Vishnu Deo Sai":"विष्णु देव साय","Kiran Singh Deo":"किरण सिंह देव",
 "Arun Sao":"अरुण साव","Vijay Sharma":"विजय शर्मा",
 "O. P. Choudhary":"ओपी चौधरी","Deepak Mhaskey":"दीपक म्हस्के",
 "Dr. Raman Singh":"रमन सिंह","Brijmohan Agrawal":"बृजमोहन अग्रवाल",
 "Bhavna Bohra":"भावना बोहरा","Kedar Kashyap":"केदार कश्यप",
 "Charan Das Mahant":"चरणदास महंत","Deepak Baij":"दीपक बैज",
 "Bhupesh Baghel":"भूपेश बघेल","T. S. Singh Deo":"टी एस सिंहदेव",
 "Phulo Devi Netam":"फूलो देवी नेताम",
 "Jyotsna Charandas Mahant":"ज्योत्स्ना महंत",
 "Mohan Markam":"मोहन मरकाम","Sandeep Sahu":"संदीप साहू",
 "Devendra Yadav":"देवेंद्र यादव","Umesh Patel":"उमेश पटेल"}
BJP = set(list(NAMES)[:10])
RSS_HOSTS = ("bing.com","news.google.com")
URLS = re.compile(r"""https?://(?:www\.)?(?:x\.com|twitter\.com|facebook\.com|instagram\.com)/[^\s<>"'\]\[()\\]+""",re.I)
X = re.compile(r"^https://x\.com/([a-zA-Z0-9_]+)/status/(\d{16,22})$",re.I)

def load(path, fallback):
 try:
  val=json.loads(path.read_text(encoding="utf-8"))
  return val if isinstance(val,dict) else fallback
 except (ValueError,OSError): return fallback

def save(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def allowed_host(url,domains):
 try:
  uri=urllib.parse.urlsplit(url)
  h=(uri.hostname or "").lower()
  return uri.scheme=="https" and any(h==d or h.endswith("."+d) for d in domains)
 except ValueError: return False

def read_public(url,domains):
 if not allowed_host(url,domains): return None,None
 try:
  req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"text/html,application/rss+xml"})
  with urllib.request.urlopen(req,timeout=14) as res:
   final=res.geturl()
   if not allowed_host(final,domains): return None,None
   return res.read(1_600_000).decode("utf-8","replace"),final
 except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError,ValueError):return None,None

def canonical_post(value):
 raw=html.unescape(str(value or "")).replace("\\/","/").rstrip(".,;")
 if raw.startswith("http://"):raw="https://"+raw[7:]
 try:u=urllib.parse.urlsplit(raw)
 except ValueError:return None
 host=(u.hostname or "").lower().removeprefix("www.").replace("twitter.com","x.com")
 if host not in ("x.com","instagram.com","facebook.com"):return None
 path=u.path.rstrip("/")
 if host=="x.com":
  m=X.fullmatch("https://x.com"+path)
  return ("https://x.com/"+m[1]+"/status/"+m[2]) if m else None
 if host=="instagram.com":
  if re.fullmatch(r"/(p|reel|tv)/[A-Za-z0-9_-]+",path):return "https://www.instagram.com"+path+"/"
  return None
 if re.fullmatch(r"/[A-Za-z0-9_.-]+/posts/[A-Za-z0-9_-]+",path):return "https://www.facebook.com"+path
 if re.fullmatch(r"/(posts|reel|videos)/[A-Za-z0-9_-]+",path):return "https://www.facebook.com"+path
 if path=="/permalink.php":
  query=urllib.parse.parse_qs(u.query)
  if query.get("story_fbid") and query.get("id"):
   return "https://www.facebook.com/permalink.php?"+urllib.parse.urlencode({"story_fbid":query["story_fbid"][0],"id":query["id"][0]})
 return None

class AnchorParser(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag.lower() in ("a","iframe","blockquote","link","meta"):
   self.links.extend(v for k,v in attrs if k in ("href","src","cite","content") and v)

def embedded_posts(page):
 page=html.unescape(page.replace("\\/","/").replace("\\u002F","/").replace("\\u0026","&"))
 collector=AnchorParser()
 try:collector.feed(page)
 except ValueError:pass
 return sorted({p for url in collector.links+URLS.findall(page) if (p:=canonical_post(url))})

def x_timestamp(url):
 m=X.fullmatch(url)
 if not m:return None
 try:return dt.datetime.fromtimestamp(((int(m[2])>>22)+1288834974657)/1000,dt.timezone.utc).astimezone(TZ).date()
 except (OSError,OverflowError,ValueError):return None

def original_handles():
 known={}
 def add(name,platform,url):
  if name not in NAMES or not url:return
  u=urllib.parse.urlsplit(url)
  h=(u.hostname or "").lower().removeprefix("www.")
  if (platform=="X" and h!="x.com") or (platform=="Instagram" and h!="instagram.com") or (platform=="Facebook" and h!="facebook.com"):return
  bits=u.path.strip("/").split("/")
  if len(bits)==1 and bits[0] and bits[0] not in ("permalink.php","posts","reel"):
   known[(name,platform)]=bits[0].lower()
 for x in load(SOCIAL,{}).get("accounts",[]):add(x.get("person"),x.get("platform"),x.get("url"))
 for x in load(OPP,{}).get("x_accounts",[]):add(x.get("leader"),"X",x.get("profile_url"))
 for x in load(META,{}).get("accounts",[]):
  for p in ("facebook","instagram"):add(x.get("leader"),p.title(),(x.get(p) or {}).get("url"))
 return known

def identify(url,leader,known):
 u=urllib.parse.urlsplit(url)
 h=(u.hostname or "").lower().removeprefix("www.")
 p={"x.com":"X","instagram.com":"Instagram","facebook.com":"Facebook"}.get(h)
 handle=u.path.strip("/").split("/")[0].lower()
 return p, bool(known.get((leader,p)) and known[(leader,p)]==handle)

def pubdate(raw):
 try:
  d=parsedate_to_datetime(raw)
  if d.tzinfo is None:d=d.replace(tzinfo=dt.timezone.utc)
  return d.astimezone(TZ).date().isoformat()
 except (ValueError,TypeError,OverflowError):return None

def publisher_link(url):
 """Bing News RSS uses an apiclick URL with the genuine publisher in ?url=."""
 try:
  parts=urllib.parse.urlsplit(url)
  if (parts.hostname or "").lower() in ("www.bing.com","bing.com") and parts.path=="/news/apiclick.aspx":
   params=urllib.parse.parse_qs(parts.query)
   value=(params.get("url") or [""])[0]
   if value.startswith("http://"):value="https://"+value[7:]
   return value if allowed_host(value,ALLOWED) else None
  return url if allowed_host(url,ALLOWED) else None
 except ValueError:return None

def news_articles(query):
 for endpoint in (
  "https://www.bing.com/news/search?"+urllib.parse.urlencode({"q":query,"format":"rss"}),
  "https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":query,"hl":"en-IN","gl":"IN","ceid":"IN:en"})):
  xml,_=read_public(endpoint,RSS_HOSTS)
  if not xml:continue
  try:root=ET.fromstring(xml)
  except ET.ParseError:continue
  rows=[]
  for x in root.findall("./channel/item")[:12]:
   url=(x.findtext("link") or "").strip()
   article=publisher_link(url)
   if article:rows.append((x.findtext("title") or "",article,pubdate(x.findtext("pubDate") or "")))
  if rows:return rows
 return []

def scan_publishers(found, known, metrics, state):
 """Second discovery route: recent public publisher RSS items with embedded originals."""
 feeds=[
  "https://bharatnewsservice.com/feed/",
  "https://pradeshkhabar.in/feed/",
  "https://apnachhattisgarh.com/feed/",
  "https://ajkinews.com/feed/",
  "https://www.bansalnews.com/feed/",
  "https://www.jansatta.com/rss/chhattisgarh.xml",
 ]
 start=int(state.get("publisher_feed_cursor",0))%len(feeds)
 began=time.monotonic()
 scanned=0
 for step in range(3):
  if time.monotonic()-began>165:break
  scanned+=1
  rss_url=feeds[(start+step)%len(feeds)]
  text,_=read_public(rss_url,ALLOWED)
  metrics["publisher_feeds_scanned"]+=1
  if not text:continue
  try:root=ET.fromstring(text)
  except ET.ParseError:continue
  for item in root.findall(".//item")[:9]:
   if time.monotonic()-began>165:break
   title=" ".join((item.findtext("title") or "").split())[:225]
   link=(item.findtext("link") or "").strip()
   dated=pubdate(item.findtext("pubDate") or "")
   if dated and dated<DATE_MIN.isoformat():continue
   if not allowed_host(link,ALLOWED):continue
   article,final=read_public(link,ALLOWED)
   if not article:continue
   metrics["publisher_pages_read"]+=1
   excerpt=(title+" "+re.sub("<[^>]+>"," ",article[:14000])).casefold()
   plausible=[issue for issue,words in ISSUES.items() if any(word.casefold() in excerpt for word in words)]
   for post in embedded_posts(article)[:20]:
    for leader in NAMES:
     platform,matched=identify(post,leader,known)
     if not matched or post in found:continue
     when=x_timestamp(post) if platform=="X" else None
     if when and (when<DATE_MIN or when>NOW.astimezone(TZ).date()):continue
     published=when.isoformat() if when else dated
     if not published or published<DATE_MIN.isoformat():continue
     issue=plausible[0] if plausible else "Unclassified"
     found[post]={
      "id":"FEED-"+hashlib.sha256((leader+"|"+post).encode()).hexdigest()[:18],
      "leader":leader,"party":"BJP" if leader in BJP else "Opposition",
      "platform":platform,"date":published,
      "dateSource":"X_id_derived_date" if when else "publisher_date_NOT_post_date",
      "url":post,"title":title,"primaryIssue":issue,"secondaryIssues":plausible[1:3],
      "districts":[],"publisherUrl":final,"publisherName":urllib.parse.urlsplit(final).hostname,
      "evidenceClass":"public_publisher_embedded_original_permalink",
      "postVerification":"not_authenticated_from_platform_API",
      "identityVerification":"index_referenced_account_handle_match",
      "issueVerification":"publisher_context_preliminary",
      "reviewStatus":"needs_human_review","apiVerified":False}
     metrics["original_post_urls_added"]+=1
  time.sleep(0.5)
 return (start+scanned)%len(feeds)

def run():
 existing=load(POSTS,{"posts":[]})
 found={p["url"]:p for p in existing.get("posts",[]) if isinstance(p,dict) and p.get("url")}
 old_leads=load(LEADS,{"leads":[]})
 leads={str(p.get("source_url"))+"|"+str(p.get("post_url")):p for p in old_leads.get("leads",[]) if isinstance(p,dict)}
 state=load(STATE,{"cursor":0})
 known=original_handles()
 combos=[(n,issue) for n in NAMES for issue in ISSUES]
 start=int(state.get("cursor",0))%len(combos)
 metrics={"search_queries":0,"rss_articles":0,"publisher_pages_read":0,"original_post_urls_added":0,"unconfirmed_attributions":0,"publisher_pages_unavailable":0,"publisher_feeds_scanned":0}
 began=time.monotonic()
 processed=0
 for step in range(QUERY_LIMIT):
  if time.monotonic()-began>390:break
  leader,issue=combos[(start+step)%len(combos)]
  query='("'+leader+'" OR "'+NAMES[leader]+'") ('+ISSUES[issue][0]+' OR '+ISSUES[issue][1]+') (twitter OR facebook OR instagram OR post OR पोस्ट)'
  metrics["search_queries"]+=1
  for title,link,dated in news_articles(query)[:4]:
   metrics["rss_articles"]+=1
   if not allowed_host(link,ALLOWED):continue
   article,final=read_public(link,ALLOWED)
   if article is None:
    metrics["publisher_pages_unavailable"]+=1
    continue
   metrics["publisher_pages_read"]+=1
   combined=(title+" "+article[:70000]).casefold()
   if not (leader.casefold() in combined or NAMES[leader].casefold() in combined):continue
   if not any(term.casefold() in combined for term in ISSUES[issue]):continue
   posts=embedded_posts(article)
   if not posts:
    leads[final+"|"]={"leader":leader,"suggested_issue":issue,"publisher_title":title[:200],
     "source_url":final,"post_url":None,"publisher_date":dated,"status":"no_original_permalink_in_public_article"}
   for post in posts[:15]:
    platform,match=identify(post,leader,known)
    date=x_timestamp(post) if platform=="X" else None
    if date and (date<DATE_MIN or date>NOW.astimezone(TZ).date()):continue
    if not match:
     leads[final+"|"+post]={"leader":leader,"suggested_issue":issue,"publisher_title":title[:200],
      "source_url":final,"post_url":post,"platform":platform,"publisher_date":dated,
      "status":"original_post_link_found_but_author_not_confirmed"}
     metrics["unconfirmed_attributions"]+=1
     continue
    if post in found:continue
    published=date.isoformat() if date else dated
    if not published or published<DATE_MIN.isoformat():continue
    found[post]={"id":"DISC-"+hashlib.sha256((leader+"|"+post).encode()).hexdigest()[:18],
     "leader":leader,"party":"BJP" if leader in BJP else "Opposition","platform":platform,
     "date":published,"dateSource":"X_id_derived_date" if date else "publisher_date_NOT_post_date",
     "url":post,"title":title[:230],"primaryIssue":issue,"secondaryIssues":[],"districts":[],
     "publisherUrl":final,"publisherName":urllib.parse.urlsplit(final).hostname,
     "evidenceClass":"publisher_embedded_original_permalink",
     "postVerification":"not_authenticated_from_platform_API",
     "identityVerification":"index_referenced_account_handle_match",
     "issueVerification":"publisher_context_preliminary","reviewStatus":"needs_human_review","apiVerified":False}
    metrics["original_post_urls_added"]+=1
  processed+=1
  time.sleep(0.7)  # public-source rate limit; never evade 403/429 or access restrictions
 feed_cursor=scan_publishers(found,known,metrics,state)
 stamp=NOW.isoformat()
 existing.update({"asOf":stamp,"lastDiscoveryMethod":"public_news_RSS_and_publisher_page_permalink_extraction",
 "posts":sorted(found.values(),key=lambda x:(x.get("date") or "",x.get("leader") or ""),reverse=True)})
 existing["platformCounts"]={x:sum(p.get("platform")==x for p in found.values()) for x in ("X","Facebook","Instagram")}
 save(POSTS,existing)
 save(LEADS,{"last_checked_utc":stamp,"status":"unverified_public_discovery_leads",
  "limitations":"A publisher reference without a confirmed original author is not a verified leader post.",
  "leads":list(leads.values())[-1500:]})
 save(STATE,{"last_checked_utc":stamp,"cursor":(start+processed)%len(combos),
  "pairs_total":len(combos),"pairs_checked":processed,"publisher_feed_cursor":feed_cursor,"result":metrics})
 print(json.dumps({"pairs_total":len(combos),"next_cursor":(start+processed)%len(combos),**metrics}))
 return 0

def self_test():
 page='<a href="https://twitter.com/DeepakBaijINC/status/2086769976183230616?utm_medium=tw">tweet</a><iframe src="https://www.instagram.com/p/ABC123/"></iframe>'
 assert "https://x.com/DeepakBaijINC/status/2086769976183230616" in embedded_posts(page)
 assert "https://www.instagram.com/p/ABC123/" in embedded_posts(page)
 assert x_timestamp("https://x.com/DeepakBaijINC/status/2086769976183230616")
 assert canonical_post("https://www.facebook.com/BhupeshBaghelCG/posts/123456")=="https://www.facebook.com/BhupeshBaghelCG/posts/123456"
 print("Self-test passed: extracted X, Instagram and Facebook original links.")

if __name__=="__main__":
 if "--self-test" in sys.argv:self_test()
 else:sys.exit(run())
