(function v12Enhance(){
"use strict";
const get=id=>document.getElementById(id);
const escape=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const d=JSON.parse(get("v12Data").textContent||"{}");
const op=JSON.parse(get("archiveData").textContent||"[]");
const oppNames=JSON.parse(get("peopleData").textContent||"[]");
const TAX=d.issueTaxonomy||[];
let socials=JSON.parse(get("v12SocialLinksData").textContent||"{}");
const normalize=val=>{const key=String(val||"").toLowerCase().trim();if(key==="tribal issues"||key==="tribal rights")return "Tribal Issues";return TAX.find(t=>t.id.toLowerCase()===key)?.id||null;};
const first=cs=>(Array.isArray(cs)?cs:[]).map(normalize).find(Boolean)||null;
const B=d.bjpLeaders.map(x=>x.n);
const V12_DATES={from:"2026-08-05",to:"2026-11-05"};
const all=[];for(const r of d.bjpRecords){if(r.date<V12_DATES.from||r.date>V12_DATES.to)continue;const issue=normalize(r.primaryIssue);all.push({leader:r.leader,issue,date:r.date,district:r.district||"",party:"bjp",source:r.url||""});}
for(const r of op){if(r.date<V12_DATES.from||r.date>V12_DATES.to)continue;const issue=first(r.categories);for(const leader of Array.isArray(r.leaders)?r.leaders:[]){if(oppNames.includes(leader))all.push({leader,issue,date:r.date,district:r.district||"",party:"opp",source:r.url||""});}}
const flow={party:"bjp",leader:"all",issue:"all",paused:false};
const namesFor=()=>flow.party==="bjp"?B:flow.party==="opp"?oppNames:B.concat(oppNames);
const rowsFor=()=>all.filter(r=>(flow.party==="all"||r.party===flow.party)&&(flow.leader==="all"||flow.leader===r.leader)&&(flow.issue==="all"||flow.issue===r.issue)&&r.issue);
function flowOptions(){
 const sel=get("v12FlowLeader");if(!sel)return;
 const before=flow.leader;const names=namesFor();
 sel.innerHTML='<option value="all">All '+names.length+' leaders</option>'+names.map(n=>'<option value="'+escape(n)+'">'+escape(n)+'</option>').join("");
 if(before!=="all"&&names.includes(before))sel.value=before;else{flow.leader="all";sel.value="all";}
 const topic=get("v12FlowIssue");topic.innerHTML='<option value="all">All ten issues</option>'+TAX.map(x=>'<option value="'+escape(x.id)+'">'+escape(x.id)+'</option>').join("");
 topic.value=flow.issue;
}
function svgCurve(fromX,fromY,toX,toY){
 const bend=(toX-fromX)*.48;
 return `M${fromX},${fromY} C${fromX+bend},${fromY} ${toX-bend},${toY} ${toX},${toY}`;
}
function flowRender(){
 const svg=get("v12FlowSvg");if(!svg)return;
 const rows=rowsFor(), leaders=namesFor();
 const issueList=TAX.map(t=>t.id);
 const countBy=new Map();
 const byIssue=new Map();
 const districts=new Map();
 const outDist=name=>{
   const v=String(name||"").trim();
   if(!v||/statewide|national|multiple|division|not assign|all districts/i.test(v))return "Regional / unassigned";
   return v;
 };
 for(const r of rows){const ld=r.leader+"|"+r.issue;countBy.set(ld,(countBy.get(ld)||0)+1);
   byIssue.set(r.issue,(byIssue.get(r.issue)||0)+1);
   const district=outDist(r.district);districts.set(district,(districts.get(district)||0)+1);}
 const districtNames=[...districts].sort((a,b)=>b[1]-a[1]).slice(0,8).map(x=>x[0]);
 if(districts.size>8)districtNames.push("Other districts");
 if(districtNames.length===0)districtNames.push("No district records");
 const w=1070;
 const height=Math.max(595,92+Math.max(leaders.length,issueList.length,districtNames.length)*27);
 svg.setAttribute("viewBox","0 0 "+w+" "+height);
 const yFor=(i,n)=>74+(i+.5)*((height-115)/Math.max(1,n));
 const leaderPos=new Map(leaders.map((x,i)=>[x,yFor(i,leaders.length)]));
 const issuePos=new Map(issueList.map((x,i)=>[x,yFor(i,issueList.length)]));
 const districtPos=new Map(districtNames.map((x,i)=>[x,yFor(i,districtNames.length)]));
 const districtFor=x=>districtPos.has(x)?x:"Other districts";
 const edgesLeft=[];for(const [key,val] of countBy){const at=key.indexOf("|");const name=key.slice(0,at),topic=key.slice(at+1);if(val>0&&leaderPos.has(name)&&issuePos.has(topic))edgesLeft.push({name,topic,val});}
 const edgesRight=new Map();
 for(const r of rows){const key=r.issue+"|"+districtFor(outDist(r.district));edgesRight.set(key,(edgesRight.get(key)||0)+1);}
 const right=[...edgesRight].map(([key,val])=>{const at=key.indexOf("|");return{topic:key.slice(0,at),district:key.slice(at+1),val};}).filter(x=>districtPos.has(x.district)&&issuePos.has(x.topic));
 const animatedLeft=new Set(edgesLeft.slice().sort((a,b)=>b.val-a.val).slice(0,4).map(x=>x.name+"|"+x.topic));
 const animatedRight=new Set(right.slice().sort((a,b)=>b.val-a.val).slice(0,4).map(x=>x.topic+"|"+x.district));
 const line1=edgesLeft.map(x=>{
   const t=TAX.find(z=>z.id===x.topic);
   const live=animatedLeft.has(x.name+"|"+x.topic);
   return '<path d="'+svgCurve(258,leaderPos.get(x.name),413,issuePos.get(x.topic))+'" class="v12-flow-line'+(live?" live":"")+'" stroke="'+escape(t?.color||"#7ea7b6")+'" stroke-width="'+Math.min(3,1+Math.sqrt(x.val)*.32)+'"><title>'+escape(x.name+" → "+x.topic+": "+x.val+" indexed")+'</title></path>';
 }).join("");
 const line2=right.map(x=>{
   const t=TAX.find(z=>z.id===x.topic),live=animatedRight.has(x.topic+"|"+x.district);
   return '<path d="'+svgCurve(664,issuePos.get(x.topic),824,districtPos.get(x.district))+'" class="v12-flow-line'+(live?" live":"")+'" stroke="'+escape(t?.color||"#7ea7b6")+'" stroke-width="'+Math.min(3,1+Math.sqrt(x.val)*.33)+'"><title>'+escape(x.topic+" → "+x.district+": "+x.val+" indexed")+'</title></path>';
 }).join("");
 const legend='<text class="v12-header-label" x="44" y="30">LEADERS</text><text class="v12-header-label" x="430" y="30">ISSUES</text><text class="v12-header-label" x="836" y="30">DISTRICTS</text>';
 const a=leaders.map(n=>{
  const y=leaderPos.get(n),cnt=rows.filter(r=>r.leader===n).length,selected=flow.leader===n;
  const label=n.length>18?n.slice(0,17)+"…":n;
  return '<g data-flow-leader="'+escape(n)+'" role="button" tabindex="0" aria-label="Filter to '+escape(n)+'"><rect class="v12-node" x="30" y="'+(y-13)+'" width="228" height="26" rx="8" style="'+(selected?"stroke:#e8c78d;fill:#2e3c43;":"")+'"></rect><text x="43" y="'+y+'">'+escape(label)+'</text><text class="v12-node-count" x="245" y="'+y+'" text-anchor="end">'+cnt+'</text></g>';
 }).join("");
 const mid=issueList.map(n=>{
  const y=issuePos.get(n),topic=TAX.find(t=>t.id===n),short=topic?.ab||n,cnt=byIssue.get(n)||0;
  return '<g data-flow-issue="'+escape(n)+'" role="button" tabindex="0" aria-label="Filter issue '+escape(n)+'"><rect class="v12-node" x="411" y="'+(y-14)+'" width="254" height="28" rx="8" style="stroke:'+escape(topic?.color||"#627")+';'+(flow.issue===n?"fill:#284345;":"")+'"></rect><text x="423" y="'+y+'">'+escape(short)+'</text><text class="v12-node-count" x="649" y="'+y+'" text-anchor="end">'+cnt+'</text></g>';
 }).join("");
 const ds=districtNames.map(n=>{
   const y=districtPos.get(n),cnt=n==="Other districts"?[...districts].filter(x=>!districtNames.includes(x[0])).reduce((a,x)=>a+x[1],0):districts.get(n)||0;
   return '<g data-flow-district="'+escape(n)+'" role="button" tabindex="0" aria-label="Open '+escape(n)+' district map"><rect class="v12-node" x="823" y="'+(y-14)+'" width="229" height="28" rx="8"></rect><text x="835" y="'+y+'">'+escape(n.length>20?n.slice(0,19)+"…":n)+'</text><text class="v12-node-count" x="1038" y="'+y+'" text-anchor="end">'+cnt+'</text></g>';
 }).join("");
 svg.innerHTML=legend+line1+line2+a+mid+ds;
 const uniqueSource=new Set(rows.map(r=>r.source)).size;
 const kpis=[
 [uniqueSource,"unique source URLs in filter"],
 [leaders.filter(n=>rows.some(r=>r.leader===n)).length,"leaders with issue evidence"],
 [byIssue.size,"issues with linked records"],
 [districts.size,"distinct district labels"]
 ];
 get("v12FlowKpis").innerHTML=kpis.map(([v,l])=>'<div class="v12-flow-kpi"><b>'+v+'</b><span>'+escape(l)+'</span></div>').join("");
 get("v12FlowScope").textContent=rows.length+" leader-source references · source-share paths, not traffic or geolocation";
 get("v12FlowPause").textContent=flow.paused?"▶ Resume motion":"❚❚ Pause motion";
 get("v12FlowPanel").dataset.motion=flow.paused?"paused":"active";
}
function showParty(party){
 flow.party=party;flow.leader="all";get("v12FlowParty").value=party;flowOptions();flowRender();
}
function initFlow(){
 if(!get("v12FlowPanel"))return;
 flowOptions();
 get("v12FlowParty").addEventListener("change",e=>showParty(e.target.value));
 get("v12FlowLeader").addEventListener("change",e=>{flow.leader=e.target.value;flowRender();});
 get("v12FlowIssue").addEventListener("change",e=>{flow.issue=e.target.value;flowRender();});
 get("v12FlowPause").addEventListener("click",()=>{flow.paused=!flow.paused;flowRender();});
 const nodes=get("v12FlowSvg");
 function activate(target){
   const leader=target.closest("[data-flow-leader]");const issue=target.closest("[data-flow-issue]");const district=target.closest("[data-flow-district]");
   if(leader){flow.leader=leader.getAttribute("data-flow-leader");get("v12FlowLeader").value=flow.leader;flowRender();}
   if(issue){flow.issue=issue.getAttribute("data-flow-issue");get("v12FlowIssue").value=flow.issue;flowRender();}
   if(district){const d=district.getAttribute("data-flow-district");const match=[...document.querySelectorAll(".cg-poly")].find(x=>x.getAttribute("data-name")===d);
     if(match){match.dispatchEvent(new MouseEvent("click",{bubbles:true}));match.scrollIntoView({behavior:"smooth",block:"center"});}
   }
 }
 nodes.addEventListener("click",e=>activate(e.target));
 nodes.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();activate(e.target);}});
 const panel=get("v12FlowPanel");
 if("IntersectionObserver" in window){const ob=new IntersectionObserver(entries=>{for(const e of entries)panel.dataset.visible=e.isIntersecting?"true":"false";},{threshold:0.02});ob.observe(panel);}
 document.addEventListener("visibilitychange",()=>{panel.dataset.visible=document.hidden?"false":"true";});
 get("v12FlowJump")?.addEventListener("click",()=>{document.querySelector('[data-nav="command"]')?.click();setTimeout(()=>panel.scrollIntoView({behavior:"smooth",block:"start"}),0);});
 flowRender();
}
function socialCard(p){
 const link=String(p.url||"").startsWith("https://")?p.url:"";
 const corroboration=String(p.publisherUrl||"").startsWith("https://")?p.publisherUrl:"";
 return '<article class="v12-social-card"><small>'+escape(p.date)+' · X / Twitter · <b>Publisher-embedded original post URL</b> · '+escape(p.publisherName||"Media source")+'</small><strong>'+escape(p.title||"Publisher-linked X post")+'</strong><small>'+escape(p.issue==="Unclassified"?"Not issue-classified":p.issue)+' · Original X permalink recovered, API-authored text not retrieved</small><div class="v12-social-links">'+(link?'<a target="_blank" rel="noopener noreferrer" href="'+escape(link)+'">Open original X post ↗</a>':'')+(corroboration?'<a target="_blank" rel="noopener noreferrer" href="'+escape(corroboration)+'">Read corroborating publisher ↗</a>':'')+'</div></article>';
}
let socialIssue="all",socialQuery="";
function filteredPosts(){
 return (socials.originalXPostLinks||[]).filter(p=>(socialIssue==="all"||p.issue===socialIssue)&&(!socialQuery||(p.title+" "+p.issue+" "+p.date+" "+p.publisherName).toLowerCase().includes(socialQuery)))
 .sort((a,b)=>b.date.localeCompare(a.date));
}
function accountsHtml(){
 return (socials.accounts||[]).map(p=>'<div class="v12-social-account"><b>'+escape(p.person)+' · '+escape(p.platform)+'</b><small>'+escape(p.verification||"")+'</small><a href="'+escape(p.url)+'" target="_blank" rel="noopener noreferrer">Open account ↗</a></div>').join("");
}
function renderSocial(){
 if(!get("v12SocialLedger"))return;
 const p=filteredPosts();
 get("v12SocialLedger").innerHTML=p.length?p.map(socialCard).join(""):'<div class="v12-blank">No publisher-embedded post permalinks match this filter. This does not imply no posts were made.</div>';
 get("v12SocialCount").textContent=p.length+" original X URLs with publisher references";
 const cm=get("v12CmDiscoveryPreview");
 if(cm){cm.innerHTML='<div class="v12-social-kpis"><div><b>'+socials.originalXPostLinks.length+'</b><span>publisher-linked CM X post permalinks</span></div><div><b>'+socials.accounts.filter(p=>p.platform==="Facebook"||p.platform==="Instagram").length+'</b><span>CM and CMO Meta account links</span></div><div><b>0</b><span>authenticated API-origin post imports</span></div></div><p class="v12-hint">Recovered links are real post URLs embedded in dated published articles. They are not a full API-sourced X archive or authenticated Meta posts.</p><button type="button" class="v12-btn" id="v12OpenSocial" style="margin-top:8px">Open source-linked social archive ↗</button>';
  get("v12OpenSocial")?.addEventListener("click",()=>document.querySelector('[data-nav="v12-links"]')?.click());
 }
 const stats=get("v12SocialStats");
 if(stats)stats.innerHTML='<div><b>'+socials.originalXPostLinks.length+'</b><span>CM X original post permalinks</span></div><div><b>'+socials.accounts.length+'</b><span>official CM/CMO account directory links</span></div><div><b>'+socials.metaPostLinks.length+'</b><span>Meta original post permalinks independently recovered</span></div>';
 const recovered=get("v12CmSocialRecoveredList");
 if(recovered){recovered.innerHTML='<h3 style="margin:14px 0 5px;font-size:14px;color:#d4eee9">Original CM X posts recovered via publishers</h3><p class="v12-hint">These are exact public post permalinks with corroborating articles, not authenticated X API exports.</p>'+(socials.originalXPostLinks||[]).slice().sort((a,b)=>b.date.localeCompare(a.date)).slice(0,10).map(socialCard).join("")+'<button type="button" class="v12-btn" id="v12CmViewAllPosts">View all source-linked CM X posts ↗</button>';
 recovered.querySelector("#v12CmViewAllPosts")?.addEventListener("click",()=>document.querySelector('[data-nav="v12-links"]')?.click());}
 document.querySelectorAll("[data-v12-social-banner]").forEach(b=>{b.innerHTML='<span class="v12-cap">V12.1 / ORIGINAL SOCIAL LINKS RECOVERED</span><h3>CM X: '+(socials.originalXPostLinks||[]).length+' publisher-embedded post permalinks · Meta: '+socials.accounts.filter(a=>a.platform==="Facebook"||a.platform==="Instagram").length+' CM / CMO account references</h3><p class="v12-hint">These are separate from the API-verified totals, which remain zero until authorised collection. Open the sourced archive for individual post URLs and publisher references.</p><button type="button" class="v12-btn" data-open-social-links>Open original X &amp; Meta links ↗</button>';b.querySelector("[data-open-social-links]")?.addEventListener("click",()=>document.querySelector('[data-nav="v12-links"]')?.click());});
 get("v12SocialAccounts").innerHTML=accountsHtml();
 const select=get("v12SocialIssue");if(select&&select.options.length===1)select.innerHTML='<option value="all">All issue tags</option><option value="Unclassified">Unclassified / ceremonial</option>'+TAX.map(t=>'<option value="'+escape(t.id)+'">'+escape(t.id)+'</option>').join("");
 if(select)select.value=socialIssue;
}
function publicSearchCards(){
 const names=d.bjpLeaders.map(x=>({name:x.n,party:"BJP / Government"})).concat(oppNames.map(name=>({name,party:"Opposition"})));
 const parent=get("v12PublicSocialSearch");if(!parent)return;
 parent.innerHTML=names.map(x=>{
 const query='"'+x.name+'" since:2026-08-05 until:2026-11-06';
 const xurl='https://x.com/search?q='+encodeURIComponent(query)+'&src=typed_query';
 const fb='https://www.google.com/search?q='+encodeURIComponent('site:facebook.com "'+x.name+'" "2026"');
 const ig='https://www.google.com/search?q='+encodeURIComponent('site:instagram.com "'+x.name+'" 2026');
 return '<div class="v12-social-searchrow"><b>'+escape(x.name)+'</b><small>'+escape(x.party)+' · search shortcuts only, not verified post records</small><a href="'+escape(xurl)+'" target="_blank" rel="noopener noreferrer">Search X ↗</a><a href="'+escape(fb)+'" target="_blank" rel="noopener noreferrer">Search Facebook ↗</a><a href="'+escape(ig)+'" target="_blank" rel="noopener noreferrer">Search Instagram ↗</a></div>';
 }).join("");
}
function initSocial(){
 if(!get("v12SocialLedger"))return;
 publicSearchCards();renderSocial();
 get("v12SocialIssue").addEventListener("change",e=>{socialIssue=e.target.value;renderSocial();});
 let last="",timer=null;
 get("v12SocialSearch").addEventListener("input",e=>{socialQuery=e.target.value.toLowerCase().trim();clearTimeout(timer);timer=setTimeout(()=>renderSocial(),120);});
 // Static embedded snapshot is usable offline. Fetch enables updated publisher-link data without an HTML rebuild.
 fetch("./social_discovery.json",{cache:"no-store"}).then(r=>r.ok?r.json():null).then(p=>{
    if(p&&Array.isArray(p.originalXPostLinks)&&Array.isArray(p.accounts)){socials=p;renderSocial();}
 }).catch(()=>{});
}
initFlow();initSocial();
})();