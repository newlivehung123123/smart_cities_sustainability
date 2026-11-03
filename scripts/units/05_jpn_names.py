"""Fill the Japanese unit names that the geoBoundaries gbOpen file leaves blank or as question marks (dataset plan
section 2b), so that designations can be matched by name.

Each such unit is looked up once through the OpenStreetMap Nominatim reverse geocoder at its representative point
(municipality zoom, one request every 1.5 seconds, as its usage policy asks), and the answer is kept. A name is accepted
only if Nominatim places the point in the unit's own prefecture and the OSM outline it returns overlaps the unit by at
least 90 percent of the unit's area.

argv[1] = data/interim/units, argv[2] = data/raw/boundaries. Writes jpn_name_fill.csv and the raw answers
(nominatim/jpn_*.json) into argv[2].
"""
import json, subprocess, sys, time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import shape

U, RAW = Path(sys.argv[1]), Path(sys.argv[2])
UA = "smart_cities_sustainability research script (github.com/newlivehung123123/smart_cities_sustainability)"
URL = ("https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=10&namedetails=1&polygon_geojson=1"
       "&accept-language=en&lat={lat:.6f}&lon={lon:.6f}")

units = gpd.read_parquet(U / "units.parquet")
jp = units[(units.iso3 == "JPN") & (units.name.isna() | units.name.astype(str).str.contains(r"\?"))]
d = RAW / "nominatim"
d.mkdir(exist_ok=True)
rows = []
for _, u in jp.iterrows():
    f = d / f"jpn_{u.unit_id}.json"
    if not f.exists():
        q = u.geometry.representative_point()
        out = subprocess.run(["curl", "-sSf", "-A", UA, "-m", "60", URL.format(lat=q.y, lon=q.x)],
                             capture_output=True, check=True).stdout
        f.write_bytes(out)
        time.sleep(1.5)
    a = json.loads(f.read_text())
    osm = gpd.GeoSeries([shape(a["geojson"])], crs=4326).to_crs(6933)[0]
    share = shapely.area(shapely.intersection(osm, gpd.GeoSeries([u.geometry], crs=4326).to_crs(6933)[0])) / (u.area_km2 * 1e6)
    pref = a.get("address", {}).get("province", a.get("address", {}).get("state", ""))
    nd = a.get("namedetails", {})
    rows.append({"unit_id": u.unit_id, "cluster_name": u.cluster_name, "name_filled": nd.get("name:en", a.get("name")),
                 "name_ja": nd.get("name:ja", nd.get("name")), "osm_type": a["osm_type"], "osm_id": a["osm_id"],
                 "osm_prefecture": pref, "overlap_share": round(share, 4),
                 "accepted": u.cluster_name.split()[0].lower() in pref.lower() and share >= 0.9})
t = pd.DataFrame(rows)
t.to_csv(RAW / "jpn_name_fill.csv", index=False)
print(t[["cluster_name", "name_filled", "name_ja", "overlap_share", "accepted"]].to_string())
print(int(t.accepted.sum()), "of", len(t), "accepted")
