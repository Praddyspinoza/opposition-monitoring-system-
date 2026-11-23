
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

import json,pathlib,re,urllib.parse
P=(RESEARCH_ROOT / 'v5_data/issues')
R=P.parents[1]
roster=json.loads((R/'election_research/senate_roster_2026.json').read_text())['senators']
home={};about={};errors=[]
for f in P.glob('profiles_raw_*.json'):
 d=json.loads(f.read_text());home.update({x['url']:x for x in d['results']});errors+=d.get('errors',[])
for f in P.glob('profiles_about_*.json'):
 d=json.loads(f.read_text());about.update({x['url'].removesuffix('/about'):x for x in d['results']});errors+=d.get('errors',[])
for f in [P/'profiles_about_fallback.txt',P/'profiles_committees_fallback.txt']:
 for part in re.split(r'\n-{20,}\n',f.read_text()):
  m=re.search(r'\((https://www.nysenate.gov/senators/[^/]+/about)\)',part)
  if not m:continue
  base=m[1].removesuffix('/about');txt='\n'.join(re.findall(r'^L\d+: ?(.*)$',part,re.M))
  txt=re.sub(r'【\d+†([^†】]+)(?:†[^】]*)?】',r'\1',txt)
  begin=txt.find('## About ');txt=txt[begin:] if begin>=0 else txt
  txt=re.sub(r'(?m)^\s*\* (.+?) ((?:Ranking |Co-)?(?:Member|Chair))\s*$',r'* \1\n  \2',txt)
  txt=txt.replace('## About Text Block','').strip()
  prev=about.get(base,{})
  about[base]={**prev,'url':m[1],'text':txt,'image_links':prev.get('image_links',[]),'links':prev.get('links',[])}
profiles=[]
for s in roster:
 u=s['profileUrl'];h=home.get(u,{});a=about.get(u,{});text=a.get('text','');imgs=a.get('image_links',[])+h.get('image_links',[])
 portrait=next((i for i in imgs if '/styles/4_3_large/' in i),None)
 hero=next((i for i in imgs if '/styles/senator_hero/public/' in i),None)
 committees=[];bio=''
 if '### Committees' in text:
  rest=text.split('### Committees',1)[1].strip();lines=rest.splitlines();last=0
  i=0
  while i<len(lines):
   ln=lines[i].strip()
   if not ln:i+=1;continue
   if ln.startswith('* '):
    name=ln[2:].strip();j=i+1
    while j<len(lines) and not lines[j].strip():j+=1
    role=lines[j].strip() if j<len(lines) and re.fullmatch(r'(?:Ranking |Co-)?(?:Member|Chair)',lines[j].strip()) else 'Unspecified'
    committees.append({'name':name,'role':role,'sourceUrl':u+'/about','retrievedAt':'2026-11-23'})
    i=j+1 if role!='Unspecified' else i+1;last=i;continue
   break
  bio='\n'.join(lines[last:]).strip()
 else:bio=text
 bio='\n'.join(ln for ln in bio.splitlines() if not re.match(r'^(?:About New York State Senator|Para leer la biograf|En Espa[ñn]ol)',ln.strip(),re.I)).strip()
 available=bool(bio) and 'bios will be released soon' not in bio.lower()
 news=[]
 for link in h.get('links',[]):
  if '/newsroom/' in link and not any(x['url']==link for x in news):
   raw=urllib.parse.unquote(link.rstrip('/').split('/')[-1])
   news.append({'title':raw.replace('-',' ').capitalize(),'url':link,'titleMethod':'Readable label derived from official URL; open source for exact headline','discoveredAt':'2026-11-23'})
 pro=dict(district=s['district'],name=s['name'],parties=s.get('parties',[]),profileUrl=u,aboutUrl=u+'/about' if a else None,
  profileStatus='Incoming member profile; not the serving incumbent at the 2026 election' if s['district']==12 else 'Official serving-member directory profile; separate from the November election outcome',
  retrievedAt='2026-11-23',biographyAvailable=available,biography=bio if available else None,biographyExcerpt=bio.split('\n\n')[0] if available else None,
  biographyAttribution='Official New York State Senate biography; office-authored',committees=committees,newsroomItems=news[:8],
  headshotUrl=portrait,heroImageUrl=hero,headshotSourceUrl=(u+'/about') if a else u,headshotVerified=bool(portrait),
  headshotAttribution='New York State Senate',imagePolicyUrl='https://www.nysenate.gov/policies-and-waivers',
  imageLicense='CC BY-NC-ND 3.0 US plus Senate CC+ permissions for pictures and graphics; broader derivative/commercial use excludes political fundraising',
  gaps=[])
 if not available:pro['gaps'].append('Biography not available from the retrieved official page.')
 if not committees:pro['gaps'].append('Committee list was not retrievable; do not infer memberships.')
 if not portrait:pro['gaps'].append('No exact official headshot URL was retrieved.')
 profiles.append(pro)
if (P/'portraits_manifest.json').exists():
 manifest=json.loads((P/'portraits_manifest.json').read_text())
 for pro in profiles:
  asset=next((r for r in manifest['portraits'] if r['district']==pro['district'] and r['status']=='downloaded'),None)
  if asset:pro.update(headshotLocalPath=asset['localPath'],headshotFilename=asset['filename'])
(P/'official_profiles.json').write_text(json.dumps({'meta':{'retrievedAt':'2026-11-23','count':len(profiles),'headshots':sum(bool(x['headshotUrl']) for x in profiles),'biographies':sum(x['biographyAvailable'] for x in profiles),'imagePolicyUrl':'https://www.nysenate.gov/policies-and-waivers','statusCaution':'SD12 incoming Aber Kawas profile is preserved separately from the vacant seat/incumbency at election; official biographies are office-authored, not independent assessments.'},'profiles':profiles,'fetchErrors':errors},ensure_ascii=False,indent=2))
out=json.loads((P/'normalized.json').read_text());out['profiles']=profiles
out['meta']['officialProfileCount']=len(profiles);out['meta']['officialHeadshotCount']=sum(bool(x['headshotUrl']) for x in profiles)
out['meta']['officialBiographyCount']=sum(x['biographyAvailable'] for x in profiles)
(P/'normalized.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'profiles':len(profiles),'headshots':sum(bool(x['headshotUrl']) for x in profiles),'biographies':sum(x['biographyAvailable'] for x in profiles),'committeeLists':sum(bool(x['committees']) for x in profiles),'noHeadshot':[x['district'] for x in profiles if not x['headshotUrl']],'noBio':[x['district'] for x in profiles if not x['biographyAvailable']]}))
