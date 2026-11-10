const {chromium}=require('playwright');
const {pathToFileURL}=require('url');
const path=require('path');
function check(condition,message){if(!condition)throw Error(message)}
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 try{
  for(const spec of [
   {name:'desktop',width:1440,height:900,js:true},
   {name:'ipad',width:1024,height:1366,js:true},
   {name:'iphone',width:390,height:844,js:true},
   {name:'iphone-nojs',width:390,height:844,js:false}
  ]){
   const context=await browser.newContext({viewport:{width:spec.width,height:spec.height},javaScriptEnabled:spec.js,reducedMotion:'reduce'});
   const page=await context.newPage(),errors=[];
   page.on('pageerror',error=>errors.push(String(error.message||error)));
   await page.goto(pathToFileURL(path.resolve(__dirname,'../index.html')).href,{waitUntil:'load'});
   check(await page.locator('#siEvidenceHub').count()===1,spec.name+': new social intelligence console absent');
   check(await page.locator('#cgDistrictMap .cg-poly').count()===33,spec.name+': original district map changed');
   if(spec.js){
    await page.locator('[data-nav="meta"]').click();
    check(await page.locator('#meta').isVisible(),spec.name+': social archive tab did not activate');
    check((await page.locator('#siXCount').innerText()).trim()==='11',spec.name+': expected eleven publisher-corroborated X post URLs');
    check((await page.locator('#siPressCount').innerText()).trim()==='14',spec.name+': expected fourteen press leads');
    check((await page.locator('#siMetaCount').innerText()).trim()==='0',spec.name+': should not fabricate direct Meta posts');
    check(await page.locator('#siAccountDirectory .si-account').count()===10,spec.name+': missing leader account entries');
    check(await page.locator('#siAccountDirectory .si-acc-platforms>div').count()===30,spec.name+': missing Facebook Instagram or X identity slots');
    await page.locator('#siKind').selectOption('x');
    check((await page.locator('#siMatches').innerText()).includes('11 evidence items'),spec.name+': X permalink mode broken');
    check(await page.locator('#siEvidenceList a[href^="https://x.com/"]').count()===11,spec.name+': original X links not rendered');
    await page.locator('#siLeader').selectOption('Deepak Baij');
    check((await page.locator('#siMatches').innerText()).includes('2 evidence items'),spec.name+': leader filter failed');
    await page.locator('#siTopic').selectOption('Tribal Issues');
    check((await page.locator('#siMatches').innerText()).includes('2 evidence items'),spec.name+': topic filter failed');
    await page.locator('#siReset').click();
    await page.locator('#siKind').selectOption('meta');
    check((await page.locator('#siMatches').innerText()).includes('1 evidence item'),spec.name+': one Facebook press reference should show');
    check((await page.locator('#siEvidenceList').innerText()).includes('not a retrieved first-party social post'),spec.name+': publisher link misrepresented');
    await page.locator('#siPlatform').selectOption('Instagram');
    check((await page.locator('#siMatches').innerText()).includes('0 evidence items'),spec.name+': should not synthesize Instagram post');
    check((await page.locator('#siEvidenceList').innerText()).includes('No attributable evidence'),spec.name+': collection gap missing');
    await page.locator('#siReset').click();
    const count=await page.locator('#siEvidenceList .si-card').count();
    check(count===18,spec.name+': list must show first 18 evidence items; got '+count);
    await page.locator('#siMore').click();
    check(await page.locator('#siEvidenceList .si-card').count()===25,spec.name+': show-more button missing final source');
    await page.locator('#siAccountsDetails summary').click();
    check(await page.locator('#siAccountsDetails').getAttribute('open')!==null,spec.name+': candidate account directory did not open');
    check((await page.locator('#metaOriginalCount').innerText()).trim()==='0',spec.name+': old Meta archive must not change');
   }else{
    check(await page.locator('#meta').isVisible(),spec.name+': no-JS status must remain accessible');
    check(await page.locator('#siEvidenceList a[href^="https://x.com/"]').count()>=2,spec.name+': static original X links unavailable');
   }
   const overflow=await page.evaluate(()=>Math.max(0,document.documentElement.scrollWidth-window.innerWidth));
   check(overflow<=28,spec.name+': horizontal overflow '+overflow+'px');
   check(!errors.length,spec.name+': uncaught JS errors: '+errors.join(' / '));
   await page.screenshot({path:path.resolve(__dirname,'social-'+spec.name+'.png'),fullPage:false});
   console.log('PASS',spec.name,JSON.stringify({overflow,errors}));
   await context.close();
  }
 }finally{await browser.close()}
 console.log('PASS: social cross-platform verified evidence smoke');
})().catch(error=>{console.error(error);process.exit(1)});