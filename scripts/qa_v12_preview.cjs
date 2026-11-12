#!/usr/bin/env node
'use strict';
// Local static and source integrity checks for Chhattisgarh V12; no API credentials.
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const page=fs.readFileSync(path.join(root,'preview/v12/index.html'),'utf8');
const v11=fs.readFileSync(path.join(root,'index.html'),'utf8');
const data=JSON.parse(fs.readFileSync(path.join(root,'preview/v12/v12_data.json'),'utf8'));
const social=JSON.parse(fs.readFileSync(path.join(root,'preview/v12/social_discovery.json'),'utf8'));
function scriptById(id) {
 const escaped=id.replace(/[.*+?^$\{\}()|[\]\\]/g,'\\$&');
 const rx=new RegExp('<script id="'+escaped+'"([^>]*)>([\\s\\S]*?)<\\/script>');
 const result=page.match(rx);
 assert(result,'Missing inline script: '+id);
 return {attrs:result[1],text:result[2]};
}
const expected=["Vishnu Deo Sai","Kiran Singh Deo","Arun Sao","Vijay Sharma","O. P. Choudhary","Deepak Mhaskey","Dr. Raman Singh","Brijmohan Agrawal","Bhavna Bohra","Kedar Kashyap"];
assert.deepEqual(data.bjpLeaders.map(x=>x.n),expected);
assert.equal(data.issueTaxonomy.length,10);
assert.equal(data.bjpRecords.length,112);
assert.equal(social.originalXPostLinks.length,24);
assert.equal(JSON.parse(scriptById('archiveData').text).length,182);
assert.equal(JSON.parse(scriptById('v12Data').text).bjpRecords.length,112);
assert.equal(JSON.parse(scriptById('v12MapRecords').text).length,112);
assert.equal(JSON.parse(scriptById('v12SocialLinksData').text).originalXPostLinks.length,24);
const originalArchive=v11.match(/<script id="archiveData" type="application\/json">([\s\S]*?)<\/script>/);
assert(originalArchive,'Original V11 archive missing');
assert.equal(scriptById('archiveData').text,originalArchive[1],'V11 research archive unexpectedly modified');
for(const id of ['v12MainScript','v12MotionSocialScript'])new vm.Script(scriptById(id).text,{filename:id+'.js'});
for(const id of ['v12FlowPanel','v12FlowSvg','v12SocialLedger','v12SocialAccounts','v12CmSocialRecoveredList','v12BjpGallery','v12MatrixBody','v12CmPie']){
 assert(page.includes('id="'+id+'"'),'Missing HTML target '+id);
}
assert(page.includes('data-nav="v12-links"'));
assert(page.includes('data-nav="v12-bjp"'));
assert(page.includes('data-nav="v12-cm"'));
assert(page.includes('id="cgDistrictMap"'));
const keys=new Set();
for(const r of data.bjpRecords){
 assert(r.date>='2026-08-05'&&r.date<='2026-11-05','Date out of window '+r.id);
 assert(/^https:\/\//.test(r.url),'Bad BJP URL '+r.id);
 assert(expected.includes(r.leader),'Unknown leader '+r.id);
 if(r.primaryIssue)assert(data.issueTaxonomy.some(t=>t.id===r.primaryIssue),'Unknown issue '+r.id);
 const key=r.leader+'|'+r.url;
 assert(!keys.has(key),'Duplicate BJP leader+URL '+r.id);keys.add(key);
}
for(const post of social.originalXPostLinks){
 const match=String(post.url).match(/^https:\/\/x\.com\/vishnudsai\/status\/(\d+)$/);
 assert(match,'Not CM original status permalink: '+post.url);
 const date=new Date(Number(BigInt(match[1])>>22n)+1288834974657).toISOString().slice(0,10);
 assert.equal(date,post.date,'X snowflake date mismatch');
 assert(post.date>='2026-08-05'&&post.date<='2026-11-05');
 assert(post.publisherUrl.startsWith('https://'),'No corroborating publisher');
 assert.equal(post.apiVerified,false,'Publisher-linked post must not be called API-verified');
}
const motion=fs.readFileSync(path.join(root,'preview/v12/motion_social.js'),'utf8');
assert(!motion.includes('requestAnimationFrame('),'Motion should not repaint continuously via JS');
assert(!motion.includes('setInterval('),'Motion should not run background JS intervals');
assert(page.includes('prefers-reduced-motion:reduce'),'Reduced-motion CSS missing');
console.log('PASS V12 static QA: V11 preserved; BJP=112; opposition=182; CM X originals=24; 10 issues; 20 leaders; JS syntax valid; flow uses no JS animation loop.');
