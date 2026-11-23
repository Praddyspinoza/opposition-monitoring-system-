
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import json,sys,hashlib,math
BASE=RESEARCH_ROOT;OUT=BASE/'v5_data/handoff';GEO=BASE/'geography'
sys.path.insert(0,str(GEO/'geolibs'))
from shapely.geometry import shape, Polygon, MultiPolygon, GeometryCollection
from shapely.ops import transform,polylabel
from shapely.strtree import STRtree
from shapely import make_valid
from pyproj import CRS,Transformer

def polys(g):
 if isinstance(g,Polygon):return [g] if g.area>0 else []
 if isinstance(g,(MultiPolygon,GeometryCollection)):return [p for x in g.geoms for p in polys(x)]
 return []
def valid(g):
 if not g.is_valid:g=make_valid(g)
 pp=polys(g)
 return MultiPolygon(pp) if len(pp)>1 else pp[0] if pp else GeometryCollection()
proj4='+proj=aea +lat_1=40 +lat_2=45 +lat_0=42.5 +lon_0=-76 +datum=WGS84 +units=m +no_defs'
proj=Transformer.from_crs('EPSG:4326',CRS.from_proj4(proj4),always_xy=True)
raw=json.loads((GEO/'official_senate_districts.geojson').read_text())
state=json.loads((GEO/'official_state_shoreline.geojson').read_text())
sds=[(int(f['properties']['DISTRICT']),transform(proj.transform,valid(shape(f['geometry'])))) for f in raw['features']]
sds.sort(key=lambda d:d[0]);sg=transform(proj.transform,valid(shape(state['features'][0]['geometry'])))
bb=[sg.bounds]+[g.bounds for _,g in sds]
x0=min(b[0] for b in bb);y0=min(b[1] for b in bb);x1=max(b[2] for b in bb);y1=max(b[3] for b in bb)
W,H,PAD=1000,780,26;scale=min((W-2*PAD)/(x1-x0),(H-2*PAD)/(y1-y0));offx=(W-(x1-x0)*scale)/2;offy=(H-(y1-y0)*scale)/2
def xy(x,y):return ((x-x0)*scale+offx,(y1-y)*scale+offy)
def bounds(g):
 a,b,c,d=g.bounds;x,y=xy(a,d);return [round(v,3) for v in (x,y,(c-a)*scale,(d-b)*scale)]
def path(g):
 parts=[]
 for p in polys(g):
  for r in [p.exterior,*p.interiors]:
   coords=[xy(x,y) for x,y,*_ in r.coords];vals=[]
   for x,y in coords:
    s=f'{x:.3f},{y:.3f}'
    if not vals or s!=vals[-1]:vals.append(s)
   if len(vals)>=4:parts.append('M'+'L'.join(vals)+'Z')
 return ''.join(parts)
rows={i:{'district':i,'id':i,'bounds':bounds(g),'neighborhoods':[],'electionDistricts':[]} for i,g in sds}
nyc_raw=json.loads((OUT/'raw'/'nyc_senate_districts.geojson').read_text())
clip_sds=sorted([(int(f['properties']['st_sen_dist']),transform(proj.transform,valid(shape(f['geometry'])))) for f in nyc_raw['features']])
for i,g in clip_sds:
 rows[i].update(detailedPath=path(g.simplify(3,preserve_topology=True)),detailedBounds=bounds(g),detailedBoundaryScope='NYC portion of Senate district' if i in [34,36] else 'Senate district within NYC',detailedBoundarySource='NYC_SD_26C')
tree=STRtree([g for _,g in clip_sds]);validation={'sourceCounts':{},'intersections':{},'unassignedSourceFeatures':{},'allLabelPointsWithinClippedGeometry':True,'retainedFragmentsOutsideSenate':0,'repairedSourceFeatures':{},'minAreaM2':{'neighborhoods':100,'electionDistricts':1},'minShareOfSourceArea':0.001}
plotdata={}
for layer,file,key in [('neighborhoods','nyc_nta2020','nta2020'),('electionDistricts','nyc_election_districts','elect_dist')]:
 src=json.loads((OUT/'raw'/f'{file}.geojson').read_text());validation['sourceCounts'][layer]=len(src['features']);unassigned=[];cnt=0;repaired=0
 for f in src['features']:
  props=f['properties'];rawg=shape(f['geometry']);repaired+=not rawg.is_valid;g=transform(proj.transform,valid(rawg));assigned=0
  for idx in tree.query(g,predicate='intersects'):
   sd,sdg=clip_sds[idx];clip=valid(g.intersection(sdg));area=clip.area
   if area<(1 if layer=='electionDistricts' else 100) or area/g.area<0.001:continue
   # SVG is for display; keep the authoritative intersections and their area calculation unsimplified.
   display=clip.simplify(3 if layer=='electionDistricts' else 5,preserve_topology=True)
   land=max(polys(clip),key=lambda p:p.area);p=polylabel(land,tolerance=5)
   if not clip.covers(p):p=land.representative_point()
   assert clip.covers(p)
   record={'id':str(props[key]),'path':path(display),'position':[round(v,3) for v in xy(p.x,p.y)],'bounds':bounds(clip),'areaKm2':round(area/1e6,5),'shareOfSourceAreaPct':round(area/g.area*100,2),'partial':area/g.area<0.995}
   if layer=='neighborhoods':record.update(name=props['ntaname'],borough=props['boroname'],typeCode=props['ntatype'],kind='Neighborhood tabulation area' if props['ntatype']=='0' else 'Special-area tabulation area',communityDistrict=props['cdta2020'],communityDistrictName=props['cdtaname'])
   else:
    ed=str(props['elect_dist']).zfill(5);record.update(id=ed,assemblyDistrict=int(ed[:-3]),electionDistrict=int(ed[-3:]),name=f'AD {int(ed[:-3])} · ED {int(ed[-3:])}')
   rows[sd][layer].append(record);assigned+=1;cnt+=1
   if sd in [12,15,17,47]:plotdata.setdefault(sd,[]).append((layer,record,display))
  if not assigned:unassigned.append(str(props[key]))
 validation['intersections'][layer]=cnt;validation['unassignedSourceFeatures'][layer]=unassigned;validation['repairedSourceFeatures'][layer]=repaired
 print(layer,cnt,'intersections; unassigned',len(unassigned),flush=True)
for r in rows.values():
 r['neighborhoods'].sort(key=lambda x:(x['typeCode']!='0',-x['areaKm2']))
 r['electionDistricts'].sort(key=lambda x:x['id'])
 r['coverage']='NYC boundaries available' if r['neighborhoods'] else 'Outside NYC dataset coverage'
 r['neighborhoodCount']=sum(x['typeCode']=='0' for x in r['neighborhoods'])
 r['specialAreaCount']=sum(x['typeCode']!='0' for x in r['neighborhoods'])
 r['electionDistrictCount']=len(r['electionDistricts'])
 r['neighborhoodNames']=[x['name'] for x in r['neighborhoods'] if x['typeCode']=='0']
sources=[{'id':'NYC_SD_26C','title':'State Senate Districts, NYC shoreline, version 26c','publisher':'NYC Department of City Planning','url':'https://data.cityofnewyork.us/City-Government/State-Senate-Districts/afns-vxeu','dataUrl':'https://data.cityofnewyork.us/resource/afns-vxeu.geojson?$limit=1000','sourceUpdatedAt':'2026-11-02','retrievedAt':'2026-11-23','features':28},{'id':'NYC_NTA_26C','title':'2020 Neighborhood Tabulation Areas (NTAs), version 26c','publisher':'NYC Department of City Planning / NYC Open Data','url':'https://data.cityofnewyork.us/City-Government/2020-Neighborhood-Tabulation-Areas-NTAs-/9nt8-h7nd','dataUrl':'https://data.cityofnewyork.us/resource/9nt8-h7nd.geojson?$limit=1000','sourceUpdatedAt':'2026-11-02','retrievedAt':'2026-11-23','features':262},{'id':'NYC_ED_26C','title':'Election Districts, version 26c','publisher':'NYC Department of City Planning, from NYC Board of Elections','url':'https://data.cityofnewyork.us/City-Government/Election-Districts/wwxk-38u4','dataUrl':'https://data.cityofnewyork.us/resource/wwxk-38u4.geojson?$limit=10000','sourceUpdatedAt':'2026-11-02','retrievedAt':'2026-11-23','features':4214},{'id':'NYS_SD_2022','title':'New York State Senate Districts, 2022 redistricting','publisher':'NYS ITS Geospatial Services','url':'https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/ArcGIS/rest/services/NYS_Senate_Districts/FeatureServer/0','retrievedAt':'2026-11-22'}]
obj={'metadata':{'title':'Official NYC neighborhood and election-district overlays for NY Senate districts','retrievedAt':'2026-11-23','boundaryVersion':'NYC 26c, updated 2026-11-02; NTA statistical definitions are 2020 vintage','viewBox':[0,0,W,H],'proj4':proj4,'projectionTransform':{'x0':x0,'y1':y1,'scale':scale,'offx':offx,'offy':offy},'fillRule':'evenodd','method':'Official NYC polygons projected and spatially clipped to matching NYC DCP 26c State Senate district polygons. The statewide atlas projection is retained exactly, while the detailed NYC Senate outline avoids mismatched shared edges from separately generalized statewide data. NTA fragments below 100 m², ED fragments below 1 m², or fragments below 0.1% of source feature area are suppressed; the lower ED threshold retains all 4,214 published precinct geometries, including very small shoreline features. SVG display simplified 5 m for NTAs and 3 m for EDs, preserving topology; areas calculated before simplification. Label points lie inside clipped polygons.','limits':['Neighborhood tabulation areas approximate neighborhoods; they are statistical areas, not definitive neighborhood borders.','Detailed overlays use the matching NYC DCP 26c Senate, NTA and ED representations. At transition from the statewide atlas, tiny outline differences can occur due to the atlas service generalization.','An ED can intersect multiple Senate districts. The clip does not allocate voters, population, or votes.','No election returns are supplied or inferred by this geometry dataset.','Non-NYC Senate districts are outside the coverage of these NYC datasets.'],'sources':sources,'districtsWithNycCoverage':[r['district'] for r in rows.values() if r['neighborhoods']]},'districts':list(rows.values())}
(OUT/'district_overlays.json').write_text(json.dumps(obj,separators=(',',':'),ensure_ascii=False))
validation['districtsWithNycCoverage']=obj['metadata']['districtsWithNycCoverage'];validation['outputBytes']=(OUT/'district_overlays.json').stat().st_size
validation['perDistrict']=[{k:r[k] for k in ['district','neighborhoodCount','specialAreaCount','electionDistrictCount']} for r in rows.values() if r['neighborhoods']]
(OUT/'geography_validation.json').write_text(json.dumps(validation,indent=2))
# Compact neighborhood-only file for fast initial render; full ED detail can be loaded separately.
obj['districts']=[{k:v for k,v in r.items() if k!='electionDistricts'} for r in rows.values()]
(OUT/'neighborhood_overlays.json').write_text(json.dumps(obj,separators=(',',':'),ensure_ascii=False))
# Inspection image for a dense Queens/Brooklyn district and Manhattan.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
fig,axes=plt.subplots(1,3,figsize=(16,7),facecolor='#0a0d10')
for ax,sd in zip(axes,[12,17,47]):
 ax.set_facecolor('#0a0d10');sg=dict(clip_sds)[sd]
 for layer,rec,geom in plotdata.get(sd,[]):
  for p in polys(geom):
   coords=[xy(x,y) for x,y in p.exterior.coords]
   ax.add_patch(MP(coords,facecolor='#293846' if layer=='neighborhoods' else 'none',edgecolor='#cdad68' if layer=='neighborhoods' else '#8391a0',linewidth=1 if layer=='neighborhoods' else .18,zorder=1 if layer=='neighborhoods' else 2))
 for p in polys(sg):ax.add_patch(MP([xy(x,y) for x,y in p.exterior.coords],fill=False,edgecolor='#f4ddb2',lw=1.4,zorder=3))
 x,y,w,h=bounds(sg);ax.set_xlim(x-w*.06,x+w*1.06);ax.set_ylim(y+h*1.06,y-h*.06);ax.set_aspect('equal');ax.axis('off')
 r=rows[sd];ax.set_title(f'SD {sd}  |  {r["neighborhoodCount"]} NTAs · {r["electionDistrictCount"]} EDs',color='#f4ddb2',fontsize=13)
fig.text(.05,.035,'Official NYC 26c boundaries clipped to official Senate districts · Neighborhoods in gold, election districts in silver · No vote data implied',color='#c6cdd5',fontsize=10)
fig.savefig(OUT/'geography_preview.png',dpi=140,facecolor=fig.get_facecolor(),bbox_inches='tight')
print(json.dumps({'coverage':validation['districtsWithNycCoverage'],'outputBytes':validation['outputBytes'],'initialFileBytes':(OUT/'neighborhood_overlays.json').stat().st_size}),flush=True)
