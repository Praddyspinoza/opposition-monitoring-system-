/** Optional local PDF smoke check. Usage: node validate_export.cjs APP_RUNTIME_DIR [OUTPUT_DIR]. */
const fs=require('fs'),path=require('path'),zlib=require('zlib');
const runtime=path.resolve(process.argv[2]||path.join(__dirname,'../..'));
const output=path.resolve(process.argv[3]||path.join(__dirname,'../work/pdf_validation'));
function readSnapshot(){
 for(const candidate of [path.join(runtime,'data-unpacked.json'),path.join(runtime,'../data-unpacked.json')]) if(fs.existsSync(candidate))return JSON.parse(fs.readFileSync(candidate,'utf8'));
 const loader=fs.readFileSync(path.join(runtime,'data.js'),'utf8');
 if(loader.includes('SENATE_PARTS')){
  const parts=new Map();
  for(const name of fs.readdirSync(runtime).filter(n=>/^data-\d\d\.js$/.test(n)).sort()){
   const m=fs.readFileSync(path.join(runtime,name),'utf8').match(/window\.SENATE_PARTS\[(\d+)\]\s*=\s*['"]([A-Za-z0-9+/=]+)['"]/);
   if(!m||parts.has(Number(m[1])))throw new Error('Invalid or duplicate runtime data chunk: '+name);
   parts.set(Number(m[1]),m[2]);
  }
  const keys=[...parts.keys()].sort((a,b)=>a-b);
  if(!keys.length||keys.some((n,i)=>n!==i))throw new Error('Runtime data chunks are missing.');
  return JSON.parse(zlib.gunzipSync(Buffer.from(keys.map(i=>parts.get(i)).join(''),'base64')).toString('utf8'));
 }
 const m=loader.match(/atob\(['"]([A-Za-z0-9+/=]+)['"]\)/);
 if(m)return JSON.parse(zlib.gunzipSync(Buffer.from(m[1],'base64')).toString('utf8'));
 return JSON.parse(loader.replace(/^window\.SENATE_DATA\s*=\s*/,'').replace(/;\s*$/,''));
}
(async()=>{
 const data=readSnapshot();
 const {jsPDF}=require(path.join(runtime,'vendor/jspdf.umd.min.js'));globalThis.jspdf={jsPDF};
 const moduleText=fs.readFileSync(path.join(runtime,'export.js'),'utf8');
 const {createDistrictPDF}=await import('data:text/javascript;base64,'+Buffer.from(moduleText).toString('base64'));
 fs.mkdirSync(output,{recursive:true});const reports=[];
 for(const id of [44,12]){
  const doc=createDistrictPDF(data,id);const bytes=Buffer.from(doc.output('arraybuffer'));
  fs.writeFileSync(path.join(output,`District_${id}_dossier.pdf`),bytes);
  reports.push({district:id,pages:doc.internal.getNumberOfPages(),bytes:bytes.length,metrics:data.census?.districts?.find(d=>d.district===id)?.metrics?.length,evidence:data.issueEvidence?.evidence?.filter(e=>e.district===id).length});
 }
 fs.writeFileSync(path.join(output,'report.json'),JSON.stringify(reports,null,2));console.log(JSON.stringify(reports));
})().catch(e=>{console.error(e.message);process.exit(1);});
