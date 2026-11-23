
# Packaged copy: resolve a configurable, isolated research working root.
from pathlib import Path as _ResearchPath
import sys as _research_sys
_research_package = next(p for p in _ResearchPath(__file__).resolve().parents if (p / 'research_paths.py').is_file())
_research_sys.path.insert(0, str(_research_package))
from research_paths import ROOT as RESEARCH_ROOT, RETRIEVED_AT as RESEARCH_RETRIEVED_AT

from pathlib import Path
import sys,json
sys.path.insert(0,str(RESEARCH_ROOT / 'geography/geolibs'))
from shapely.geometry import shape,Polygon,MultiPolygon,GeometryCollection
from shapely.ops import transform
from shapely import make_valid
from pyproj import Transformer
b=RESEARCH_ROOT
g=json.loads((b/'geography/atlas_geometry.json').read_text())
v=json.loads((b/'geography/geometry_validation.json').read_text())
x0,y0,x1,y1=v['planarExtentMetres'];sc=min(948/(x1-x0),728/(y1-y0));ox=(1000-(x1-x0)*sc)/2;oy=(780-(y1-y0)*sc)/2
proj=Transformer.from_crs('EPSG:4326',g['metadata']['proj4'],always_xy=True)
def polys(s):
 if isinstance(s,Polygon): return [s] if s.area else []
 return [p for part in s.geoms for p in polys(part)] if hasattr(s,'geoms') else []
def ring(r):return [[round((x-x0)*sc+ox,3),round((y1-y)*sc+oy,3)] for x,y,*_ in r.coords]
raw=json.loads((b/'geography/official_senate_districts.geojson').read_text())
for f in raw['features']:
 s=transform(proj.transform,make_valid(shape(f['geometry']))).simplify(65,preserve_topology=True)
 d=next(d for d in g['districts'] if d['id']==f['properties']['DISTRICT'])
 d['polygons']=[{'outer':ring(p.exterior),'holes':[ring(h) for h in p.interiors]} for p in polys(s)]
(b/'senate_v5/map-data.json').write_text(json.dumps(g,separators=(',',':')))
print('Prepared',len(g['districts']),'districts with actual projected polygons for 3D extrusion.')
