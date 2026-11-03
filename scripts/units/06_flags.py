"""Flag units that cannot be designated and set the estimation panel (dataset plan section 2b). Runs after
04_population.py and rewrites data/final/units.csv.

- non_admin: areas that are not municipalities or districts (Chiba's land of undetermined affiliation, and Indonesia's
  lakes, forest and reservoir units).
- fragment: a 0.17 km2 piece of Saitama City that gbOpen keeps as a separate unit (name filled from OSM as Saitama).
Flagged units stay in the table but leave the panel. The panel is every urban unit that is not a city-state and not
flagged; the size groups (quartiles of 2015 population) are recomputed on it.

argv[1] = data/final/units.csv
"""
import sys
from pathlib import Path

import pandas as pd

F = Path(sys.argv[1])
FLAGS = {
    "22064153B42729341445185": "non_admin",  # Chiba, 所属未定地 (land of undetermined affiliation)
    "22746128B15758871990616": "non_admin",  # Danau (lake), Sumatera Barat
    "22746128B58041142516585": "non_admin",  # Danau Toba (lake), Sumatera Utara
    "22746128B69994664325988": "non_admin",  # Hutan (forest), Jawa Tengah
    "22746128B76055711701199": "non_admin",  # Waduk Cirata (reservoir), Jawa Barat
    "22064153B20100015994007": "fragment",   # 0.17 km2 piece of Saitama City
}

t = pd.read_csv(F, dtype={"size_group": "Int64"})
assert set(FLAGS) <= set(t.unit_id)
t["unit_flag"] = t.unit_id.map(FLAGS)
t["in_panel"] = t.urban & ~t.city_state & t.unit_flag.isna()
t["size_group"] = pd.Series(pd.NA, index=t.index, dtype="Int64")
t.loc[t.in_panel, "size_group"] = pd.qcut(t.loc[t.in_panel, "pop2015"], 4, labels=[1, 2, 3, 4]).astype(int)
t.to_csv(F, index=False, float_format="%.6g")
print(t.unit_flag.value_counts().to_dict(), "|", int((t.urban & t.unit_flag.notna()).sum()), "flagged urban units removed |",
      int(t.in_panel.sum()), "panel units; size group bounds",
      t[t.in_panel].groupby("size_group").pop2015.agg(["min", "max"]).round(0).values.tolist())
