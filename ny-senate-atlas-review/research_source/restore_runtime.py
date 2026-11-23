#!/usr/bin/env python3
"""Restore normalized research snapshots from an existing app, without executing JS.

Accepts data-unpacked.json, a runtime directory, or data.js. Supports split
window.SENATE_PARTS payloads, the earlier single atob payload, and plain JSON
assignment. Does not fetch the network or execute the copied research scripts.
"""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,re,shutil
PACKAGE=Path(__file__).resolve().parent

def load_runtime(location):
    location=Path(location).expanduser().resolve()
    if location.is_file() and location.suffix.lower()=='.json':
        raw=location.read_bytes();return json.loads(raw),[location],raw
    dirs=[location] if location.is_dir() else [location.parent]
    if location.is_dir():dirs += [location/'dist',location/'senate_v5',location/'senate_v5/dist']
    # Prefer a complete unpacked checkpoint, including the sibling of dist/.
    for directory in dirs+[p.parent for p in dirs]:
        candidate=directory/'data-unpacked.json'
        if candidate.is_file():
            raw=candidate.read_bytes();return json.loads(raw),[candidate],raw
    for directory in dirs:
        loader=directory/'data.js'
        if not loader.is_file():continue
        code=loader.read_text()
        if 'SENATE_PARTS' in code:
            indexed={};used=[]
            for part in sorted(directory.glob('data-[0-9][0-9].js')):
                matches=re.findall(r"window\.SENATE_PARTS\[(\d+)\]\s*=\s*['\"]([A-Za-z0-9+/=]+)['\"]",part.read_text())
                if len(matches)!=1:raise ValueError(f'Expected one encoded chunk in {part.name}')
                index,text=matches[0];index=int(index)
                if index in indexed:raise ValueError(f'Duplicate data chunk {index}')
                indexed[index]=text;used.append(part)
            if not indexed or sorted(indexed)!=list(range(len(indexed))):raise ValueError('Runtime data chunks are missing or not contiguous from zero.')
            packed=''.join(indexed[i] for i in range(len(indexed)))
            raw=gzip.decompress(base64.b64decode(packed,validate=True))
            return json.loads(raw),used+[loader],raw
        match=re.search(r"atob\(['\"]([A-Za-z0-9+/=]+)['\"]\)",code)
        if match:
            raw=gzip.decompress(base64.b64decode(match.group(1),validate=True));return json.loads(raw),[loader],raw
        match=re.search(r'window\.SENATE_DATA\s*=\s*',code)
        if match:
            value,end=json.JSONDecoder().raw_decode(code[match.end():])
            if code[match.end()+end:].strip().strip(';'):raise ValueError('Unexpected trailing content after JSON assignment.')
            raw=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode();return value,[loader],raw
    raise FileNotFoundError('Provide data-unpacked.json or a runtime folder containing data.js and every data-00.js, data-01.js, ... part.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',required=True,help='Path to data-unpacked.json, data.js or the app runtime directory')
    parser.add_argument('--output',default=str(PACKAGE/'work'),help='Isolated working root; default research_source/work')
    parser.add_argument('--overwrite',action='store_true',help='Replace existing working snapshots with this runtime edition')
    args=parser.parse_args();data,sourcefiles,raw=load_runtime(args.runtime)
    if not isinstance(data,dict) or not isinstance(data.get('elections',{}).get('districts'),list):raise ValueError('Input does not contain a valid SENATE_DATA snapshot.')
    out=Path(args.output).expanduser().resolve();writes={}
    mapping={'geometry':'senate_v5/map-data.json','elections':'election_research/senate_elections_2026.json','finance':'finance_research/atlas_finance_normalized.json','directory':'election_research/district_counties_official.json','research':'dossier_research/district_enrichment_compact.json','issuePlan':'dossier_research/issues_corrected.json','handoff':'v5_data/handoff/normalized.json','census':'v5_data/census/normalized.json','issueEvidence':'v5_data/issues/normalized.json','overlays':'v5_data/handoff/district_overlays.json','profiles':'v5_data/issues/official_profiles.json','migrationFresh':'v5_data/handoff/fresh_migration.json'}
    for key,relative in mapping.items():
        if key in data:writes[relative]=data[key]
    if 'geometry' in data:writes['geography/atlas_geometry.json']=data['geometry']
    metadata=json.loads((PACKAGE/'metadata/snapshot_metadata.json').read_text())
    original_meta={x['originalPath']:x['meta'] for x in metadata['snapshots']}
    districts=data['elections']['districts']
    writes['election_research/senate_elections_2024.json']={'meta':original_meta.get('election_research/senate_elections_2024.json',{}),'districts':[x['history2024'] for x in districts if x.get('history2024')]}
    writes['election_research/senate_primaries_2026.json']={'meta':original_meta.get('election_research/senate_primaries_2026.json',{}),'contests':[c for x in districts for c in x.get('primaryElections',[])]}
    # Keep the already merged media records intact when the original build script re-merges its input files.
    research=data.get('research',{});research_districts=research.get('districts',[]) if isinstance(research,dict) else []
    writes['dossier_research/media_records.json']={'districts':[{'district':x['district'],'media_records':x.get('media_records',[])} for x in research_districts]}
    writes['dossier_research/candidate_media_records.json']={'districts':[]}
    issues=data.get('issueEvidence',{})
    if issues.get('legislation'):writes['v5_data/issues/official_legislation.json']={'meta':original_meta.get('v5_data/issues/official_legislation.json',{}),'legislation':issues['legislation']}
    if not data.get('profiles') and issues.get('profiles'):writes['v5_data/issues/official_profiles.json']={'meta':original_meta.get('v5_data/issues/official_profiles.json',{}),'profiles':issues['profiles']}
    if 'handoff' in data:
        writes['v5_data/handoff/master_plan_v5.txt']='\f'.join(p['text'] for p in data['handoff'].get('pages',[]))+'\f'
        writes['v5_data/handoff/migration_charts_data.json']={'charts':data['handoff'].get('migration',{}).get('charts',[]),'note':'Recovered exactly from the runtime handoff chart objects.'}
    # Small original reviewed ID mappings and historical audit reports can seed the work folder.
    for rootname in ['inputs','audits']:
        for p in (PACKAGE/rootname).rglob('*'):
            if p.is_file():writes[str(p.relative_to(PACKAGE/rootname))]=p.read_bytes()
    # Preserve official geography source/schema metadata at its expected working paths.
    for p in (PACKAGE/'metadata/geography').glob('*.json'):
        writes['geography/'+p.name]=p.read_bytes()
    encoded={rel:obj if isinstance(obj,bytes) else obj.encode() if isinstance(obj,str) else json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode() for rel,obj in writes.items()}
    conflicts=[rel for rel,b in encoded.items() if (out/rel).exists() and (out/rel).read_bytes()!=b]
    if conflicts and not args.overwrite:raise FileExistsError('Working files already differ; choose another --output or explicitly use --overwrite: '+', '.join(conflicts[:5]))
    for rel,b in encoded.items():
        target=out/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
    for rel in ['v5_data/census/raw','v5_data/handoff/raw','v5_data/handoff/charts','finance_research/raw','senate_v5/dist']:(out/rel).mkdir(parents=True,exist_ok=True)
    report={'runtimeSources':[str(p) for p in sourcefiles],'runtimeJsonBytes':len(raw),'runtimeJsonSha256':hashlib.sha256(raw).hexdigest(),'outputRoot':str(out),'restoredFileCount':len(encoded),'runtimeTopLevelKeys':list(data),'counts':{'districts':len(districts),'censusDistricts':len(data.get('census',{}).get('districts',[])),'issues':len(issues.get('issues',[])),'uniqueIssueRecords':len(issues.get('evidence',[])),'migrationCountySeries':len(data.get('migrationFresh',{}).get('countyPopulationChanges',[]))},'note':'Normalized snapshots restored; raw captures, source PDFs, original charts and portrait binaries were not reconstructed. Audit files retain their original dates.'}
    (out/'restore_manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
