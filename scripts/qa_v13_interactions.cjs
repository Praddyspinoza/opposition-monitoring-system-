#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const spawn=require('node:child_process').spawn;
const sleep=n=>new Promise(ok=>setTimeout(ok,n));
const chrome=['/usr/bin/google-chrome','/usr/bin/chromium','/usr/bin/chromium-browser'].find(x=>fs.existsSync(x));
if(!chrome){console.log('SKIP: Chrome unavailable');process.exit(0);}
const port=9300+(process.pid%400);
const html='file://'+path.resolve(__dirname,'../preview/v12/index.html');
const processChrome=spawn(chrome,['--headless=new','--no-sandbox','--disable-gpu','--disable-extensions',
 '--remote-allow-origins=*','--remote-debugging-port='+port,'--user-data-dir=/tmp/v13-qa-'+process.pid,
 '--window-size=1280,900',html],{stdio:'ignore'});
let socket;
let idx=0;
const callbacks=new Map();
async function connect(){
 let page;
 for(let i=0;i<70;i++){
  try{
   const res=await fetch('http://127.0.0.1:'+port+'/json');
   if(res.ok){page=(await res.json()).find(x=>x.type==='page'&&x.webSocketDebuggerUrl);if(page)break;}
  }catch(_){}
  await sleep(200);
 }
 assert(page,'Chrome debugger did not expose a page');
 socket=new WebSocket(page.webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
 socket.onmessage=e=>{
  const val=JSON.parse(e.data);
  if(val.id&&callbacks.has(val.id)){const ok=callbacks.get(val.id);callbacks.delete(val.id);ok(val);}
 };
}
function cmd(method,params={}){
 return new Promise((resolve,reject)=>{
  const id=++idx;
  callbacks.set(id,result=>result.error?reject(new Error(JSON.stringify(result.error))):resolve(result.result));
  socket.send(JSON.stringify({id,method,params}));
  setTimeout(()=>{if(callbacks.has(id)){callbacks.delete(id);reject(new Error('Timed out: '+method));}},9000);
 });
}
async function evaluate(expression){
 const value=await cmd('Runtime.evaluate',{expression,returnByValue:true});
 if(value.exceptionDetails)throw Error(value.exceptionDetails.text||'JS evaluation failed');
 return value.result.value;
}
async function main(){
 try{
  await connect();
  await cmd('Runtime.enable');
  let visible=false;
  for(let i=0;i<70;i++){
   visible=await evaluate("!!document.getElementById('v13Evidence') && document.querySelectorAll('[data-v13-kind=bjp]').length===10 && document.querySelectorAll('[data-v13-kind=opp]').length===10");
   if(visible)break;
   await sleep(150);
  }
  assert(visible,'Twenty leader nodes not present');
  const state=await evaluate("(()=>{function set(id,v){const s=document.getElementById(id);if(!s)throw Error('Missing '+id);s.value=v;s.dispatchEvent(new Event('change',{bubbles:true}));}set('v13Bjp','Vishnu Deo Sai');set('v13Opp','Bhupesh Baghel');set('v12FlowIssue','Governance');set('v13District','Raipur');const e=document.getElementById('v13Evidence');return {bjp:document.getElementById('v13Bjp').value,opp:document.getElementById('v13Opp').value,issue:document.getElementById('v12FlowIssue').value,district:document.getElementById('v13District').value,nodes:document.querySelectorAll('.v13-node-group.selected').length,visible:!!e.querySelector('.v13-evidence-grid'),summary:e.textContent.slice(0,500)};})()");
  assert.equal(state.bjp,'Vishnu Deo Sai');
  assert.equal(state.opp,'Bhupesh Baghel');
  assert.equal(state.issue,'Governance');
  assert.equal(state.district,'Raipur');
  assert.equal(state.nodes,4);
  assert(state.visible,'Evidence panel not expanded');
  for(const label of ['Vishnu Deo Sai','Bhupesh Baghel','Governance','Raipur'])assert(state.summary.includes(label));
  const reset=await evaluate("(()=>{document.getElementById('v13Reset').click();return [document.getElementById('v13Bjp').value,document.getElementById('v13Opp').value,document.getElementById('v12FlowIssue').value,document.getElementById('v13District').value,document.querySelectorAll('.v13-node-group.selected').length];})()");
  assert.deepEqual(reset,['all','all','all','all',0]);
  const clicked=await evaluate("(()=>{for(const [type,value] of [['bjp','Vishnu Deo Sai'],['opp','Bhupesh Baghel'],['issue','Governance'],['district','Raipur']]){const n=[...document.querySelectorAll('[data-v13-kind]')].find(x=>x.dataset.v13Kind===type&&x.dataset.v13Value===value);if(!n)throw Error('Missing clickable '+type+': '+value);n.dispatchEvent(new MouseEvent('click',{bubbles:true}));}return {nodes:document.querySelectorAll('.v13-node-group.selected').length,expanded:!!document.querySelector('#v13Evidence .v13-evidence-grid'),text:document.getElementById('v13Evidence').textContent.slice(0,500)};})()");
  assert.equal(clicked.nodes,4,'Four selected SVG nodes expected after direct clicking');
  assert(clicked.expanded,'SVG clicks must open source-backed evidence panel');
  assert(clicked.text.includes('Governance')&&clicked.text.includes('Raipur'),'Direct SVG clicks should update issue-region evidence');
  console.log('PASS: 10 BJP + 10 opposition nodes; four dropdown filters and direct SVG node clicks; evidence expansion; clear all');
 }finally{try{socket?.close();}catch(_){}processChrome.kill('SIGTERM');}
}
main().catch(e=>{console.error('FAIL browser interactions: '+e.stack);processChrome.kill('SIGTERM');process.exitCode=1;});
