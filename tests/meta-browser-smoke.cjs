const { chromium } = require('playwright');
const { pathToFileURL } = require('url');
const path = require('path');
function assert(cond,msg){if(!cond)throw Error(msg)}
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try {
  for(const spec of [
   {name:'desktop',width:1440,height:900,js:true},
   {name:'ipad',width:1024,height:1366,js:true},
   {name:'iphone',width:390,height:844,js:true},
   {name:'iphone-nojs',width:390,height:844,js:false}
  ]){
   const context=await browser.newContext({viewport:{width:spec.width,height:spec.height},javaScriptEnabled:spec.js,reducedMotion:'reduce',acceptDownloads:true});
   const page=await context.newPage(),errors=[];
   page.on('pageerror',e=>errors.push(e.message||String(e)));
   await page.goto(pathToFileURL(path.resolve(__dirname,'../index.html')).href,{waitUntil:'load'});
   assert(await page.locator('#meta').count()===1,spec.name+': Meta view missing');
   assert(await page.locator('#metaAccountDirectory').count()===1,spec.name+': directory missing');
   assert(await page.locator('#cgDistrictMap .cg-poly').count()===33,spec.name+': existing map changed');
   if(spec.js){
    await page.locator('[data-nav="meta"]').click();
    assert(await page.locator('#meta').isVisible(),spec.name+': Meta tab not activated');
    assert(await page.locator('#metaAccountDirectory .meta-account').count()===10,spec.name+': 10 profiles not visible');
    assert(await page.locator('#metaAccountDirectory .meta-account-links>div').count()===20,spec.name+': 20 platform slots missing');
    assert((await page.locator('#metaOriginalCount').innerText()).trim()==='0',spec.name+': historical posts must not be invented');
    const example=[{leader:'Deepak Baij',platform:'Facebook',published_at:'2026-10-12',url:'https://www.facebook.com/SomePage/posts/TESTONLY_12345',text:'Automated test fixture. Not a real post.',topics:['Tribal Issues'],districts:['Bastar'],post_type:'post'}];
    await page.locator('#metaPaste').fill(JSON.stringify(example));
    await page.locator('#metaImportPaste').click();
    assert((await page.locator('#metaLocalCount').innerText()).trim()==='1',spec.name+': valid post import missing');
    assert(await page.locator('#metaPostList .meta-post').count()===1,spec.name+': post card missing');
    assert((await page.locator('#metaPostList .meta-post').innerText()).includes('unverified'),spec.name+': imported content needs label');
    await page.locator('#metaPlatform').selectOption('Instagram');
    assert((await page.locator('#metaFilteredCount').innerText()).includes('0 match'),spec.name+': platform filter broken');
    await page.locator('#metaClearFilters').click();
    assert((await page.locator('#metaFilteredCount').innerText()).includes('1 match'),spec.name+': clear filters broken');
    await page.locator('#metaPaste').fill(JSON.stringify([{...example[0],url:'https://www.facebook.com/SomePage',published_at:'2026-10-14'}]));
    await page.locator('#metaImportPaste').click();
    assert((await page.locator('#metaImportStatus').innerText()).includes('rejected'),spec.name+': profile-only URL accepted');
    assert((await page.locator('#metaLocalCount').innerText()).trim()==='1',spec.name+': invalid import altered dataset');
    page.once('dialog',dlg=>dlg.accept());
    await page.locator('#metaClearLocal').click();
    assert((await page.locator('#metaLocalCount').innerText()).trim()==='0',spec.name+': local clearing failed');
   }else{
    assert(await page.locator('#meta').isVisible(),spec.name+': no-JS fallback not readable');
    assert((await page.locator('#meta').innerText()).includes('Collection status'),spec.name+': status note absent');
   }
   const overflow=await page.evaluate(()=>Math.max(0,document.documentElement.scrollWidth-window.innerWidth));
   assert(overflow<=28,spec.name+': horizontal overflow '+overflow+'px');
   assert(errors.length===0,spec.name+': JS errors '+errors.join('|'));
   await page.screenshot({path:path.resolve(__dirname,'meta-'+spec.name+'.png'),fullPage:false});
   console.log('PASS',spec.name,JSON.stringify({overflow,errors}));
   await context.close();
  }
 }finally{await browser.close()}
 console.log('PASS: Meta live-tab browser smoke validation');
})().catch(e=>{console.error(e);process.exit(1)});
