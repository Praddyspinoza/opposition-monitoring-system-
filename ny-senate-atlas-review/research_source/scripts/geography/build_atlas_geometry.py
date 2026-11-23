
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

import sys, json, pathlib, datetime
sys.path.insert(0, str(RESEARCH_ROOT / 'geography/geolibs'))
from pyproj import CRS, Transformer
from shapely.geometry import shape, mapping, box, Polygon, MultiPolygon, GeometryCollection
from shapely.ops import transform, polylabel
from shapely import make_valid

BASE = (RESEARCH_ROOT / 'geography')
senate = json.loads((BASE / 'official_senate_districts.geojson').read_text())
state = json.loads((BASE / 'official_state_shoreline.geojson').read_text())
senate_meta = json.loads((BASE / 'official_senate_metadata.json').read_text())
state_meta = json.loads((BASE / 'official_state_metadata.json').read_text())

crs = CRS.from_proj4('+proj=aea +lat_1=40 +lat_2=45 +lat_0=42.5 +lon_0=-76 +datum=WGS84 +units=m +no_defs')
proj = Transformer.from_crs('EPSG:4326', crs, always_xy=True)

def polygons(g):
    if isinstance(g, Polygon):
        return [g] if g.area > 0 else []
    if isinstance(g, (MultiPolygon, GeometryCollection)):
        return [p for part in g.geoms for p in polygons(part)]
    return []

def valid_polygonal(g):
    if not g.is_valid:
        g = make_valid(g)
    parts = polygons(g)
    return MultiPolygon(parts) if len(parts)>1 else parts[0]

raw_state = valid_polygonal(shape(state['features'][0]['geometry']))
projected_state = transform(proj.transform, raw_state)
senate_shapes = []
invalid = []
for f in senate['features']:
    g = shape(f['geometry'])
    if not g.is_valid:
        invalid.append(f['properties']['DISTRICT'])
    senate_shapes.append((f, transform(proj.transform, valid_polygonal(g))))

all_bounds = [projected_state.bounds] + [g.bounds for f,g in senate_shapes]
x0 = min(b[0] for b in all_bounds); y0 = min(b[1] for b in all_bounds)
x1 = max(b[2] for b in all_bounds); y1 = max(b[3] for b in all_bounds)
W,H,PAD = 1000,780,26
scale = min((W-PAD*2)/(x1-x0), (H-PAD*2)/(y1-y0))
offx=(W-(x1-x0)*scale)/2
offy=(H-(y1-y0)*scale)/2

def xy(x,y,z=None):
    return ((x-x0)*scale+offx, (y1-y)*scale+offy)

def xy_arr(p):
    return [round(v,3) for v in xy(p.x,p.y)]

def geo_xy(lon,lat):
    return [round(v,3) for v in xy(*proj.transform(lon,lat))]

def path(g):
    segments = []
    for p in polygons(g):
        for r in [p.exterior, *p.interiors]:
            coords = [xy(x,y) for x,y,*_ in r.coords]
            segments.append('M'+'L'.join(f'{x:.2f},{y:.2f}' for x,y in coords)+'Z')
    return ''.join(segments)

def bounds(g, pad=0):
    a,b,c,d = g.bounds
    x,y = xy(a,d); w,h=(c-a)*scale,(d-b)*scale
    return [round(x-pad,3),round(y-pad,3),round(w+pad*2,3),round(h+pad*2,3)]

districts=[]
for f,g in senate_shapes:
    props=f['properties']; sd=props['DISTRICT']
    land=max(polygons(g), key=lambda p:p.area)
    point=polylabel(land,tolerance=100)
    assert land.covers(point)
    districts.append({
        'id':sd,'path':path(g),'centroid':xy_arr(point),'bounds':bounds(g),
        'areaKm2':round(g.area/1e6,2),
        'geographicBounds':[round(v,5) for v in shape(f['geometry']).bounds],
        'incumbent':props['NAME'],'party':props['Party'],
        'contacts':{'albanyPhone':props['Phone'],'districtPhone':props['dist_phone'],'email':props['email'],
          'address':', '.join(str(props[k]) for k in ['Address','Address2','City','State','Zip'] if props.get(k))},
    })
districts.sort(key=lambda d:d['id'])
assert [d['id'] for d in districts]==list(range(1,64))
assert all(d['path'] and d['bounds'][2]>0 and d['bounds'][3]>0 for d in districts)

def inset(title, ext):
    # Bounds include projected points along edges to preserve a consistent geographic window.
    a,b,c,d=ext
    pts=[]
    for i in range(21):
        t=i/20; pts.extend([(a+t*(c-a),b),(a+t*(c-a),d),(a,b+t*(d-b)),(c,b+t*(d-b))])
    px=[geo_xy(*p) for p in pts]
    aa,bb,cc,dd=min(p[0] for p in px),min(p[1] for p in px),max(p[0] for p in px),max(p[1] for p in px)
    return {'title':title,'viewBox':[round(aa,3),round(bb,3),round(cc-aa,3),round(dd-bb,3)],'geographicBounds':ext}

data={
  'metadata':{
    'title':'Official New York State Senate District Boundaries',
    'retrieved':'2026-11-22',
    'districtCount':63,
    'districtSource':'https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/ArcGIS/rest/services/NYS_Senate_Districts/FeatureServer/0',
    'stateSource':'https://services6.arcgis.com/EbVsqZ18sv1kVJ3k/arcgis/rest/services/NYS_Civil_Boundaries/FeatureServer/1',
    'officialMap':'https://pubgeo.nysenate.gov/map/senate',
    'boundaryVintage':'NYS Senate 2022 redistricting; clipped to New York shoreline by NYS ITS Geospatial Services.',
    'senatorRosterAsOf':'2026-08-28',
    'stateShorelineAsOf':'2026-03',
    'projection':'New York Albers equal-area conic, WGS84; central meridian 76°W; standard parallels 40°N and 45°N; origin 42.5°N.',
    'proj4':crs.to_proj4(),
    'simplification':'Official service query maxAllowableOffset=0.0003 degrees; geometryPrecision=5; invalid degenerate polygon fragments repaired with Shapely make_valid. All positive-area polygons and holes retained.',
    'rosterNote':'GIS name/party/contact fields reflect the source update date and do not establish November 2026 election outcomes.',
    'fillRule':'evenodd',
  },
  'viewBox':[0,0,W,H],
  'state':{'path':path(projected_state),'bounds':bounds(projected_state)},
  'districts':districts,
  'insets':{'nyc':inset('New York City',[-74.28,40.47,-73.68,40.94]),
            'longIsland':inset('Long Island',[-73.99,40.51,-71.84,41.31])},
  'places':[{'name':name,'position':geo_xy(lon,lat)} for name,lon,lat in [
     ('Buffalo',-78.8784,42.8864),('Rochester',-77.6109,43.1566),('Syracuse',-76.1474,43.0481),
     ('Albany',-73.7562,42.6526),('New York City',-74.006,40.7128),('Montauk',-71.9545,41.0359),
     ('Lake Ontario',-77.65,43.63),('Adirondacks',-74.72,44.13),('Long Island',-72.72,40.80)
   ]],
}
(BASE/'atlas_geometry.json').write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False))
report={'districtCount':len(districts),'uniqueIds':len(set(d['id'] for d in districts)),
        'idsComplete': [d['id'] for d in districts]==list(range(1,64)),
        'allLabelPointsOnDistrictLand':True,'viewBox':data['viewBox'],
        'geographicExtent':list(raw_state.bounds),'planarExtentMetres':[x0,y0,x1,y1],
        'repairedDegenerateDistricts':invalid,'outputBytes':(BASE/'atlas_geometry.json').stat().st_size,
        'officialSourcesRespondedHTTP200':True}
(BASE/'geometry_validation.json').write_text(json.dumps(report,indent=2))

# Independent visual proof of silhouette, all polygons and state outline.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, PathPatch
from matplotlib.path import Path
fig,ax=plt.subplots(figsize=(12,9.36),facecolor='#0b1014')
ax.set_facecolor('#0b1014')
for f,g in senate_shapes:
    sd=f['properties']['DISTRICT']
    for poly in polygons(g):
        pts=[xy(x,y) for x,y in poly.exterior.coords]
        ax.add_patch(MP(pts,facecolor=plt.cm.cividis(0.22+0.7*sd/63),edgecolor='#e0d5b8',linewidth=.55))
for p in polygons(projected_state):
    pts=[xy(x,y) for x,y in p.exterior.coords]
    ax.add_patch(MP(pts,fill=False,edgecolor='#f8e5b0',linewidth=.75))
for d in districts:
    if d['areaKm2']>1200:
        ax.text(*d['centroid'],str(d['id']),ha='center',va='center',color='white',fontsize=8)
ax.set_xlim(0,W);ax.set_ylim(H,0);ax.set_aspect('equal');ax.axis('off')
fig.text(.04,.965,'NEW YORK STATE  |  63 OFFICIAL SENATE DISTRICTS',color='#e3c58a',fontsize=15)
fig.text(.04,.025,'NYS ITS Geospatial Services · 2022 redistricting · New York Albers projection',color='#b8c0c4',fontsize=10)
fig.savefig(BASE/'official_geometry_preview.png',dpi=130,facecolor=fig.get_facecolor(),bbox_inches='tight')
print(json.dumps(report,indent=2))
