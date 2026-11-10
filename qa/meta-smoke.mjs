import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';

const html=readFileSync('index.html','utf8');
const seedMatch=html.match(/<script id="cgMetaSeed" type="application\/json">([\s\S]*?)<\/script>/);
assert(seedMatch,'Meta archive needs an embedded data manifest');
const meta=JSON.parse(seedMatch[1]);
assert.equal(meta.accounts.length,10,'10 leader identities');
assert.equal(meta.accounts.flatMap(a=>['facebook','instagram'].map(p=>a[p])).length,20,'20 platform slots');
assert.equal(meta.posts.length,0,'unretrieved historical posts must never be fictionalized');
assert.equal(meta.window.from,'2026-08-05');
assert.equal(meta.window.to,'2026-11-05');
assert.match(html,/data-nav="meta"/);
assert.match(html,/const views=new Set\(\[[^\]]*'meta'/);
const errors=[];
const dom=new JSDOM(html,{
 url:'https://example.org/opposition-monitoring-system-/',
 runScripts:'dangerously',
 pretendToBeVisual:true,
 beforeParse(w){
  w.scrollTo=()=>{};
  w.matchMedia=()=>({matches:false,addListener(){},removeListener(){}});
  w.confirm=()=>true;
  w.Element.prototype.scrollIntoView=()=>{};
  w.addEventListener('error',e=>errors.push(e.message||String(e.error)));
 }
});
const {document,MouseEvent,Event}=dom.window;
const E=id=>document.getElementById(id);
assert.equal(document.querySelectorAll('#metaAccountDirectory .meta-account').length,10);
assert.equal(document.querySelectorAll('#metaAccountDirectory .meta-account-links>div').length,20);
assert.equal(E('metaOriginalCount').textContent,'0');
assert.equal(E('metaLocalCount').textContent,'0');
document.querySelector('[data-nav="meta"]').dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
assert(document.getElementById('meta').classList.contains('active'),'Meta nav activates new tab');
assert(E('metaPostList').textContent.includes('No source-linked Meta posts'));
const fixture=[{leader:'Bhupesh Baghel',platform:'Instagram',published_at:'2026-09-03',url:'https://www.instagram.com/p/TEST123_alpha/',text:'Test record for issue classification',topics:['Governance'],districts:['Raipur'],post_type:'photo'}];
E('metaPaste').value=JSON.stringify(fixture);
E('metaImportPaste').click();
assert.equal(E('metaLocalCount').textContent,'1','one locally imported post');
assert.equal(E('metaFilteredCount').textContent,'1 match','post appears in default feed');
assert.match(E('metaPostList').textContent,/User-supplied/,'post must be marked unverified');
assert.match(E('metaPostList').textContent,/Raipur/);
assert.equal(document.querySelectorAll('#metaPostList a[href^="https://www.instagram.com/p/"]').length,1);
assert.equal(JSON.parse(dom.window.localStorage.getItem('cg_meta_public_posts_local_v10')).length,1);
E('metaPlatform').value='Facebook';E('metaPlatform').dispatchEvent(new Event('input',{bubbles:true}));
assert.equal(E('metaFilteredCount').textContent,'0 matches');
E('metaClearFilters').click();
assert.equal(E('metaFilteredCount').textContent,'1 match');
E('metaPaste').value=JSON.stringify(fixture);E('metaImportPaste').click();
assert.equal(E('metaLocalCount').textContent,'1','duplicates not double-counted');
E('metaPaste').value=JSON.stringify([{...fixture[0],published_at:'2026-08-04',url:'https://www.instagram.com/p/TEST123_date/'}]);E('metaImportPaste').click();
assert.match(E('metaImportStatus').textContent,/rejected/i);
assert.equal(E('metaLocalCount').textContent,'1','outside-window record not imported');
E('metaPaste').value=JSON.stringify([{...fixture[0],url:'https://www.instagram.com/bhupeshbaghelinc/'}]);E('metaImportPaste').click();
assert.match(E('metaImportStatus').textContent,/rejected/i);
assert.equal(E('metaLocalCount').textContent,'1','profile link not accepted as post');
E('metaPaste').value=JSON.stringify([{...fixture[0],url:'https://example.com/p/test/'}]);E('metaImportPaste').click();
assert.match(E('metaImportStatus').textContent,/rejected/i);
assert.equal(E('metaLocalCount').textContent,'1','non-Meta domain rejected');
E('metaClearLocal').click();
assert.equal(E('metaLocalCount').textContent,'0');
assert.equal(JSON.parse(dom.window.localStorage.getItem('cg_meta_public_posts_local_v10')).length,0);
assert.equal(errors.length,0,'No JavaScript errors: '+errors.join('; '));
console.log('PASS: Meta separate tab, 20 identity slots, no invented posts, local imports, validation, deduplication and clearing');
