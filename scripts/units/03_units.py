"""Combine the boundary files into one table of district units with cluster, area and urban flag (dataset plan section 2b).

Each unit gets the cluster (ADM1; Philippine province; the city-state itself) with which it shares the most area, its
area, and its overlap with the 2015 urban centres. Cluster files are those chosen in 01b_clusters.py; a unit that meets
no cluster (an islet missing from the cluster file) takes the nearest one and is flagged cluster_rule = "nearest". Areas and overlaps are computed on the WGS84 ellipsoidal equal-area
grid (EPSG:6933). A unit is urban if it overlaps an urban centre by more than 1 m2; the threshold only removes numerical
noise, since unit borders and the 1 km grid edges of the centres never coincide. Population columns are added by
04_population.py.

argv[1] = data/interim/units, argv[2] = data/raw/boundaries/boundary_sources.csv (cluster_sources.csv is read from the
same folder). Writes units.parquet into argv[1].
"""
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

U, SRC = Path(sys.argv[1]), Path(sys.argv[2])
EA = 6933
TOL_KM2 = 1e-6
CITY_STATES = {"SGP", "HKG", "MAC"}


def polygonal(geoms):
    """make_valid after reprojection, keeping only the polygon parts."""
    out = shapely.make_valid(geoms)
    bad = ~np.isin(shapely.get_type_id(out), [3, 6])
    out[bad] = [shapely.unary_union([p for p in shapely.get_parts(g) if p.geom_type in ("Polygon", "MultiPolygon")])
                for g in out[bad]]
    assert shapely.is_valid(out).all() and not shapely.is_empty(out).any()
    return out


def overlaps(a, b):
    """Every pair (i in a, j in b) whose areas meet, with the shared area in km2."""
    i, j = shapely.STRtree(b).query(a, predicate="intersects")
    km2 = shapely.area(shapely.intersection(a[i], b[j])) / 1e6
    return pd.DataFrame({"i": i, "j": j, "km2": km2})


src = pd.read_csv(SRC)
chosen = pd.read_csv(SRC.with_name("cluster_sources.csv")).query("chosen").set_index("iso3")
uc = gpd.read_parquet(U / "urban_centres_2015.parquet")
uc_ea = polygonal(uc.to_crs(EA).geometry.values)

parts = []
for iso, rows in src.groupby("iso3", sort=False):
    unit = rows[rows.role == "unit"].iloc[0]
    g = gpd.read_parquet(U / unit.file)
    assert len(g) == unit.n_units
    g_ea = polygonal(g.to_crs(EA).geometry.values)
    t = pd.DataFrame({"unit_id": g.shapeID.values, "economy": unit.economy, "iso3": iso, "level": unit.level,
                      "name": g.shapeName.values, "city_state": iso in CITY_STATES,
                      "area_km2": shapely.area(g_ea) / 1e6})

    if iso in CITY_STATES:
        t["cluster_id"], t["cluster_name"], t["cluster_share"], t["cluster_rule"] = iso, unit.economy, 1.0, "city-state"
    else:
        c = gpd.read_parquet(U / chosen.loc[iso, "file"])
        c_ea = polygonal(c.to_crs(EA).geometry.values)
        ov = overlaps(g_ea, c_ea)
        best = ov.sort_values(["i", "km2"], ascending=[True, False]).drop_duplicates("i").set_index("i").reindex(t.index)
        far = ~best.km2.gt(0).values
        if far.any():
            best.loc[far, "j"] = shapely.STRtree(c_ea).nearest(g_ea[far])
            best.loc[far, "km2"] = 0.0
        j = best.j.astype(int).values
        t["cluster_id"], t["cluster_name"] = c.shapeID.values[j], c.shapeName.values[j]
        t["cluster_share"] = best.km2.values / t.area_km2.values
        t["cluster_rule"] = np.where(far, "nearest", "overlap")
        for k in np.where(far)[0]:
            print(f"{iso}: {t.name[k]} ({t.area_km2[k]:.2f} km2) meets no cluster, nearest is {t.cluster_name[k]}", flush=True)
        print(f"{iso}: units {len(g)}, clusters used {t.cluster_id.nunique()} of {len(c)}, area units/clusters "
              f"{t.area_km2.sum() / (shapely.area(c_ea).sum() / 1e6):.4f}, lowest cluster share "
              f"{t.cluster_share.min():.3f}", flush=True)

    ov = overlaps(g_ea, uc_ea)
    ov = ov[ov.km2 > TOL_KM2]
    t["uc_overlap_km2"] = ov.groupby("i").km2.sum().reindex(t.index, fill_value=0.0).values
    t["n_uc"] = ov.groupby("i").size().reindex(t.index, fill_value=0).values
    main = ov.sort_values(["i", "km2"], ascending=[True, False]).drop_duplicates("i").set_index("i").j
    t["uc_main"] = uc.uc_id.values[main.reindex(t.index).fillna(-1).astype(int)].astype(object)
    t.loc[t.n_uc == 0, "uc_main"] = None
    t["urban"] = t.n_uc > 0
    parts.append(gpd.GeoDataFrame(t, geometry=g.geometry.values, crs=4326))
    print(f"{iso}: {int(t.urban.sum())} of {len(t)} units urban", flush=True)

units = pd.concat(parts, ignore_index=True)
assert units.unit_id.is_unique
units = units[["unit_id", "economy", "iso3", "level", "name", "cluster_id", "cluster_name", "cluster_share", "cluster_rule", "city_state",
               "area_km2", "uc_overlap_km2", "n_uc", "uc_main", "urban", "geometry"]]
units.to_parquet(U / "units.parquet", compression="zstd")
print(len(units), "units;", int(units.urban.sum()), "urban;", units.economy.nunique(), "economies")
