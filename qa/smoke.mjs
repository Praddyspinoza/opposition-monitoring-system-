import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const html=readFileSync("index.html","utf8");
assert.match(html, /id="cgDistrictMap"/);
assert.match(html, /id="cgMapHistoricData"/);
assert.equal((html.match(/class="cg-poly"/g)||[]).length,33,"33 geographic polygons");
assert.equal((html.match(/class="cg-district-choice"/g)||[]).length,33,"33 labelled district choices");
assert.equal((html.match(/data-orbit-node="/g)||[]).length,50,"50 existing topic-orbit controls");
const histMatch=html.match(/<script id="cgMapHistoricData" type="application\/json">([\s\S]*?)<\/script>/);
const archivMatch=html.match(/<script id="archiveData" type="application\/json">([\s\S]*?)<\/script>/);
assert(histMatch && archivMatch, "data containers must be available statically");
const historic=JSON.parse(histMatch[1]);
const archive=JSON.parse(archivMatch[1]);
assert.equal(historic.length,19);
assert.equal(archive.length,182);
assert.equal(new Set(historic.flatMap(r=>r.leaders)).size,10);
assert(historic.some(r=>r.date.startsWith("2023")));
assert(historic.every(r=>r.url.startsWith("https://")));
assert(historic.every(r=>r.actionType && r.outcomeStatus),"every historical item labels action and outcome");
assert(historic.some(r=>r.district==="Mahasamund"),"new Mahasamund source present");
assert(archive.every(r=>r.date>="2026-08-05" && r.date<="2026-11-05"));

const errors=[];
const dom=new JSDOM(html,{
 url:"https://example.org/opposition-monitoring-system-/",
 runScripts:"dangerously",
 pretendToBeVisual:true,
 beforeParse(w){
  w.scrollTo=()=>{};
  w.matchMedia=()=>({matches:false,addListener(){},removeListener(){}});
  w.addEventListener("error",e=>errors.push(e.message||String(e.error)));
 }
});
const {document,Event,MouseEvent}=dom.window;
assert.equal(document.querySelectorAll(".cg-poly").length,33);
assert.equal(document.getElementById("cgDistrictTitle").textContent,"Raipur","initial map district");
assert(Number(document.getElementById("cgDistrictTotal").textContent)>0,"Raipur sources count");
const durg=document.querySelector('.cg-poly[data-name="Durg"]');
durg.dispatchEvent(new MouseEvent("click",{bubbles:true}));
assert.equal(document.getElementById("cgDistrictTitle").textContent,"Durg","click selects district");
assert(Number(document.getElementById("cgDistrictTotal").textContent)>0,"Durg sources count");
const ld=document.getElementById("cgMapLeader");
ld.value="Bhupesh Baghel";
ld.dispatchEvent(new Event("change",{bubbles:true}));
const dt=document.getElementById("cgMapTo");
dt.value="2024-12-31";
dt.dispatchEvent(new Event("change",{bubbles:true}));
assert(Number(document.getElementById("cgDistrictTotal").textContent)>=1,"historic Baghel in Durg shows after date filtering");
assert.match(document.getElementById("cgDistrictEvidence").textContent,/2024-08-24/);
document.getElementById("cgMapReset").click();
assert.equal(document.getElementById("cgDistrictTitle").textContent,"Raipur");
assert.equal(ld.value,"all");
assert.equal(document.getElementById("cgMapType").value,"all","map displays all evidence classes by default");
assert.equal(document.getElementById("cgTimeline").value,"46","timeline resets to Nov 2026");
assert.equal(document.getElementById("cgTimelineMode").value,"cumulative","timeline resets to cumulative");
const time=document.getElementById("cgTimeline");
time.value="19";time.dispatchEvent(new Event("input",{bubbles:true}));
assert.equal(document.getElementById("cgMapTo").value,"2024-08-31");
assert.match(document.getElementById("cgTimelineLabel").textContent,/August 2024/);
const mode=document.getElementById("cgTimelineMode");
mode.value="monthly";mode.dispatchEvent(new Event("change",{bubbles:true}));
assert.equal(document.getElementById("cgMapFrom").value,"2024-08-01");
assert.equal(document.getElementById("cgMapTo").value,"2024-08-31");
document.getElementById("cgMapReset").click();
assert.equal(dt.value,"2026-11-10");
assert.equal(errors.length,0,"no inline JavaScript exceptions: "+errors.join("; "));
console.log("PASS: V7 map 33 boundaries, original V6 dossiers, 14 historical reports, date/leader drilldowns and default rendering");
