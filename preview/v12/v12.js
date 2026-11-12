(function v12Init(){
"use strict";
const $=id=>document.getElementById(id);
const TAX=JSON.parse($("v12Data").textContent);
const ISSUES=TAX.issueTaxonomy;
const ISSUE_SET=new Set(ISSUES.map(x=>x.id));
const OPP_NAMES=JSON.parse($("peopleData").textContent);
const B=TAX.bjpLeaders;
const OPP=JSON.parse($("archiveData").textContent);
const OUT=()=>({start:($("v12From")&&$("v12From").value)||"2026-08-05",end:($("v12To")&&$("v12To").value)||"2026-11-05"});
const defaultPeriod={start:"2026-08-05",end:"2026-11-05"};
const topicById=new Map(ISSUES.map(x=>[x.id.toLowerCase(),x]));
const statusDom={};
let bjpLeader=B[0].n;
let group="all";
let bjpStatementOnly=true;
let bjpTopic="all";
let cmIssue="all";
let cmQuery="";
let cmSourceKind="all";
let localPosts=[];
try{const items=JSON.parse(localStorage.getItem("cg_v12_local_cm_posts")||"[]");if(Array.isArray(items))localPosts=items;}catch(_){}
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const u=s=>{try{const a=new URL(s);return a.protocol==="https:"?a.href:"";}catch(_){return"";}};
const named=(s)=>String(s||"").trim().toLowerCase();
const inTime=(date)=>{const range=OUT();return String(date||"")>=range.start&&String(date||"")<=range.end;};
const normalizeIssue=(raw)=>{const k=named(raw);if(k==="tribal issues"||k==="tribal issues / adivasi"||k==="tribal rights")return"Tribal Issues";if(k==="religion / hinduism"||k==="religion")return"Religion / Hinduism";return topicById.get(k)?.id||null;};
const firstIssue=(rec)=>{
  const direct=normalizeIssue(rec.primaryIssue);if(direct)return direct;
  const cs=Array.isArray(rec.categories)?rec.categories:[rec.category||""];
  for(const v of cs){const t=normalizeIssue(v);if(t)return t;}
  return null;
};
const makeBjpRow=(r)=>({...r,issue:firstIssue(r),leader:r.leader,cohort:"BJP",statement:!!r.statement,kind:r.type||"Source report"});
const makeOppRow=(r,name)=>({...r,issue:firstIssue(r),leader:name,cohort:"Opposition",statement:null,kind:"Historical source reference"});
const rowsBjp=(name)=>TAX.bjpRecords.filter(r=>(!name||r.leader===name)&&inTime(r.date)).map(makeBjpRow);
const rowsOpp=(name)=>OPP.filter(r=>(!name||(Array.isArray(r.leaders)?r.leaders:[]).includes(name))&&inTime(r.date)).flatMap(r=>name?[makeOppRow(r,name)]:((r.leaders||[]).filter(l=>OPP_NAMES.includes(l)).map(l=>makeOppRow(r,l))));
const leaderRows=(name,statements=false)=>{
  if(B.some(b=>b.n===name))return rowsBjp(name).filter(r=>!statements||r.statement);
  return rowsOpp(name);
};
const counts=(rows)=>{const map=Object.fromEntries(ISSUES.map(x=>[x.id,0]));for(const r of rows){if(r.issue&&Object.hasOwn(map,r.issue))map[r.issue]++;}return map;};
const totalCount=cs=>Object.values(cs).reduce((a,b)=>a+b,0);
const fullPie=(cs,summary,sub)=>{
  const total=totalCount(cs);
  let cursor=0,stops=[];
  for(const topic of ISSUES){
    const val=cs[topic.id]||0;
    if(!val||!total)continue;
    const from=cursor/total*100;cursor+=val;const to=cursor/total*100;
    stops.push(topic.color+" "+from.toFixed(4)+"% "+to.toFixed(4)+"%");
  }
  const gradient=stops.length?"conic-gradient("+stops.join(",")+")":"conic-gradient(#43536a 0 100%)";
  const legend=ISSUES.filter(topic=>cs[topic.id]>0).sort((a,b)=>cs[b.id]-cs[a.id]).map(topic=>'<div class="v12-legend-row"><i style="background:'+topic.color+'"></i><span>'+esc(topic.ab)+'</span><strong>'+cs[topic.id]+' · '+Math.round(100*cs[topic.id]/total)+'%</strong></div>').join("");
  const zero='<div class="v12-legend-row">No issue-coded records in this selection.</div>';
  const label=ISSUES.filter(t=>cs[t.id]>0).map(t=>t.ab+":"+cs[t.id]).join(", ");
  return '<div class="v12-pie-layout"><div class="v12-donut" role="img" aria-label="'+esc(summary+": "+(label||"no data"))+'" style="background:'+gradient+'"><div class="v12-donut-inner"><b>'+total+'</b><small>'+esc(sub)+'</small></div></div><div class="v12-legend">'+(legend||zero)+'</div></div>';
};
const miniPie=(cs)=>{
  const total=totalCount(cs);let cursor=0,stops=[];
  for(const t of ISSUES){const n=cs[t.id]||0;if(!n||!total)continue;const a=cursor/total*100;cursor+=n;const b=cursor/total*100;stops.push(t.color+" "+a.toFixed(3)+"% "+b.toFixed(3)+"%");}
  const bg=stops.length?"conic-gradient("+stops.join(",")+")":"conic-gradient(#364758 0 100%)";
  return '<div class="v12-mini-donut'+(total?"":" empty")+'" role="img" aria-label="'+total+' issue-coded sources" style="background:'+bg+'"><span>'+(total||"—")+'</span></div>';
};
const evidence=(row,short=false)=>{
  const issue=row.issue||"Not issue-coded";const t=ISSUES.find(x=>x.id===issue);
  const link=u(row.url);
  return '<article class="v12-evidence"><div class="v12-evidence-meta">'+esc(row.date||"Undated")+' · '+esc(row.publisher||row.platform||"Source")+' · <span class="v12-type">'+esc(row.kind||row.type||"Record")+'</span></div><b>'+esc(row.title||"Source record")+'</b>'+(short?"":'<p>'+esc(row.summary||"")+'</p>')+'<div class="v12-chiprow"><span class="v12-chip" style="border-color:'+(t?.color||"#52677d")+'">'+esc(issue)+'</span>'+(row.secondaryIssues||[]).filter(x=>ISSUE_SET.has(x)).map(x=>'<span class="v12-chip">'+esc(x)+'</span>').join("")+'</div>'+(link?'<a class="v12-link" target="_blank" rel="noopener noreferrer" href="'+esc(link)+'">Open original source ↗</a>':'<span class="v12-hint">Source URL not available</span>')+'</article>';
};
function btnNav(target){document.querySelector('[data-nav="'+target+'"]')?.click();}
function personCards(items,isBjp){
  return items.map((person,i)=>{
    const name=isBjp?person.n:person;
    const cs=counts(leaderRows(name,isBjp));
    const total=totalCount(cs);
    const title=isBjp?person.r:"Opposition · existing V11 dossier";
    return '<button type="button" class="v12-person-card'+(isBjp&&bjpLeader===name?" selected":"")+'" data-v12-person="'+esc(name)+'" data-v12-party="'+(isBjp?"bjp":"opp")+'">'+miniPie(cs)+'<span class="v12-topid">'+String(i+1).padStart(2,"0")+'</span><b>'+esc(name)+'</b><small>'+esc(title)+'</small><small style="margin-top:5px;color:#b9d7d4">'+total+' issue-coded '+(isBjp?"attributed statement"+(total===1?"":"s"):"archive reference"+(total===1?"":"s"))+'</small></button>';
  }).join("");
}
function renderBjp(){
  const parent=$("v12BjpGallery");if(!parent)return;
  parent.innerHTML=personCards(B,true);
  const leader=B.find(x=>x.n===bjpLeader)||B[0];
  const rows=rowsBjp(bjpLeader);
  const chosen=rows.filter(r=>!bjpStatementOnly||r.statement);
  const sorted=chosen.slice().sort((a,b)=>String(b.date).localeCompare(String(a.date)));
  const filtered=bjpTopic==="all"?sorted:sorted.filter(r=>r.issue===bjpTopic||(r.secondaryIssues||[]).includes(bjpTopic));
  const allStatementCount=rows.filter(r=>r.statement&&r.issue).length;
  const pieces=ISSUES.map(x=>'<option value="'+esc(x.id)+'"'+(bjpTopic===x.id?" selected":"")+'>'+esc(x.id)+'</option>').join("");
  $("v12BjpDetails").innerHTML='<div class="v12-dossier"><div><div class="v12-profile"><div class="v12-label">BJP / GOVERNMENT · LEADER '+String(B.indexOf(leader)+1).padStart(2,"0")+'</div><h2>'+esc(leader.n)+'</h2><p><b>'+esc(leader.r)+'</b></p><p>'+esc(leader.p)+'</p><p>Geographic association: '+esc(leader.district||"Not assigned")+' (not evidence of project delivery)</p>'+(leader.x?'<p><a class="v12-link" href="'+esc(u(leader.x))+'" target="_blank" rel="noopener noreferrer">Official X account reference ↗</a></p>':'')+'</div><div class="v12-pills"><span class="v12-pill">'+rows.length+' source-linked reports</span><span class="v12-pill">'+allStatementCount+' tagged attributed statements</span></div><div class="v12-controls"><label>Pie counting mode<select id="v12BjpMode"><option value="statements"'+(bjpStatementOnly?" selected":"")+'>Attributed statements only</option><option value="all"'+(!bjpStatementOnly?" selected":"")+'>All issue-coded records</option></select></label></div>'+fullPie(counts(chosen),"Issue distribution for "+leader.n,bjpStatementOnly?"statements":"records")+'<div class="v12-footnote">Percentages represent the distribution within this <b>incomplete research sample</b> for 05 Aug–05 Nov 2026. One primary issue is counted per dated item. An event without an attributed quotation is excluded when statement-only mode is on. No claim of comprehensive speeches or social posts.</div></div><div><div class="v12-row"><h3 style="margin:0;color:#f0f6f9">Source-linked intelligence</h3><span class="v12-pill">'+filtered.length+' matching</span></div><div class="v12-controls" style="padding:10px;margin:12px 0"><label>Issue<select id="v12BjpIssue"><option value="all">All issues</option>'+pieces+'</select></label></div><div class="v12-evidence-list">'+(filtered.length?filtered.map(r=>evidence(r)).join(""):'<div class="v12-blank">No dated source matching this issue and statement mode. Coverage is incomplete.</div>')+'</div></div></div>';
  $("v12BjpMode")?.addEventListener("change",e=>{bjpStatementOnly=e.target.value==="statements";renderBjp();});
  $("v12BjpIssue")?.addEventListener("change",e=>{bjpTopic=e.target.value;renderBjp();});
}
function renderOppPies(){
  const g=$("v12OppGallery");if(g)g.innerHTML=personCards(OPP_NAMES,false);
  document.querySelectorAll("article.leader-detail[data-leader-detail]").forEach(panel=>{
    const name=panel.getAttribute("data-leader-detail");
    let dest=panel.querySelector(".v12-legacychart");
    if(!dest){dest=document.createElement("section");dest.className="v12-legacychart";const top=panel.querySelector(".leader-top");if(top)top.insertAdjacentElement("afterend",dest);else panel.prepend(dest);}
    const cs=counts(rowsOpp(name));
    dest.innerHTML='<h4>Issue-share pie · '+esc(name)+'</h4><p class="v12-hint">Original V11 archive topic tags, 05 August–05 November 2026. These are <b>source-linked reports</b>, not an exhaustive count of the leader’s spoken statements. The five newly added issue classes await historical retagging.</p>'+fullPie(cs,"V11 source-linked issue tags for "+name,"reports");
  });
}
function renderTiles(target){
  const bRows=rowsBjp().filter(r=>r.statement);
  const oRows=rowsOpp();
  const bCounts=counts(bRows);
  const oCounts=counts(oRows);
  $(target).innerHTML=ISSUES.map(t=>'<article class="v12-issue-tile"><i style="background:'+t.color+'"></i><strong>'+esc(t.id)+'</strong><small>'+esc(t.description)+'</small><div class="v12-row" style="margin-top:12px"><span><b>'+bCounts[t.id]+'</b><small>BJP quoted</small></span><span><b>'+oCounts[t.id]+'</b><small>Opp. references</small></span></div></article>').join("");
}
function renderMatrix(){
  const tbody=$("v12MatrixBody");if(!tbody)return;
  const figures=[
    ...B.map(x=>({name:x.n,cohort:"BJP",c:counts(rowsBjp(x.n).filter(r=>r.statement))})),
    ...OPP_NAMES.map(x=>({name:x,cohort:"Opposition",c:counts(rowsOpp(x))}))
  ].filter(x=>group==="all"||x.cohort===group);
  let max=1;for(const x of figures)for(const y of Object.values(x.c))max=Math.max(max,y);
  tbody.innerHTML=figures.map(person=>{
    const chartCount=totalCount(person.c);
    const cs=ISSUES.map(x=>{
      const n=person.c[x.id]||0;
      const alpha=n?Math.min(.72,Math.max(.17,n/max*.78)):0;
      return '<td title="'+esc(person.name+", "+x.id+": "+n+" indexed")+"'><span class=\"v12-cell"+(n?" has":"")+'" style="--v12-alpha:'+alpha.toFixed(3)+'">'+(n||"–")+'</span></td>';
    }).join("");
    return '<tr><th><button type="button" data-v12-person="'+esc(person.name)+'" data-v12-party="'+(person.cohort==="BJP"?"bjp":"opp")+'">'+esc(person.name)+'</button><div style="font-size:9px;color:#95aec2">'+person.cohort+'</div></th>'+cs+'<td><strong>'+chartCount+'</strong></td></tr>';
  }).join("");
  $("v12MatrixCount").textContent=figures.length+" leaders";
  renderTiles("v12IssueGrid");
  renderTiles("v12CommandTiles");
}
function renderCommand(){
  const b=TAX.bjpRecords.filter(r=>inTime(r.date));
  const o=OPP.filter(r=>inTime(r.date));
  const stats=[
    [B.length+OPP_NAMES.length,"leader dossiers"],
    [ISSUES.length,"issue dimensions"],
    [b.length,"BJP source-linked items"],
    [o.length,"V11 opposition records"],
  ];
  $("v12CommandStats").innerHTML=stats.map(([n,l])=>'<div class="v12-stat"><b>'+n+'</b><span>'+esc(l)+'</span></div>').join("");
  $("v12LatestEvidence").innerHTML=b.slice().sort((a,b)=>String(b.date).localeCompare(String(a.date))).slice(0,6).map(r=>evidence(makeBjpRow(r),true)).join("");
}
const POST_KEY="cg_v12_local_cm_posts";
function mergedCmPosts(){
  const api=(TAX.cmSocialApi?.posts||[]).map(x=>({...x,_source:"Published API feed",api_verified:x.api_verified===true}));
  return api.concat(localPosts.map(x=>({...x,_source:"Browser-local import, NOT API-verified",api_verified:false})));
}
function renderCm(){
  const cmRows=rowsBjp("Vishnu Deo Sai").sort((a,b)=>String(b.date).localeCompare(String(a.date)));
  const cmStatements=cmRows.filter(r=>r.statement&&r.issue);
  const cmShares=counts(cmStatements);
  $("v12CmPie").innerHTML=fullPie(cmShares,"CM reported attributed public statements","statements")+'<div class="v12-footnote">Chart counts reported, source-linked public statements. It does not measure all speeches, posts or completed project outcomes.</div>';
  const api=(TAX.cmSocialApi||{});
  const posts=mergedCmPosts();
  const verified=posts.filter(p=>p.api_verified===true);
  $("v12CmMetrics").innerHTML=[
    [cmRows.length,"indexed CM source records"],
    [cmStatements.length,"issue-coded attributed statements"],
    [verified.filter(p=>p.platform==="X").length,"API-verified X posts"],
    [verified.filter(p=>p.platform==="Facebook"||p.platform==="Instagram").length,"API-verified Meta posts"]
  ].map(([val,label])=>'<div class="v12-stat"><b>'+val+'</b><span>'+esc(label)+'</span></div>').join("");
  $("v12CmSocial").innerHTML=[
    ["X / Twitter",api.x?.handle||"@vishnudsai",api.x?.status||"No official account feed connected",api.x?.handle?"https://x.com/"+api.x.handle.replace(/^@/,""):""],
    ["Facebook","CM public Page",api.status?.facebook?.state==="connected"?"Connected via authorised Meta Page API · "+api.status.facebook.retrieved+" posts retrieved":"No approved Page token or authenticated API collection",""],
    ["Instagram","CM professional account",api.status?.instagram?.state==="connected"?"Connected via authorised Instagram Graph API · "+api.status.instagram.retrieved+" posts retrieved":"No authorised Meta Graph API connection",""]
  ].map(([title,handle,status,url])=>'<div class="v12-socialbox"><div class="v12-row"><h3>'+esc(title)+'</h3><span class="v12-account-status"+(status.startsWith("Connected")?" connected":"")+">"+(status.startsWith("Connected")?"API CONNECTED":"API PENDING")+"</span></div><p>'+esc(handle)+'</p><p>'+esc(status)+'</p>'+(url?'<a class="v12-link" href="'+esc(u(url))+'" target="_blank" rel="noopener noreferrer">Open account ↗</a>':'<span class="v12-hint">No authenticated official Page/profile URL assigned</span>')+'</div>').join("");
  const filtered=cmRows.filter(r=>(cmIssue==="all"||r.issue===cmIssue||(r.secondaryIssues||[]).includes(cmIssue))&&(cmSourceKind==="all"||cmSourceKind==="sources")&&(!cmQuery||(r.title+" "+r.summary+" "+r.publisher+" "+r.district).toLowerCase().includes(cmQuery)));
  $("v12CmResults").innerHTML=cmSourceKind==="posts"?"":filtered.length?filtered.map(r=>evidence(r)).join(""):'<div class="v12-blank">No matching CM source reports in this subset.</div>';
  let visiblePosts=posts.filter(p=>inTime(p.date)&&(cmIssue==="all"||p.issue===cmIssue)&&(!cmQuery||(String(p.text||"")+" "+String(p.handle||"")).toLowerCase().includes(cmQuery))).sort((a,b)=>b.date.localeCompare(a.date));
  const postHTML=visiblePosts.length?visiblePosts.map(p=>evidence({date:p.date,publisher:p.platform,kind:p._source,title:p.text||"Original post",summary:(p.handle||"")+" · "+(p.api_verified?"Authorised API source":"User-imported record, not independently verified"),url:p.url,issue:p.issue})).join(""):'<div class="v12-blank">No authenticated CM X / Facebook / Instagram posts have been collected for this date range. You may import an authorised JSON export below; local imports are not labelled API-verified.</div>';
  $("v12CmPosts").innerHTML=cmSourceKind==="sources"?"":postHTML;
  $("v12CmSourceCount").textContent=filtered.length+" linked press/official sources · "+visiblePosts.length+" platform post entries";
  const cIssues='<option value="all">All ten issues</option>'+ISSUES.map(t=>'<option value="'+esc(t.id)+'"'+(cmIssue===t.id?" selected":"")+'>'+esc(t.id)+'</option>').join("");
  $("v12CmFilters").innerHTML='<label>Issue<select id="v12CmIssue">'+cIssues+'</select></label><label>Evidence<select id="v12CmKind"><option value="all"'+(cmSourceKind==="all"?" selected":"")+'>All source types</option><option value="sources"'+(cmSourceKind==="sources"?" selected":"")+'>Press / official sources</option><option value="posts"'+(cmSourceKind==="posts"?" selected":"")+'>Original platform posts</option></select></label><label>Search<input id="v12CmQuery" type="search" placeholder="Scheme, district, quote…" value="'+esc(cmQuery)+'"></label><button id="v12CmClear" type="button">Reset filters</button>';
  $("v12CmIssue").addEventListener("change",e=>{cmIssue=e.target.value;renderCm()});
  $("v12CmKind").addEventListener("change",e=>{cmSourceKind=e.target.value;renderCm()});
  $("v12CmQuery").addEventListener("input",e=>{const at=e.target.selectionStart;cmQuery=e.target.value;renderCm();const box=$("v12CmQuery");box?.focus();if(at!==null)box?.setSelectionRange(at,at);});
  $("v12CmClear").addEventListener("click",()=>{cmIssue="all";cmQuery="";cmSourceKind="all";renderCm()});
  const status=$("v12CmImportCount");if(status)status.textContent=localPosts.length+" browser-local imported posts (unverified)";
}
function validPost(raw){
  if(!raw||typeof raw!=="object")return null;
  const platform=String(raw.platform||"").trim();
  if(!["X","Facebook","Instagram"].includes(platform))return null;
  const date=String(raw.date||raw.published_at||"").slice(0,10);
  if(date<defaultPeriod.start||date>defaultPeriod.end)return null;
  const source=u(raw.url);
  if(!source)return null;
  const host=new URL(source).hostname.replace(/^www\./,"");
  if(platform==="X"&&!["x.com","twitter.com"].includes(host))return null;
  if(platform==="Facebook"&&!["facebook.com","m.facebook.com","web.facebook.com"].includes(host))return null;
  if(platform==="Instagram"&&host!=="instagram.com")return null;
  const issue=normalizeIssue(raw.issue);
  if(!issue)return null;
  const handle=String(raw.handle||raw.account||"").slice(0,100);
  const text=String(raw.text||raw.caption||raw.title||"").slice(0,2500);
  return {date,platform,url:source,issue,handle,text};
}
function importPosts(txt){
  let raw;try{raw=JSON.parse(txt)}catch(e){$("v12CmImportMessage").textContent="Invalid JSON syntax.";return;}
  const arr=Array.isArray(raw)?raw:Array.isArray(raw.posts)?raw.posts:[raw];
  const accepted=arr.map(validPost).filter(Boolean);
  const by=new Map(localPosts.map(p=>[p.platform+"|"+p.url,p]));
  for(const p of accepted)by.set(p.platform+"|"+p.url,p);
  const before=localPosts.length;localPosts=[...by.values()].slice(0,2000);
  try{localStorage.setItem(POST_KEY,JSON.stringify(localPosts));}catch(_){}
  $("v12CmImportMessage").textContent="Accepted "+accepted.length+"/"+arr.length+" source-format entries. Saved locally only; no authenticated API verification. Total "+localPosts.length+".";
  $("v12CmImportCount").textContent=localPosts.length+" browser-local imported posts";
  renderCm();
}
function setupImport(){
  $("v12CmImportButton").addEventListener("click",()=>importPosts($("v12CmImportText").value));
  $("v12CmImportFile").addEventListener("change",e=>{const file=e.target.files[0];if(!file)return;if(file.size>2e6){$("v12CmImportMessage").textContent="Please use a JSON file smaller than 2 MB";return;}file.text().then(importPosts).catch(()=>$("v12CmImportMessage").textContent="Unable to read file.");});
  $("v12CmExport").addEventListener("click",()=>{
    const bytes=JSON.stringify({schema_version:1,source:"browser-local-user-import",posts:localPosts},null,2);
    const blob=new Blob([bytes],{type:"application/json"});
    const link=document.createElement("a");link.href=URL.createObjectURL(blob);link.download="cm_v12_imported_posts.json";link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1500);
  });
}
function addDistrictPanel(){
  const container=$("cgDistrictEvidence");if(!container)return;
  let brief=$("v12DistrictBrief");
  if(!brief){brief=document.createElement("div");brief.id="v12DistrictBrief";brief.className="v12-district-brief";container.insertAdjacentElement("afterend",brief);}
  const d=$("cgDistrictTitle")?.textContent?.trim()||"Raipur";
  const name=$("cgMapLeader")?.value||"all";
  const topic=$("cgMapIssue")?.value||"all";
  const start=$("cgMapFrom")?.value||"2023-01-01";
  const end=$("cgMapTo")?.value||"2026-11-10";
  const matching=TAX.bjpRecords.filter(r=>r.date>=start&&r.date<=end&&r.district===d&&(name==="all"||r.leader===name)&&(topic==="all"||r.primaryIssue===topic||(r.secondaryIssues||[]).includes(topic)));
  brief.innerHTML='<b>V12 BJP / Government District Evidence</b><p>'+esc(d)+' · '+matching.length+' newly indexed BJP source-linked item(s) under current filters. This is a selective index; zero does not establish inactivity. The main district map also contains the original V11 archive.</p>'+(matching.length?matching.slice(0,5).map(r=>'<p><strong>'+esc(r.date)+' · '+esc(r.leader)+'</strong> · <a class="v12-link" target="_blank" rel="noopener noreferrer" href="'+esc(u(r.url))+'">'+esc(r.title)+' ↗</a></p>').join(""):'');
}
function installEvents(){
  document.addEventListener("click",e=>{
    const btn=e.target.closest("[data-v12-person]");
    if(btn){e.preventDefault();const name=btn.getAttribute("data-v12-person"),side=btn.getAttribute("data-v12-party");if(side==="bjp"){bjpLeader=name;bjpTopic="all";renderBjp();btnNav("v12-bjp");$("v12BjpDetails")?.scrollIntoView({behavior:"smooth",block:"nearest"});}else{const picker=[...document.querySelectorAll("[data-pick-leader]")].find(x=>x.dataset.pickLeader===name);picker?.click();}return;}
    if(e.target.closest(".cg-poly")||e.target.closest("[data-map-choice]"))setTimeout(addDistrictPanel,0);
  });
  ["cgMapLeader","cgMapIssue","cgMapType","cgMapFrom","cgMapTo","cgMapReset","cgTimeline"].forEach(id=>$(id)?.addEventListener("change",()=>setTimeout(addDistrictPanel,0)));
  $("v12GroupFilter")?.addEventListener("change",e=>{group=e.target.value;renderMatrix()});
  ["v12From","v12To"].forEach(id=>$(id)?.addEventListener("change",()=>{const range=OUT();if(range.end<range.start){$("v12To").value=range.start;}renderAll();}));
}
function renderAll(){renderBjp();renderOppPies();renderMatrix();renderCommand();renderCm();addDistrictPanel();}
async function loadApiFeed(){
  try{
    const response=await fetch("./cm_posts.json",{cache:"no-store"});
    if(!response.ok)return;
    const body=await response.json();
    if(!body||!Array.isArray(body.posts))return;
    const allowed=new Set(["X","Facebook","Instagram"]);
    const imported=body.posts.filter(p=>p&&p.api_verified===true&&allowed.has(p.platform)
      &&String(p.date||"")>="2026-08-05"&&String(p.date||"")<="2026-11-05"
      &&Boolean(u(p.url))&&String(p.collection_method||"").startsWith("authorised_"));
    TAX.cmSocialApi.posts=imported;
    TAX.cmSocialApi.status=body.status||{};
    if(body.status?.x?.state==="connected")TAX.cmSocialApi.x.status="Connected via authorised X API · "+body.status.x.retrieved+" posts retrieved";
    renderCm();
  }catch(_){/* Static embedded archive remains available without API file. */}
}
setupImport();installEvents();renderAll();loadApiFeed();
document.documentElement.classList.add("v12-ready");
})();