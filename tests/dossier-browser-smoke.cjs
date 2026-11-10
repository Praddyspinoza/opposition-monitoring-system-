const { chromium } = require('playwright');
const { pathToFileURL } = require('url');
const path = require('path');

const must = (condition, message) => { if(!condition) throw new Error(message); };
(async () => {
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const entry=pathToFileURL(path.resolve(__dirname,'../index.html')).href;
 try {
  for(const spec of [
   {name:'desktop',width:1440,height:900,js:true},
   {name:'ipad',width:1024,height:1366,js:true},
   {name:'mobile',width:390,height:844,js:true},
   {name:'ipad-nojs',width:1024,height:1366,js:false},
   {name:'mobile-nojs',width:390,height:844,js:false}
  ]) {
   const context=await browser.newContext({viewport:{width:spec.width,height:spec.height},javaScriptEnabled:spec.js,reducedMotion:'reduce'});
   const page=await context.newPage(),errors=[];
   page.on('pageerror',error=>errors.push(String(error)));
   await page.goto(entry,{waitUntil:'load'});
   must(await page.locator('#cgDistrictMap .cg-poly').count()===33,spec.name+': 33 district outlines required');
   must(await page.locator('.cg-district-choice').count()===33,spec.name+': 33 district choices required');
   must(await page.locator('#cg-map-hub').isVisible(),spec.name+': map not visible');
   if(spec.js) {
    const stats=await page.evaluate(()=>({
     archive:JSON.parse(document.querySelector('#archiveData').textContent).length,
     old:JSON.parse(document.querySelector('#cgMapHistoricData').textContent).length
    }));
    must(stats.archive===182&&stats.old===32,spec.name+': source count changed: '+JSON.stringify(stats));
    await page.locator('.cg-district-choice[data-map-choice="Sakti"]').click();
    must((await page.locator('#cgResearchDistrict').textContent()).includes('Sakti'),spec.name+': selecting Sakti must open dossier');
    must(await page.locator('#cgResearchMatrixBody tr').count()===10,spec.name+': expected 10 leader rows');
    must(await page.locator('#cgResearchMatrixBody button[data-research-topic]:not([data-research-topic="all"])').count()===50,spec.name+': expected 50 leader-topic cells');
    await page.locator('.cg-district-choice[data-map-choice="Korba"]').click();
    must((await page.locator('#cgResearchDistrict').textContent()).includes('Korba'),spec.name+': selecting Korba must change dossier');
    await page.selectOption('#cgResearchLeader','Jyotsna Charandas Mahant');
    await page.selectOption('#cgResearchTopic','Mining');
    const link=page.locator('#cgResearchFeed a.cg-item-head').first();
    must(await link.count()>0,spec.name+': Korba/Jyotsna/Mining should have publisher source');
    must((await link.getAttribute('href')).startsWith('https://'),spec.name+': original source URL absent');
    await page.locator('.cg-district-choice[data-map-choice="Bemetara"]').click();
    must(await page.locator('#cgResearchMatrixBody tr').count()===10,spec.name+': all 10 leaders must appear for gaps');
    must(await page.locator('#cgResearchMatrixBody button[data-research-topic]:not([data-research-topic="all"])').count()===50,spec.name+': gap rows must preserve all 50 intersections');
    await page.locator('#cgResearchClear').click();
    const r=page.locator('#cgResearchRelation');const before=+(await page.locator('#cgResearchSourceCount').textContent());
    await r.selectOption('all');
    const after=+(await page.locator('#cgResearchSourceCount').textContent());
    must(after>=before,spec.name+': expanded location scope must not reduce sources');
    await page.locator('#cgMapReset').click();
    must((await page.locator('#cgResearchDistrict').textContent()).includes('Raipur'),spec.name+': reset must return to Raipur');
   }
   const overflow=await page.evaluate(()=>Math.max(0,document.documentElement.scrollWidth-window.innerWidth));
   must(overflow<=28,spec.name+': horizontal overflow '+overflow+'px');
   must(errors.length===0,spec.name+': browser JavaScript errors '+errors.join('; '));
   await page.screenshot({path:path.resolve(__dirname,'v9-'+spec.name+'.png'),fullPage:false});
   console.log('PASS',spec.name,JSON.stringify({overflow,js:spec.js}));
   await context.close();
  }
 }finally{await browser.close()}
 console.log('PASS: V9 district dossier smoke complete');
})().catch(e=>{console.error(e);process.exit(1)});
