
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
from html.parser import HTMLParser
import ast,json,re,shutil,hashlib
BASE=RESEARCH_ROOT
SRC=BASE/'v5_reference/handoff/The_Sixty_Three_handoff'
OUT=BASE/'v5_data/handoff'
class N:
 def __init__(self,tag='root',attrs=(),parent=None):self.tag=tag;self.a=dict(attrs);self.c=[];self.parent=parent
 def text(self):
  return re.sub(r'\s+',' ',' '.join(c if isinstance(c,str) else c.text() for c in self.c)).strip()
 def nodes(self,tag=None):
  for c in self.c:
   if isinstance(c,N):
    if tag is None or c.tag==tag:yield c
    yield from c.nodes(tag)
 def cls(self,k):return k in self.a.get('class','').split()
class P(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.root=N();self.stack=[self.root]
 def handle_starttag(self,t,a):
  n=N(t,a,self.stack[-1]);self.stack[-1].c.append(n)
  if t not in ['img','br','hr','meta','link','input','source','wbr']:self.stack.append(n)
 def handle_endtag(self,t):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==t:self.stack=self.stack[:i];break
 def handle_data(self,d):self.stack[-1].c.append(d)
def parse(s):p=P();p.feed(s);return p.root
def constants(p):
 out={}
 def lit(x):
  if isinstance(x,ast.Name) and x.id in out:return out[x.id]
  if isinstance(x,(ast.List,ast.Tuple)):return [lit(v) for v in x.elts]
  if isinstance(x,ast.Dict):return {lit(k):lit(v) for k,v in zip(x.keys,x.values)}
  return ast.literal_eval(x)
 for n in ast.parse(Path(p).read_text()).body:
  if isinstance(n,ast.Assign):
   try:v=lit(n.value)
   except Exception:continue
   for target in n.targets:
    if isinstance(target,ast.Name):out[target.id]=v
 return out
def links(n):return [{'label':x.text(),'url':x.a['href']} for x in n.nodes('a') if x.a.get('href','').startswith(('http://','https://'))]
def table(n,heading=''):
 rows=[]
 for tr in n.nodes('tr'):
  cells=[c.text() for c in tr.c if isinstance(c,N) and c.tag in ['th','td']]
  if cells:rows.append(cells)
 return {'title':heading,'headers':rows[0] if rows else [],'rows':rows[1:],'links':links(n)}
root=parse((SRC/'v5/master_v5.html').read_text())
sections=[];sec_by={};alltables=[]
for n in root.nodes('section'):
 if not n.cls('sec'):continue
 h=next(n.nodes('h1'),None);heading=h.text() if h else ''
 blocks=[]
 for x in n.c:
  if not isinstance(x,N):continue
  if x.tag=='h1':continue
  if x.tag in ['h2','h3']:heading=x.text();blocks.append({'type':'heading','text':heading})
  elif x.tag=='table':
   t=table(x,heading);blocks.append({'type':'table',**t});alltables.append({'section':n.a.get('id'),**t})
  elif x.tag=='div' and x.cls('fig'):
   im=next(x.nodes('img'),None);cap=next((d for d in x.nodes('div') if d.cls('cap')),None)
   blocks.append({'type':'chart','imageAsset':Path(im.a.get('src','')).name if im else None,'caption':cap.text() if cap else '', 'title':heading})
  elif x.tag not in ['svg','script','style'] and x.text():blocks.append({'type':'text','text':x.text(),'links':links(x)})
 section={'id':n.a.get('id'),'title':h.text() if h else '', 'blocks':blocks};sections.append(section);sec_by[section['id']]=section
readme=(SRC/'README.md').read_text()
lay=re.search(r'## 5\. All 24 layers(.*?)(?=\n## 6\.)',readme,re.S).group(1)
layers=[]
for line in lay.splitlines():
 if not re.match(r'\| \d+\.',line):continue
 vals=[x.strip() for x in line.strip().strip('|').split('|')]
 id,title=re.match(r'(\d+)\. (.*)',vals[0]).groups()
 layers.append({'id':int(id),'title':title,'description':vals[1],'sources':vals[2],'evidenceType':vals[3],'phase':vals[4]})
assert len(layers)==24
page_text=(OUT/'master_plan_v5.txt').read_text()
pages=page_text.split('\f')
if not pages[-1].strip():pages.pop()
assert len(pages)==98,len(pages)
pages=[{'page':i+1,'text':p.strip()} for i,p in enumerate(pages)]
def js_array(name,source):
 m=re.search(r'const '+name+r'[^=]*=\s*(\[[\s\S]*?\n\]);',source)
 if not m:return []
 text=re.sub(r',\s*([\]}])',r'\1',m.group(1))
 return json.loads(text)
media=[];layerjs=(SRC/'src/layers.tsx').read_text()
for symbol,plat in [('XP','X'),('YT','YouTube'),('POD','Podcast / radio')]:
 for i,row in enumerate(js_array(symbol,layerjs)):
  publisher,kind,date,summary,evidence,url=row
  tags=sorted(set(int(d) for d in re.findall(r'\bSD\s?(\d{1,2})\b',' '.join(row))))
  media.append({'id':symbol.lower()+'-'+str(i+1),'platform':plat,'publisher':publisher,'publisherType':kind,'publishedAtLabel':date,'timezone':'Asia/Kolkata','summary':summary,'evidenceType':evidence,'sourceUrl':url,'districts':tags,'association':'Explicit district tag only' if tags else 'Statewide / unassigned','verificationStatus':'Historical link recorded in supplied v5 handoff; not re-opened in this import','recordedAt':'2026-11-20'})
v4=constants(SRC/'v5/layers_19_23_data.py');v3=constants(SRC/'v3/layers_17_18_data.py');v5=constants(SRC/'v5/layer24_sources.py')
sources=[]
for row in json.loads((SRC/'src/src.json').read_text()):
 sources.append(dict(zip(['id','title','publisher','publishedAt','sourceUrl','districts','topics','sourceType'],row)))
for name,rows in [('V',v4['VSRC']),('R',v3['RSRC']),('M',v5['NSRC'])]:
 for row in rows:
  obj=dict(zip(['id','title','publisher','publishedAt','sourceUrl','verificationStatus'],row));obj['recordedAt']='2026-11-20' if name=='M' else '2026-11-19';sources.append(obj)
for i,row in enumerate(json.loads((SRC/'src/layer_links.json').read_text())):
 sources.append(dict(zip(['title','publisher','publishedAt','sourceUrl'],row))|{'id':f'L{i+1}','verificationStatus':'Historical link from supplied handoff'})
for s in sources:
 url=s.get('sourceUrl','')
 # Retain explanatory source text separately when it is not a valid bare URL.
 if not re.match(r'^https?://[^\s]+$',url):s['sourceNote']=url;s['sourceUrl']=re.match(r'^(https?://[^\s]+)',url).group(1) if re.match(r'^(https?://[^\s]+)',url) else None
 s.setdefault('verificationStatus','Imported from supplied handoff; not independently reverified in this import')
# Import native, hand-written chart values through literal AST parsing. No handoff code is executed.
c=constants(SRC/'v5/charts.py')
series={
'c09_office_availability_trend':{'unit':'percent','geography':'Manhattan','measure':'Office availability, Colliers series','points':[{'period':p,'value':v} for p,v in c['pts']],'sourceIds':['M13','M15'],'status':'Partly verified in handoff; gaps between quarters are not observations'},
'c10_office_yardsticks':{'unit':'percent','geography':'Manhattan','period':'Q3 2026','measure':'Broker yardsticks, differing definitions','points':[{'label':p.replace('\n',' '),'value':v} for p,v,*_ in c['yk']],'sourceIds':['M14'],'status':'Different firms and vacancy/availability definitions; not a single comparable series'},
'c11_manhattan_rent_vacancy':{'geography':'Manhattan','series':[{'label':'Median new-lease rent','unit':'USD','points':[{'period':p,'value':v} for p,v,z in c['rj']]},{'label':'Listing vacancy','unit':'percent','points':[{'period':p,'value':z} for p,v,z in c['rj']]}],'sourceIds':['M10'],'status':'Elliman/Miller Samuel figures imported from handoff; individual source URLs not retained'},
'c12_manhattan_sales':{'geography':'Manhattan','series':[{'label':'Median sale price','unit':'USD','points':[{'period':str(y),'value':v} for y,v in zip(range(2016,2026),c['med'])]},{'label':'Closed sales','unit':'sales','points':[{'period':str(y),'value':v} for y,v in zip(range(2016,2026),c['ns'])]}],'sourceIds':['M11'],'status':'Elliman/Miller Samuel handoff figures'},
'c13_comptroller_outmigration':{'geography':'New York City','series':[{'label':'All part-year filers, net federal AGI','unit':'USD billions','points':[{'period':str(y),'value':v} for y,v in zip(c['yy'],c['allb'])]},{'label':'Filers with $1 million or more, net federal AGI','unit':'USD billions','points':[{'period':str(y),'value':v} for y,v in zip(c['yy'],c['m1'])]}],'sourceIds':['M9'],'status':'NYC Comptroller Fiscal Note 7-2025, Table 8; not tax revenue'},
'c14_hamptons_prices':{'geography':'Hamptons','series':[{'label':'Single-family plus condominium median','unit':'USD thousands','points':[{'period':p,'value':v} for p,v in c['s1']]},{'label':'Single-family median','unit':'USD thousands','points':[{'period':p,'value':v} for p,v in c['s2']]}],'sourceIds':['M16','M17','M18'],'status':'Series definitions differ; Q3 2020 and Q3 2026 partly verified in handoff'}
}
chart_info={}
last={}
for node in ast.parse((SRC/'v5/charts.py').read_text()).body:
 if not isinstance(node,ast.Expr) or not isinstance(node.value,ast.Call) or not isinstance(node.value.func,ast.Name):continue
 call=node.value
 if call.func.id=='head':
  last={}
  for k,arg in zip(['title','subtitle'],call.args[1:3]):
   try:last[k]=ast.literal_eval(arg)
   except Exception:pass
 if call.func.id=='foot':
  try:last['sourceText']=ast.literal_eval(call.args[1])
  except Exception:pass
 if call.func.id=='save':
  try:chart_info[Path(ast.literal_eval(call.args[1])).stem]=last.copy()
  except Exception:pass
charts=[]
for b in sec_by['s20']['blocks']:
 if b['type']=='chart':
  filename=b['imageAsset'];key=Path(filename).stem
  file=SRC/'v5/charts'/filename
  if file.exists():shutil.copy2(file,OUT/'charts'/filename)
  charts.append({'id':key,'file':'charts/'+filename,'title':chart_info.get(key,{}).get('title',b['title']),'sectionTitle':b['title'],'subtitle':chart_info.get(key,{}).get('subtitle'),'sourceText':chart_info.get(key,{}).get('sourceText'),'caption':b['caption'],'data':series.get(key),'sourceState':'Imported v5 chart; preserve geographic unit and original evidence qualifications'})
# Structured research catalogs include every method/gap field from their source rows.
research={'studentSegments':[t for t in alltables if t['section']=='s6'], 'employmentSegments':[t for t in alltables if t['section']=='s7'],
 'voterBlocs':[t for t in alltables if t['section']=='s3'],'households':[t for t in alltables if t['section']=='s8'],
 'communities':{'columns':['group','field','acsCell','note'],'rows':v4['GROUPS']},
 'professions':{'columns':['profession','acsField','detailedCodeRoute','organizations','method','evidenceType'],'rows':v4['PROFS'],'methods':v4['PROF_COMMON']},
 'schools':{'columns':['school','admissionRoute','borough','officialSite','studentPublication','reddit'],'rows':v4['SCHOOLS'],'methods':v4['SCHOOL_METHOD'],'ethics':v4['SCHOOL_ETHICS']},
 'ethnicMedia':{'columns':['community','outlet','language','sourceUrl','verificationInHandoff'],'rows':v4['MEDIA'],'exclusions':v4['MEDIA_DROPPED']},
 'platforms':{'columns':['platform','captures','relevance','accessRoute','verification','evidenceType','limits'],'rows':v3['PLAT']},
 'reddit':{'communities':v3['SUBS'],'threads':v3['HYPER'],'metrics':v3['METRICS'],'access':v3['ACCESS'],'ethics':v3['ETHICS']},
 'nativeNations':v4['RES'],'communityStudy':v4['UJA'],'communityPlaceContext':v4['PLACES']}
issues=[t for t in alltables if t['section']=='s2']
obj={'meta':{'title':'The Sixty-Three — v5 handoff evidence','preparedAt':'2026-11-20','importedAt':'2026-11-23','timezone':'Asia/Kolkata','sourceFile':'NY_State_Senate_Terminal_Master_Plan_v5.pdf','pageCount':98,'sourceSha256':hashlib.sha256((BASE/'v5_reference/master-plan/NY_State_Senate_Terminal_Master_Plan_v5.pdf').read_bytes()).hexdigest(),'status':'Historical supplied research; fresh records are separately dated','note':'Document-imported figures are not automatically newly verified. County/city/state migration does not establish district flows or individual voting behavior.'},'layers':layers,'pages':pages,'sections':sections,'issueDefinitions':issues,'issueCatalog':[dict(zip(['id','title','status','regions','indicators','evidenceType','voterBlocs'],r)) for t in issues for r in t['rows']],'migration':{'charts':charts,'tables':[t for t in alltables if t['section']=='s20'],'sourceIds':['M'+str(i) for i in range(1,25)],'note':'Migration and real estate records retain their original city, county, state or market geography. No county-to-Senate-district population allocation has been inferred.'},'researchGroups':research,'media':media,'sources':sources}
(OUT/'normalized.json').write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')))
(OUT/'tables.json').write_text(json.dumps(alltables,ensure_ascii=False,indent=2))
print(json.dumps({'pages':len(pages),'layers':len(layers),'sections':len(sections),'tables':len(alltables),'migrationCharts':len(charts),'migrationTables':len(obj['migration']['tables']),'media':len(media),'sources':len(sources),'outputBytes':(OUT/'normalized.json').stat().st_size}))
