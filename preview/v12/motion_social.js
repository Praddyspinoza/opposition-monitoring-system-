(function v13InteractiveIntelligence(){
"use strict";
const byId=id=>document.getElementById(id);
const esc=value=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const safeUrl=value=>{try{const x=new URL(String(value||""));return x.protocol==="https:"?x.href:"";}catch(_){return "";}};
const loadTag=id=>{try{return JSON.parse(byId(id).textContent);}catch(_){return null;}};
const dataset=loadTag("v12Data")||{};
const op=loadTag("archiveData")||[];
const opposition=loadTag("peopleData")||[];
const discovery=loadTag("v12SocialLinksData")||{};
const topics=dataset.issueTaxonomy||[];
const bjp=(dataset.bjpLeaders||[]).map(x=>x.n);
const issueNames=topics.map(x=>x.id);
const topicColor=name=>(topics.find(x=>x.id===name)||{}).color||"#8cb3c5";
const normIssue=name=>{const k=String(name||"").toLowerCase().trim();if(k==="tribal issues"||k==="tribal rights"||k==="tribal issues / adivasi")return "Tribal Issues";return issueNames.find(x=>x.toLowerCase()===k)||null;};
const normDistrict=x=>{const s=String(x||"").trim();return !s||/statewide|national|multiple|division|not assign|all districts|not specified|not recorded/i.test(s)?"Region not assigned":s;};
const canonical=value=>String(value||"").replace(/[?#].*$/,"").replace(/\/$/,"").toLowerCase();
const nowStart="2026-08-05", historicalEnd="2026-11-05";
let postCorpus=(discovery.originalXPostLinks||[]).filter(x=>x.url).map(x=>({id:x.id,url:x.url,date:x.date,leader:x.leader,party:"BJP",platform:"X",title:x.title,primaryIssue:normIssue(x.issue)||"Unclassified",secondaryIssues:[],districts:[],publisherUrl:x.publisherUrl,publisherName:x.publisherName,evidenceClass:x.evidenceClass,postVerification:"publisher_corroborated_link_not_api_verified",issueVerification:"publisher_context_preliminary",reviewStatus:"needs_human_review",apiVerified:false}));
let activeSource="embedded source snapshot";
let socialIssue="all",socialLeader="all",socialQuery="";
let flow={bjp:"all",opp:"all",issue:"all",district:"all",period:"all",paused:false,open:false,limit:12};
const sourceRows=(dataset.bjpRecords||[]).filter(x=>x.date>=nowStart).map(x=>({
 id:x.id,date:x.date,leader:x.leader,party:"BJP",url:x.url||"",publisher:x.publisher||"Publisher",title:x.title||"Public source",
 summary:x.summary||"",issue:normIssue(x.primaryIssue),secondary:(x.secondaryIssues||[]).map(normIssue).filter(Boolean),
 district:normDistrict(x.district),kind:x.type||"Press reference",originalPost:false
})).concat(op.filter(x=>x.date>=nowStart).flatMap(x=>(x.leaders||[]).filter(n=>opposition.includes(n)).map(leader=>({
 id:x.id,date:x.date,leader,party:"Opposition",url:x.url||"",publisher:x.publisher||"Publisher",title:x.title||"Public source",
 summary:x.summary||"",issue:(x.categories||[]).map(normIssue).find(Boolean)||null,
 secondary:(x.categories||[]).map(normIssue).filter(Boolean).slice(1),
 district:normDistrict(x.district),kind:"Opposition archive / press reference",originalPost:false
}))));
function postRows(){return postCorpus.map(p=>({
 id:p.id||canonical(p.url),date:p.date||"",leader:p.leader||"",party:p.party||((bjp.includes(p.leader))?"BJP":"Opposition"),
 url:p.url,publisher:p.publisherName||"Publisher-backed original URL",title:p.title||"Original platform post",
 summary:"Original "+(p.platform||"social")+" permalink recovered via publisher. Content/author not authenticated using platform API; issue label requires editorial review.",
 issue:normIssue(p.primaryIssue||p.issue),secondary:(p.secondaryIssues||[]).map(normIssue).filter(Boolean),
 district:normDistrict((p.districts||[])[0]),kind:"Original social permalink · publisher-backed",originalPost:true,
 publisherUrl:p.publisherUrl||"",status:p.postVerification||"publisher_corroborated_link_not_api_verified",platform:p.platform||"X"
 }));}
const allRows=()=>sourceRows.concat(postRows());
const inPeriod=x=>x.date>=nowStart&&(flow.period==="all"||x.date<=historicalEnd);
const hasLeaderChoice=()=>flow.bjp!=="all"||flow.opp!=="all";
function rowsMatch(){
 return allRows().filter(r=>inPeriod(r)
 &&(!hasLeaderChoice()||(flow.bjp!=="all"&&r.party==="BJP"&&r.leader===flow.bjp)||(flow.opp!=="all"&&r.party==="Opposition"&&r.leader===flow.opp))
 &&(flow.issue==="all"||r.issue===flow.issue||r.secondary.includes(flow.issue))
 &&(flow.district==="all"||r.district===flow.district));
}
const yFor=(i,n,h)=>78+(i+.5)*(h-118)/Math.max(n,1);
const curve=(x1,y1,x2,y2)=>"M"+x1+","+y1+" C"+(x1+(x2-x1)*.47)+","+y1+" "+(x2-(x2-x1)*.47)+","+y2+" "+x2+","+y2;
const node=(x,y,w,label,qty,kind,value,selected,color)=>'<g class="v13-node-group'+(selected?' selected':'')+'" data-v13-kind="'+kind+'" data-v13-value="'+esc(value)+'" tabindex="0" role="button" aria-label="Select '+esc(label)+'"><rect class="v12-node" x="'+x+'" y="'+(y-16)+'" width="'+w+'" height="32" rx="9" style="'+(color?'stroke:'+esc(color)+';':'')+(selected?'stroke-width:2.6;fill:#28453f;':'')+'"></rect><text x="'+(x+11)+'" y="'+y+'">'+esc(label.length>26?label.slice(0,25)+"…":label)+'</text><text class="v12-node-count" x="'+(x+w-10)+'" y="'+y+'" text-anchor="end">'+qty+'</text></g>';
function updateDropdown(){
 const opts=(items,all)=>'<option value="all">'+esc(all)+'</option>'+items.map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join("");
 if(byId("v13Bjp")){byId("v13Bjp").innerHTML=opts(bjp,"All BJP leaders");byId("v13Bjp").value=flow.bjp;}
 if(byId("v13Opp")){byId("v13Opp").innerHTML=opts(opposition,"All opposition leaders");byId("v13Opp").value=flow.opp;}
 if(byId("v12FlowIssue")){byId("v12FlowIssue").innerHTML=opts(issueNames,"All ten issues");byId("v12FlowIssue").value=flow.issue;}
 const districts=[...new Set(allRows().map(r=>r.district).filter(x=>x!=="Region not assigned"))].sort();
 if(byId("v13District")){byId("v13District").innerHTML=opts(districts,"All districts / regions");byId("v13District").value=flow.district;}
 if(byId("v13Period"))byId("v13Period").value=flow.period;
}
function renderFlow(){
 const svg=byId("v12FlowSvg");if(!svg)return;
 const rows=rowsMatch();
 const rawDistCount=new Map();
 const bjpCount=new Map(),oppCount=new Map(),issueCount=new Map();
 const edgeB=new Map(),edgeO=new Map(),edgeR=new Map();
 for(const r of rows){
  const dc=r.district,issue=r.issue;
  rawDistCount.set(dc,(rawDistCount.get(dc)||0)+1);
  if(r.party==="BJP")bjpCount.set(r.leader,(bjpCount.get(r.leader)||0)+1);
  else oppCount.set(r.leader,(oppCount.get(r.leader)||0)+1);
  if(issue){issueCount.set(issue,(issueCount.get(issue)||0)+1);
   const k=r.leader+"|"+issue,m=r.party==="BJP"?edgeB:edgeO;m.set(k,(m.get(k)||0)+1);
   const kd=issue+"|"+dc;edgeR.set(kd,(edgeR.get(kd)||0)+1);
  }
 }
 let regionList=[...rawDistCount].sort((a,b)=>b[1]-a[1]).map(x=>x[0]).slice(0,10);
 if(flow.district!=="all"&&!regionList.includes(flow.district))regionList.push(flow.district);
 if(!regionList.length)regionList=["No matching district"];
 const w=1580,h=Math.max(735,130+Math.max(bjp.length,opposition.length,issueNames.length,regionList.length)*56);
 svg.setAttribute("viewBox","0 0 "+w+" "+h);
 const pB=new Map(bjp.map((n,i)=>[n,yFor(i,bjp.length,h)]));
 const pO=new Map(opposition.map((n,i)=>[n,yFor(i,opposition.length,h)]));
 const pI=new Map(issueNames.map((n,i)=>[n,yFor(i,issueNames.length,h)]));
 const pR=new Map(regionList.map((n,i)=>[n,yFor(i,regionList.length,h)]));
 const paths=[];
 function addEdges(index,from,to,x1,x2,selectedClass){
  const edges=[...index].map(([key,n])=>{const at=key.indexOf("|");return {a:key.slice(0,at),b:key.slice(at+1),n};}).sort((a,b)=>b.n-a.n);
  const animated=new Set(edges.slice(0,4).map(x=>x.a+"|"+x.b));
  for(const e of edges){if(!from.has(e.a)||!to.has(e.b))continue;
   const t=topicColor(e.b)||"#78bec9",issue=selectedClass==="region"?e.a:e.b;
   const live=animated.has(e.a+"|"+e.b);
   paths.push('<path class="v12-flow-line v13-edge '+(live?'live':'')+' '+selectedClass+'" d="'+curve(x1,from.get(e.a),x2,to.get(e.b))+'" stroke="'+esc(topicColor(issue))+'" stroke-width="'+Math.min(3.7,1.05+Math.sqrt(e.n)*.33)+'"><title>'+esc(e.a+" → "+e.b+" · "+e.n+" linked references")+'</title></path>');
  }
 }
 addEdges(edgeB,pB,pI,266,876,"bjp-edge");
 addEdges(edgeO,pO,pI,601,876,"opp-edge");
 addEdges(edgeR,pI,pR,1100,1266,"region");
 const title='<text class="v12-header-label" x="28" y="29">01 / BJP LEADERS</text><text class="v12-header-label" x="341" y="29">02 / OPPOSITION</text><text class="v12-header-label" x="882" y="29">03 / ISSUES</text><text class="v12-header-label" x="1272" y="29">04 / DISTRICTS</text>';
 const left=bjp.map(n=>node(26,pB.get(n),241,n,bjpCount.get(n)||0,"bjp",n,flow.bjp===n,"#8bbcae")).join("");
 const other=opposition.map(n=>node(330,pO.get(n),271,n,oppCount.get(n)||0,"opp",n,flow.opp===n,"#d9b780")).join("");
 const issue=issueNames.map(n=>node(875,pI.get(n),225,n,issueCount.get(n)||0,"issue",n,flow.issue===n,topicColor(n))).join("");
 const district=regionList.map(n=>node(1265,pR.get(n),290,n,rawDistCount.get(n)||0,"district",n,flow.district===n,"#80a8b5")).join("");
 svg.innerHTML=title+paths.join("")+left+other+issue+district;
 const sources=new Set(rows.map(x=>x.url).filter(Boolean));
 const kpis=[[sources.size,"distinct evidence URLs"],[new Set(rows.filter(x=>x.party==="BJP").map(x=>x.leader)).size,"BJP leaders in selection"],[new Set(rows.filter(x=>x.party==="Opposition").map(x=>x.leader)).size,"opposition leaders in selection"],[rows.filter(r=>r.originalPost).length,"publisher-backed post links"]];
 if(byId("v12FlowKpis"))byId("v12FlowKpis").innerHTML=kpis.map(([n,txt])=>'<div class="v12-flow-kpi"><b>'+n+'</b><span>'+esc(txt)+'</span></div>').join("");
 if(byId("v12FlowScope"))byId("v12FlowScope").textContent=rows.length+" leader-source references · both groups linked to shared issues and districts · not comparable voting statistics";
 if(byId("v12FlowPause"))byId("v12FlowPause").textContent=flow.paused?"▶ Resume motion":"❚❚ Pause motion";
 const panel=byId("v12FlowPanel");if(panel)panel.dataset.motion=flow.paused?"paused":"active";
 renderEvidence(rows);
}
function renderEvidence(rows){
 const target=byId("v13Evidence");if(!target)return;
 const chosen=[flow.bjp!=="all"?flow.bjp:null,flow.opp!=="all"?flow.opp:null,flow.issue!=="all"?flow.issue:null,flow.district!=="all"?flow.district:null].filter(Boolean);
 const str=chosen.length?chosen.join("  /  "):"All leaders, issues and regions";
 const list=rows.slice().sort((a,b)=>Number(b.originalPost)-Number(a.originalPost)||String(b.date).localeCompare(String(a.date)));
 const show=list.slice(0,flow.limit);
 const card=r=>{
  const link=safeUrl(r.url),back=safeUrl(r.publisherUrl),meta=(r.originalPost?'Original X/Meta URL · publisher-backed':'Newspaper / public-source report');
  const tags=[r.issue].concat(r.secondary).filter(Boolean);
  return '<article class="v13-evidence-card"><small>'+esc(r.date||"Date not established")+' · '+esc(r.party)+' · '+esc(r.leader)+' · '+esc(meta)+'</small><strong>'+esc(r.title)+'</strong><div class="v13-pillrow">'+tags.map(t=>'<span class="v13-chip" style="border-color:'+esc(topicColor(t))+'">'+esc(t)+'</span>').join("")+'<span class="v13-chip">'+esc(r.district)+'</span></div>'+(r.summary?'<p>'+esc(r.summary)+'</p>':'')+'<div class="v13-evidence-links">'+(link?'<a href="'+esc(link)+'" target="_blank" rel="noopener noreferrer">'+(r.originalPost?'Open original post':'Open source article')+' ↗</a>':'')+(back?'<a href="'+esc(back)+'" target="_blank" rel="noopener noreferrer">Corroborating publisher ↗</a>':'')+'</div></article>';
 };
 const intro='<div class="v13-evidence-bar"><div><strong>INTERCONNECTED INTELLIGENCE / '+esc(str)+'</strong><small>'+list.length+' leader-source references, '+list.filter(x=>x.originalPost).length+' publisher-backed original post links. Filtering includes secondary issue tags.</small></div><button type="button" id="v13EvidenceClose">'+(flow.open?"Hide results":"Show results")+'</button></div>';
 target.innerHTML=intro+(flow.open?'<div class="v13-evidence-grid">'+(show.length?show.map(card).join(""):'<div class="v12-blank">No indexed evidence for this selection. This does not mean no statements or posts were made.</div>')+'</div>'+(list.length>show.length?'<button class="v13-more" id="v13EvidenceMore" type="button">Show '+Math.min(12,list.length-show.length)+' more · '+(list.length-show.length)+' remaining</button>':''):'');
 target.querySelector("#v13EvidenceClose")?.addEventListener("click",()=>{flow.open=!flow.open;renderEvidence(rows);});
 target.querySelector("#v13EvidenceMore")?.addEventListener("click",()=>{flow.limit+=12;renderEvidence(rows);});
}
function selectThing(kind,value){
 const k=kind==="opposition"?"opp":kind;
 if(!(k in flow))return;
 flow[k]=flow[k]===value?"all":value;
 flow.open=true;flow.limit=12;updateDropdown();renderFlow();
}
function initFlow(){
 const panel=byId("v12FlowPanel"),svg=byId("v12FlowSvg");
 if(!panel||!svg)return;
 const existing=panel.querySelector(".v12-flow-filters");
 if(existing){
  for(const id of ["v12FlowParty","v12FlowLeader"]){const el=byId(id);if(el&&el.closest("label"))el.closest("label").style.display="none";}
  const wrap=document.createElement("div");wrap.className="v13-four-filters";
  wrap.innerHTML='<label>BJP / GOVERNMENT<select id="v13Bjp"></select></label><label>OPPOSITION<select id="v13Opp"></select></label><label>DISTRICT / REGION<select id="v13District"></select></label><label>TIME WINDOW<select id="v13Period"><option value="all">05 Aug 2026 onward</option><option value="historic">05 Aug – 05 Nov 2026</option></select></label><button type="button" id="v13Reset">Clear four-way selection</button>';
  existing.insertAdjacentElement("afterend",wrap);
 }
 const board=panel.querySelector(".v12-flow-board")||svg.parentElement;
 const evidence=document.createElement("section");evidence.id="v13Evidence";evidence.className="v13-evidence";
 board.insertAdjacentElement("afterend",evidence);
 updateDropdown();
 for(const [id,key] of [["v13Bjp","bjp"],["v13Opp","opp"],["v12FlowIssue","issue"],["v13District","district"],["v13Period","period"]]){
  byId(id)?.addEventListener("change",e=>{flow[key]=e.target.value;flow.open=true;flow.limit=12;renderFlow();});
 }
 byId("v13Reset")?.addEventListener("click",()=>{flow={...flow,bjp:"all",opp:"all",issue:"all",district:"all",period:"all",open:false,limit:12};updateDropdown();renderFlow();});
 byId("v12FlowPause")?.addEventListener("click",()=>{flow.paused=!flow.paused;renderFlow();});
 const activate=target=>{const n=target?.closest?.("[data-v13-kind]");if(!n)return;selectThing(n.getAttribute("data-v13-kind"),n.getAttribute("data-v13-value"));};
 svg.addEventListener("click",e=>activate(e.target));
 svg.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();activate(e.target);}});
 if("IntersectionObserver" in window){const io=new IntersectionObserver(es=>{for(const e of es)panel.dataset.visible=e.isIntersecting?"true":"false";},{threshold:.02});io.observe(panel);}
 document.addEventListener("visibilitychange",()=>panel.dataset.visible=document.hidden?"false":"true");
 byId("v12FlowJump")?.addEventListener("click",()=>{document.querySelector('[data-nav="command"]')?.click();panel.scrollIntoView({behavior:"smooth",block:"start"});});
 renderFlow();
}
function postCard(p){
 const issue=normIssue(p.primaryIssue||p.issue)||"Unclassified",source=safeUrl(p.url),publisher=safeUrl(p.publisherUrl);
 const status=p.apiVerified===true?"API authenticated":"Publisher-linked; not API authenticated";
 const warning=p.reviewStatus==="needs_human_review"||p.reviewStatus==="publisher_page_unavailable_recheck"?" · issue/author review pending":"";
 return '<article class="v12-social-card"><small>'+esc(p.date||"Date unverified")+' · '+esc(p.leader||"Attribution pending")+' · '+esc(p.party||"")+' · '+esc(p.platform||"X")+'</small><strong>'+esc(p.title||"Original post permalink")+'</strong><small>'+esc(issue)+' · '+esc(status)+esc(warning)+'</small><div class="v12-social-links">'+(source?'<a target="_blank" rel="noopener noreferrer" href="'+esc(source)+'">Open original post ↗</a>':'')+(publisher?'<a target="_blank" rel="noopener noreferrer" href="'+esc(publisher)+'">Publisher reference ↗</a>':'')+'</div></article>';
}
function renderSocial(){
 if(!byId("v12SocialLedger"))return;
 const filtered=postCorpus.filter(p=>(socialIssue==="all"||normIssue(p.primaryIssue||p.issue)===socialIssue||socialIssue==="Unclassified"&&(normIssue(p.primaryIssue||p.issue)==null)||(p.secondaryIssues||[]).some(x=>x===socialIssue))
 &&(socialLeader==="all"||p.leader===socialLeader)
 &&(!socialQuery||[p.title,p.leader,p.date,p.primaryIssue,p.issue,p.publisherName,p.url].join(" ").toLowerCase().includes(socialQuery))).sort((a,b)=>String(b.date).localeCompare(String(a.date)));
 byId("v12SocialLedger").innerHTML=filtered.length?filtered.map(postCard).join(""):'<div class="v12-blank">No source-backed individual posts match these filters. A zero here does not mean no posts were published.</div>';
 byId("v12SocialCount").textContent=filtered.length+" original post permalinks · "+activeSource;
 const stats=byId("v12SocialStats");
 if(stats){const x=postCorpus.filter(x=>x.platform==="X").length,fb=postCorpus.filter(x=>x.platform==="Facebook").length,ig=postCorpus.filter(x=>x.platform==="Instagram").length;
  stats.innerHTML='<div><b>'+x+'</b><span>X original permalinks (publisher-backed)</span></div><div><b>'+fb+'</b><span>Facebook original links recovered</span></div><div><b>'+ig+'</b><span>Instagram original links recovered</span></div>';}
 const cm=byId("v12CmDiscoveryPreview");
 if(cm){const items=postCorpus.filter(p=>p.leader==="Vishnu Deo Sai");cm.innerHTML='<div class="v12-social-kpis"><div><b>'+items.length+'</b><span>CM X permalink references</span></div><div><b>'+((discovery.accounts||[]).filter(a=>a.person==="Vishnu Deo Sai"&&(a.platform==="Facebook"||a.platform==="Instagram")).length)+'</b><span>CM Meta profile references</span></div><div><b>0</b><span>Authenticated platform API posts in source ledger</span></div></div><p class="v12-hint">Individual publisher-linked URLs are not equivalent to authenticated post text. Issue assignments await manual review.</p><button type="button" class="v12-btn" id="v12OpenSocial">Open indexed social archive ↗</button>';byId("v12OpenSocial")?.addEventListener("click",()=>document.querySelector('[data-nav="v12-links"]')?.click());}
 const recovered=byId("v12CmSocialRecoveredList");
 if(recovered){recovered.innerHTML='<h3 style="margin:12px 0;font-size:14px;color:#d4eee9">CM public post links</h3>'+postCorpus.filter(p=>p.leader==="Vishnu Deo Sai").slice().sort((a,b)=>String(b.date).localeCompare(String(a.date))).slice(0,8).map(postCard).join("")+'<button class="v12-btn" id="v13CmAll" type="button">View entire original-post archive ↗</button>';byId("v13CmAll")?.addEventListener("click",()=>document.querySelector('[data-nav="v12-links"]')?.click());}
 const accounts=byId("v12SocialAccounts");
 if(accounts)accounts.innerHTML=(discovery.accounts||[]).map(a=>'<div class="v12-social-account"><b>'+esc(a.person)+' · '+esc(a.platform)+'</b><small>'+esc(a.verification||"Identity review pending")+'</small><a href="'+esc(safeUrl(a.url))+'" target="_blank" rel="noopener noreferrer">Open account ↗</a></div>').join("");
 for(const b of document.querySelectorAll("[data-v12-social-banner]")){b.innerHTML='<span class="v12-cap">SOURCE-LINKED SOCIAL INTELLIGENCE</span><h3>'+postCorpus.length+' indexed original post URLs across both groups</h3><p class="v12-hint">Publisher corroboration is shown separately from platform API authentication; Facebook/Instagram links are not invented.</p><button type="button" class="v12-btn" data-open-social-links>View post ledger ↗</button>';b.querySelector("[data-open-social-links]")?.addEventListener("click",()=>document.querySelector('[data-nav="v12-links"]')?.click());}
 const s=byId("v12SocialIssue");if(s){s.innerHTML='<option value="all">All issue tags</option><option value="Unclassified">Unclassified</option>'+issueNames.map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join("");s.value=socialIssue;}
 const leaders=byId("v13SocialLeader");if(leaders){leaders.innerHTML='<option value="all">All 20 leaders</option>'+bjp.concat(opposition).map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join("");leaders.value=socialLeader;}
}
function publicSearchCards(){
 const dst=byId("v12PublicSocialSearch");if(!dst)return;
 const candidates=(discovery.accounts||[]);
 const people=bjp.map(name=>({name,party:"BJP / Government"})).concat(opposition.map(name=>({name,party:"Opposition"})));
 dst.innerHTML=people.map(x=>{
 const prof=candidates.find(p=>p.person===x.name&&p.platform==="X"&&/^https:\/\/x\.com\/[A-Za-z0-9_]+\/?$/.test(p.url||""));
 const handle=prof?prof.url.split("/").filter(Boolean).at(-1):null;
 const find=handle?'from:'+handle+' since:2026-08-05':'"'+x.name+'" since:2026-08-05';
 const xurl="https://x.com/search?q="+encodeURIComponent(find)+"&src=typed_query";
 const fb="https://www.google.com/search?q="+encodeURIComponent('site:facebook.com "'+x.name+'" 2026 post');
 const ig="https://www.google.com/search?q="+encodeURIComponent('site:instagram.com "'+x.name+'" 2026');
 return '<div class="v12-social-searchrow"><b>'+esc(x.name)+'</b><small>'+esc(x.party)+' · '+(handle?"Publisher-referenced profile; account review required":"Name search; handle not established")+'</small><a href="'+esc(xurl)+'" target="_blank" rel="noopener noreferrer">Search X ↗</a><a href="'+esc(fb)+'" target="_blank" rel="noopener noreferrer">Facebook post search ↗</a><a href="'+esc(ig)+'" target="_blank" rel="noopener noreferrer">Instagram post search ↗</a></div>';
 }).join("");
}
async function loadUnifiedPosts(){
 const sources=[
  "https://raw.githubusercontent.com/Praddyspinoza/opposition-monitoring-system-/main/preview/v12/social_intelligence_posts.json",
  "./social_intelligence_posts.json"
 ];
 for(const location of sources){
  try{
   const response=await fetch(location,{cache:"no-store"});
   if(!response.ok)continue;
   const data=await response.json();
   if(!Array.isArray(data.posts)||!data.posts.length)continue;
   const merged=new Map();
   for(const p of [...postCorpus,...data.posts]){if(p?.url&&safeUrl(p.url))merged.set(canonical(p.url),p);}
   postCorpus=[...merged.values()];
   activeSource=(location.startsWith("https://")?"live public GitHub source ledger":"GitHub Pages source ledger")+(data.asOf?" · indexed "+data.asOf.slice(0,10):"");
   updateDropdown();renderFlow();renderSocial();
   return;
  }catch(_){/* Continue to another public permitted source; retain embedded fallback. */}
 }
}
function initSocial(){
 if(!byId("v12SocialLedger"))return;
 const controls=byId("v12SocialIssue")?.closest(".v12-social-controls")||byId("v12SocialIssue")?.parentElement;
 if(controls){const label=document.createElement("label");label.className="v13-social-leader-label";label.textContent="LEADER ";
 const sel=document.createElement("select");sel.id="v13SocialLeader";label.appendChild(sel);controls.insertBefore(label,controls.firstChild);}
 byId("v12SocialIssue")?.addEventListener("change",e=>{socialIssue=e.target.value;renderSocial();});
 byId("v13SocialLeader")?.addEventListener("change",e=>{socialLeader=e.target.value;renderSocial();});
 byId("v12SocialSearch")?.addEventListener("input",e=>{socialQuery=String(e.target.value||"").trim().toLowerCase();renderSocial();});
 publicSearchCards();renderSocial();loadUnifiedPosts();
}
initFlow();initSocial();
})();