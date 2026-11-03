"""Exhibits that use no outcome data: programmes by economy, data sources, map of designation status, first designations
by year and model.

python -I scripts/exhibits/01_design_exhibits.py data/final data/interim/units/units.parquet exhibits

Reads treatment.csv and the unit boundaries only. Tables are written as CSV and as Word files with three horizontal
lines (they open in Google Docs); figures are black and white, as PNG at 600 dpi and PDF.
"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.section import WD_ORIENT  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Cm, Pt  # noqa: E402

plt.rcParams.update({"font.family": "Arial", "font.size": 8, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                     "ytick.major.width": 0.6, "pdf.fonttype": 42})

PROGRAMME = {
    "ASEAN Smart Cities Network": "ASEAN Smart Cities Network",
    "Gerakan Menuju (100) Smart City (Kominfo Ditjen Aptika)": "Movement Towards 100 Smart Cities (Kominfo)",
    "MLIT Smart City Model Projects": "MLIT Smart City Model Projects",
    "Malaysia Smart City Framework pilot cities (KPKT)": "Smart City Framework pilot cities (KPKT)",
    "Municipal SDGs Model Projects; SDGs Future Cities": "SDGs Future Cities with a Municipal SDGs Model Project",
    "National Pilot Smart Cities (국가 시범도시)": "National Pilot Smart Cities",
    "SDGs Future Cities": "SDGs Future Cities",
    "Smart Challenge (스마트 챌린지)": "Smart Challenge",
    "Smart city logo (depa, Smart City Development Committee)": "Smart city certification (depa)",
}
MODEL = {"certification; implementation support": "Certification and implementation support"}
ORDER = ["Japan", "Thailand", "Hong Kong", "Singapore", "Brunei", "Cambodia", "Indonesia", "Laos", "Macau", "Malaysia",
         "Mongolia", "Myanmar", "Philippines", "South Korea", "Taiwan", "Timor-Leste", "Vietnam"]
# economies with no designated panel district, and the city-states (one unit each, not in the pooled panel)
OTHER = {
    "Hong Kong": ("Smart City Blueprint for Hong Kong", "Whole-city strategy", "2018", "1 (synthetic control)"),
    "Singapore": ("Smart Nation", "Whole-city strategy", "2015", "1 (synthetic control)"),
    "Macau": ("Smart city framework agreement with Alibaba Group", "Whole-city strategy", "2018", "Not estimated"),
    "Taiwan": ("Nationwide programme from 2018 that names no place", "", "", "0"),
    "Mongolia": ("No national list naming places", "", "", "0"),
    "Timor-Leste": ("ASEAN Smart Cities Network (Dili, 2026, after the panel)", "Network membership", "2026", "0"),
}

GREYS = {"implementation support": "#1a1a1a", "certification": "#7a7a7a", "network membership": "#c4c4c4"}


# ---------------------------------------------------------------- tables

def programmes_table(t):
    p = t[t["in_panel"]]
    panel_n = p.groupby("economy").size()
    d = p[p["first_treated"] <= 2024]
    g = d.groupby(["economy", "first_programme", "first_model"])["first_treated"].agg(["size", "min", "max"]).reset_index()
    rows = []
    for _, r in g.iterrows():
        years = f"{int(r['min'])}" if r["min"] == r["max"] else f"{int(r['min'])} to {int(r['max'])}"
        rows.append(dict(Economy=r["economy"], Programme=PROGRAMME[r["first_programme"]],
                         Model=MODEL.get(r["first_model"], r["first_model"].capitalize()),
                         Years=years, Designated=str(r["size"])))
    for econ, (prog, model, years, n) in OTHER.items():
        rows.append(dict(Economy=econ, Programme=prog, Model=model, Years=years, Designated=n))
    tab = pd.DataFrame(rows)
    tab["Panel districts"] = tab["Economy"].map(panel_n).fillna(0).astype(int).astype(str)
    tab.loc[tab["Economy"].isin(["Hong Kong", "Singapore", "Macau"]), "Panel districts"] = ""
    tab["_o"] = tab["Economy"].map({e: i for i, e in enumerate(ORDER)})
    tab = tab.sort_values(["_o", "Years", "Programme"]).drop(columns="_o")
    # economy name and panel count only on the first row of each economy
    first = ~tab["Economy"].duplicated()
    tab.loc[~first, ["Economy", "Panel districts"]] = ""
    total = dict(Economy="Total", Programme="", Model="", Years="2017 to 2024",
                 Designated=str(int((d["first_treated"] <= 2024).sum())), **{"Panel districts": str(len(p))})
    tab = pd.concat([tab, pd.DataFrame([total])], ignore_index=True)
    return tab.rename(columns={"Years": "First designated", "Designated": "Districts first designated"})


SOURCES = [
    ("Smart city designation", "Official programme lists of 17 economies, compiled for this study", "District",
     "2017 to 2024", "Treatment"),
    ("District boundaries", "geoBoundaries gbOpen ADM1 and ADM2 (ADM3 in the Philippines); OpenStreetMap (Hong Kong, "
     "Macau, South Korea)", "", "", "Units and clusters"),
    ("Population and urban centres", "GHS-POP and GHS-SMOD R2023A", "3 arc-seconds; 1 km", "2015",
     "Weights, urban districts, size groups"),
    ("PM2.5", "ACAG V6.GL.03 (Shen et al., 2024)", "0.01 degree", "1998 to 2024 annual; 2005 to 2024 monthly",
     "Outcome"),
    ("NO2", "ACAG SatNO2 V4.GL.01 (Yan et al., 2026)", "0.01 degree", "2005 to 2024 monthly", "Outcome"),
    ("Weather", "TerraClimate monthly temperature, precipitation and wind (Abatzoglou et al., 2018)", "1/24 degree",
     "2005 to 2024", "Covariates"),
    ("Fire detections", "NASA FIRMS MODIS Collection 6.1", "1 km", "2005 to 2024", "Covariates"),
    ("Night-time light", "Harmonised DMSP and VIIRS series, version 10 (Li et al., 2020)", "30 arc-seconds",
     "2005 to 2024", "RQ2 outcome, synthetic control predictor"),
    ("Built-up area", "GHS-BUILT-S R2023A", "30 arc-seconds", "2015", "Synthetic control predictor"),
    ("Income group", "World Bank historical income classifications", "Economy", "2017 to 2024", "Heterogeneity"),
]


def border(cell, edges, size=8):
    tcPr = cell._tc.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders")
        tcPr.append(b)
    for e in edges:
        el = OxmlElement(f"w:{e}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:color"), "000000")
        b.append(el)


def write_docx(tab, title, note, path, landscape=False):
    doc = Document()
    sec = doc.sections[0]
    if landscape:
        sec.orientation = WD_ORIENT.LANDSCAPE
        sec.page_width, sec.page_height = sec.page_height, sec.page_width
    for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(sec, m, Cm(2.0))
    style = doc.styles["Normal"]
    style.font.name, style.font.size = "Times New Roman", Pt(10)
    doc.add_paragraph().add_run(title).bold = True
    t = doc.add_table(rows=len(tab) + 1, cols=tab.shape[1])
    for j, c in enumerate(tab.columns):
        cell = t.cell(0, j)
        cell.text = c
        cell.paragraphs[0].runs[0].bold = True
        border(cell, ["top"], 12)
        border(cell, ["bottom"], 6)
    for i, row in enumerate(tab.itertuples(index=False), start=1):
        for j, v in enumerate(row):
            t.cell(i, j).text = str(v)
            if i == len(tab):
                border(t.cell(i, j), ["bottom"], 12)
    doc.add_paragraph(note).runs[0].font.size = Pt(9)
    doc.save(path)


# ---------------------------------------------------------------- figures

def map_figure(t, units_path, out):
    g = gpd.read_parquet(units_path, columns=["unit_id", "iso3", "geometry"])
    g = g.merge(t[["unit_id", "in_panel", "first_treated"]], on="unit_id", how="left")
    g["geometry"] = g.geometry.simplify(0.01, preserve_topology=True)
    designated = g["in_panel"] & (g["first_treated"] <= 2024)
    panel = g["in_panel"] & ~designated
    city = g["iso3"].isin(["SGP", "HKG", "MAC"])
    fig, ax = plt.subplots(figsize=(6.5, 6.6))
    g[~g["in_panel"] & ~city].plot(ax=ax, color="white", edgecolor="#bdbdbd", linewidth=0.1)
    g[panel].plot(ax=ax, color="#a6a6a6", edgecolor="white", linewidth=0.05)
    g[designated].plot(ax=ax, color="#1a1a1a", edgecolor="white", linewidth=0.05)
    g[city].plot(ax=ax, color="white", edgecolor="#1a1a1a", linewidth=0.3)
    # labels sit in open sea: Singapore's in the South China Sea north of the Natuna Islands
    for iso, name, x, y in (("SGP", "Singapore", 105.6, 6.2), ("HKG", "Hong Kong", 115.8, 20.0)):
        c = g[g["iso3"] == iso].geometry.iloc[0].representative_point()
        ax.plot(c.x, c.y, marker="o", ms=5, mfc="white", mec="#1a1a1a", mew=0.9, zorder=5)
        ax.annotate(name, (c.x, c.y), (x, y), fontsize=7, ha="left", va="bottom",
                    arrowprops=dict(arrowstyle="-", lw=0.5, color="#1a1a1a", shrinkA=1, shrinkB=3))
    ax.set_xlim(88, 149)
    ax.set_ylim(-11.5, 53)
    ax.set_axis_off()
    handles = [plt.Rectangle((0, 0), 1, 1, fc="#1a1a1a", ec="none"),
               plt.Rectangle((0, 0), 1, 1, fc="#a6a6a6", ec="none"),
               plt.Rectangle((0, 0), 1, 1, fc="white", ec="#bdbdbd", lw=0.5),
               plt.Line2D([], [], marker="o", ls="none", ms=5, mfc="white", mec="#1a1a1a", mew=0.9)]
    n_d, n_p = int(designated.sum()), int(panel.sum())
    fig.legend(handles, [f"Urban district, designated by 2024 ({n_d:,})", f"Urban district, not designated by 2024 "
                         f"({n_p:,})", "District outside the panel", "City-state (synthetic control)"],
               loc="lower center", ncol=2, frameon=False, fontsize=7, handlelength=1.4, columnspacing=2.0,
               bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(out / f"figure1_designation_map.{ext}", dpi=600, bbox_inches="tight")
    plt.close(fig)


def cohort_figure(t, out):
    d = t[t["in_panel"] & (t["first_treated"] <= 2024)].copy()
    d["model"] = d["first_model"].map(lambda m: "implementation support" if "implementation support" in m else m)
    c = d.groupby(["first_treated", "model"]).size().unstack(fill_value=0).reindex(columns=list(GREYS))
    c.index = c.index.astype(int)
    c.to_csv(out / "figureS1_first_designations.csv")
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    bottom = np.zeros(len(c))
    for m, col in GREYS.items():
        ax.bar(c.index, c[m], bottom=bottom, color=col, edgecolor="white", linewidth=1.0, width=0.7,
               label=m.capitalize())
        bottom += c[m].to_numpy()
    for x, tot in zip(c.index, bottom):
        ax.text(x, tot + 4, f"{int(tot)}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(c.index)
    ax.set_xlabel("Year of first designation")
    ax.set_ylabel("Urban districts first designated")
    ax.set_ylim(0, bottom.max() * 1.15)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False, fontsize=7, loc="upper right")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out / f"figureS1_first_designations.{ext}", dpi=600, bbox_inches="tight")
    plt.close(fig)


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    final, units_path, ex = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    (ex / "tables").mkdir(parents=True, exist_ok=True)
    (ex / "figures").mkdir(parents=True, exist_ok=True)
    t = pd.read_csv(final / "treatment.csv", dtype={"unit_id": str})

    tab1 = programmes_table(t)
    tab1.to_csv(ex / "tables" / "table1_programmes.csv", index=False)
    write_docx(tab1, "Table I. Smart city programmes and designated urban districts by economy",
               "Note. Urban districts of the pooled panel. A district designated by more than one programme is counted "
               "under the programme of its first designation, and a first year with both certification and "
               "implementation support counts as implementation support in the comparison of models. First designated "
               "is the year of the designation if it fell in January to June and the following year otherwise. "
               "Singapore and Hong Kong are one unit each and are estimated by synthetic control. Macau is not "
               "estimated. Source. Designation lists compiled for this study.",
               ex / "tables" / "table1_programmes.docx", landscape=True)
    tab2 = pd.DataFrame(SOURCES, columns=["Variable", "Source", "Grid", "Years", "Use"])
    tab2.to_csv(ex / "tables" / "tableS1_data_sources.csv", index=False)
    write_docx(tab2, "Table S1. Data sources",
               "Note. Gridded products are averaged over each district with 2015 population weights. ACAG is the "
               "Atmospheric Composition Analysis Group.",
               ex / "tables" / "tableS1_data_sources.docx", landscape=True)
    cohort_figure(t, ex / "figures")
    map_figure(t, units_path, ex / "figures")
    print(tab1.to_string())


if __name__ == "__main__":
    main()
