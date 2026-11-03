"""Exhibits of the results: Table II (pooled effects and parallel-trends checks), Table III (programme models and focal
economies), Figure 2 (event study), Figure 3 (robustness checks) and supplement tables S2 to S4.

python -I scripts/exhibits/02_results_exhibits.py outputs/analysis exhibits

Reads the CSV files written by scripts/analysis/03_estimate.py to 06_trends.py. Effects are shown in percent,
100 x (exp(tau) - 1), with 95 percent confidence intervals in parentheses and p-values in square brackets. Tables are
written as CSV and as Word files with three horizontal lines; figures are black and white, as PNG at 600 dpi and PDF.
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.section import WD_ORIENT  # noqa: E402
from docx.shared import Cm, Pt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importlib import import_module  # noqa: E402

design = import_module("01_design_exhibits")
border = design.border

plt.rcParams.update({"font.family": "Arial", "font.size": 8, "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                     "ytick.major.width": 0.6, "pdf.fonttype": 42})
INK, MID, LIGHT = "#1a1a1a", "#7a7a7a", "#c4c4c4"
MINUS = "−"
NAMES = {"ln_pm25": "PM2.5", "ln_no2": "NO2"}
OUT = ("ln_pm25", "ln_no2")


# ---------------------------------------------------------------- formatting

def pct(x):
    return 100 * np.expm1(np.asarray(x, float))


def num(x, d=2):
    s = f"{x:,.{d}f}"
    return s.replace("-", MINUS) if not s.lstrip("-").strip("0.,") == "" else s.lstrip("-")


def pval(p):
    if not np.isfinite(p):
        return ""
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def eff(est, lo, hi, p=np.nan):
    s = f"{num(pct(est))} ({num(pct(lo))} to {num(pct(hi))})"
    return s + (f" [{pval(p)}]" if np.isfinite(p) else "")


def get(df, **kw):
    m = np.ones(len(df), bool)
    for k, v in kw.items():
        m &= (df[k].fillna("") == v).to_numpy()
    r = df[m]
    if len(r) != 1:
        raise KeyError(f"{kw}: {len(r)} rows")
    return r.iloc[0]


# ---------------------------------------------------------------- tables

def write_table(rows, header, title, note, path, landscape=False, widths=None):
    """rows: ("panel", label) for a panel heading over the full width, ("span", label, value) for a value spanning
    every column after the label, or a list of cell strings."""
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
    k = len(header)
    t = doc.add_table(rows=len(rows) + 1, cols=k)
    for j, c in enumerate(header):
        cell = t.cell(0, j)
        cell.text = c
        cell.paragraphs[0].runs[0].bold = True
        border(cell, ["top"], 12)
        border(cell, ["bottom"], 6)
    for i, r in enumerate(rows, start=1):
        if isinstance(r, tuple) and r[0] == "panel":
            cell = t.cell(i, 0).merge(t.cell(i, k - 1))
            cell.text = r[1]
            cell.paragraphs[0].runs[0].italic = True
        elif isinstance(r, tuple) and r[0] == "span":
            t.cell(i, 0).text = r[1]
            t.cell(i, 1).merge(t.cell(i, k - 1)).text = r[2]
        else:
            for j, v in enumerate(r):
                t.cell(i, j).text = str(v)
        if i == len(rows):
            for j in range(k):
                border(t.cell(i, j), ["bottom"], 12)
    if widths:
        for j, w in enumerate(widths):
            for cell in t.columns[j].cells:
                cell.width = Cm(w)
    doc.add_paragraph(note).runs[0].font.size = Pt(9)
    doc.save(path)


def flat(rows, header):
    """CSV form of a panelled table: panel headings become a column."""
    out, panel = [], ""
    for r in rows:
        if isinstance(r, tuple) and r[0] == "panel":
            panel = r[1]
        elif isinstance(r, tuple):
            out.append(dict(Panel=panel, **dict(zip(header, [r[1], r[2]]))))
        else:
            out.append(dict(Panel=panel, **dict(zip(header, r))))
    return pd.DataFrame(out)


def table2(a):
    main = a["results_main"].query("estimand == 'h0_5'").set_index("outcome")
    mde = a["mde_share"].set_index("outcome")
    pre = a["pretrend"].set_index("outcome")
    hon = a["honest"]
    est = a["robust_estimators"]
    tr = a["trends"]
    rh = a["robust_honest"]
    rows = [("panel", "Panel A. Effect of designation, years 0 to 5 after designation (RQ1)")]
    rows.append(["Imputation estimator"] + [eff(main.loc[y, "est"], main.loc[y, "ci_lo"], main.loc[y, "ci_hi"],
                                                main.loc[y, "p_holm"]) for y in OUT])
    rows.append(["Equivalence test, p"] + [pval(main.loc[y, "tost_p"]) for y in OUT])
    rows.append(["Minimum detectable effect"] + [num(mde.loc[y, "mde_pct"]) for y in OUT])
    rows.append(["Treated district-years"] + [f"{int(main.loc[y, 'n_obs']):,}" for y in OUT])
    rows.append(("panel", "Panel B. Checks of parallel trends"))
    rows.append(["Pre-designation test, F [p]"] + [f"{num(pre.loc[y, 'F'])} [{pval(pre.loc[y, 'p'])}]" for y in OUT])

    def r(df, y, **kw):
        x = get(df, outcome=y, **kw)
        return eff(x["est"], x["ci_lo"], x["ci_hi"], x["p"])
    rows.append(["Sun and Abraham, year before designation as reference"] +
                [r(rh, y, check="Sun and Abraham") for y in OUT])
    rows.append(["Callaway and Sant'Anna, doubly robust"] +
                [r(est, y, check="Callaway and Sant'Anna, doubly robust") for y in OUT])
    rows.append(["Entropy balancing on pre-designation outcomes"] +
                [r(est, y, check="entropy balancing") for y in OUT])
    rows.append(["District-specific linear trends"] +
                [r(tr, y, model="district trends", estimand="h0_5") for y in OUT])
    bd = hon[hon["mbar"].isna()].set_index("outcome")["breakdown"]
    rows.append(["Breakdown value of M"] + [("none" if not np.isfinite(bd[y]) else num(bd[y])) for y in OUT])
    h1 = a["h1"].iloc[0]
    rows.append(("panel", "Panel C. Difference between pollutants (H1) and night-time light, 2012 to 2024 (H2)"))
    rows.append(("span", "NO2 effect minus PM2.5 effect, log points x 100",
                 f"{num(100 * h1['diff'])} ({num(100 * h1['ci_lo'])} to {num(100 * h1['ci_hi'])})"))
    rq2 = a["rq2"].query("estimand == 'h0_5'").set_index("outcome")
    for y, lab in (("ln_ntl", "Night-time light"), ("ln_pm25_per_ntl", "PM2.5 relative to night-time light")):
        x = rq2.loc[y]
        rows.append(("span", lab, eff(x["est"], x["ci_lo"], x["ci_hi"], x["p"])))
    header = ["", "PM2.5", "NO2"]
    note = ("Note. Effects in percent with 95 percent confidence intervals in parentheses and p-values in square "
            "brackets. Standard errors are clustered by 328 first-level administrative units. The p-values in the "
            "first row are Holm-adjusted over the two pollutants. The equivalence test asks whether the effect lies "
            "between " + MINUS + "5 and 5 percent, and a p-value below 0.05 means that the effect does. The minimum "
            "detectable effect is in percent at 80 percent power, from 500 placebo designations. The "
            "pre-designation test is the joint test of eight pre-designation indicators (Borusyak et al., 2024). "
            "The breakdown value is the largest M of Rambachan and Roth (2023) at which the confidence set excludes "
            "zero, and none means that the confidence set includes zero at M = 0. District-specific linear trends "
            "is an exploratory check that was not in the analysis plan. In Panel C the H1 interval comes from 999 "
            "cluster bootstrap draws, and the night-time light rows use the harmonised series of Li et al. (2020). Source. ACAG "
            "PM2.5 and NO2 estimates, designation lists compiled for this study, authors' estimates.")
    return rows, header, note


def table3(a):
    rq3 = a["rq3"].set_index(["model", "outcome"])
    wald = a["rq3_wald"].set_index("outcome")
    focal = a["focal"].set_index(["estimand", "outcome"])
    syn = a["synth_results"]
    rows = [("panel", "Panel A. Programme model, pooled panel (RQ3)")]
    for m in ("implementation support", "certification", "network membership"):
        x = [rq3.loc[(m, y)] for y in OUT]
        rows.append([m.capitalize(), f"{int(x[0]['n_treated_clusters'])}"] +
                    [eff(r["est"], r["ci_lo"], r["ci_hi"], r["p_wild"] if np.isfinite(r["p_wild"]) else r["p"])
                     for r in x])
    rows.append(["Wald test of equal effects, p", ""] + [pval(wald.loc[y, "p"]) for y in OUT])
    rows.append(("panel", "Panel B. Focal economies"))
    for iso, lab in (("JPN", "Japan"), ("THA", "Thailand")):
        cells = []
        for y in OUT:
            r = focal.loc[(f"{iso}_h0_5", y)]
            p = r["p_wild"] if np.isfinite(r["p_wild"]) else r["p"]
            cells.append(eff(r["est"], r["ci_lo"], r["ci_hi"], p))
        rows.append([lab, str(int(focal.loc[(f"{iso}_h0_5", OUT[0]), "n_treated_clusters"]))] + cells)
    for unit, lab in (("SGP", "Singapore"), ("HKG", "Hong Kong")):
        cells = []
        for y in OUT:
            r = get(syn, check="main", unit=unit, outcome=y, method="ascm")
            cells.append(f"{num(r['pct'])} [{pval(r['p_ratio'])}]")
        rows.append([lab + ", augmented synthetic control", "1"] + cells)
    header = ["", "Treated first-level units", "PM2.5", "NO2"]
    note = ("Note. Effects in percent over years 0 to 5 after designation, with 95 percent confidence intervals in "
            "parentheses and p-values in square brackets. Panel A fits the imputation estimator on a separate sample "
            "for every programme model, and the Wald test uses 999 cluster bootstrap draws. Japan and Thailand are "
            "the means of the district effects in each economy from the pooled fit. Where the designated districts "
            "lie in fewer than 30 first-level units (network membership and Thailand), the p-value comes from the "
            "wild cluster bootstrap with Webb weights and 9,999 draws, and the interval still comes from the "
            "clustered standard error, so the interval and the p-value can disagree. Singapore (designated in 2015) and Hong Kong (2018) are estimated by "
            "the augmented synthetic control method over all years after designation, with no confidence interval, "
            "and the p-value is the rank of the ratio of post- to pre-designation prediction error among placebo "
            "runs that treat each donor district as designated. Source. Estimates of this study.")
    return rows, header, note


# ---------------------------------------------------------------- figures

def event_figure(a, out):
    pre = a["pretrend"].set_index("outcome")
    main = a["results_main"].set_index(["outcome", "estimand"])
    sa = a["sa_event"]
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.9), sharey=False)
    for ax, y in zip(axes, OUT):
        e_pre = np.arange(-8, 0)
        b_pre = np.array([pre.loc[y, f"lead{-e}"] for e in e_pre])
        s_pre = np.array([pre.loc[y, f"lead{-e}_se"] for e in e_pre])
        e_post = np.arange(0, 6)
        b_post = np.array([main.loc[(y, f"h{h}"), "est"] for h in e_post])
        s_post = np.array([main.loc[(y, f"h{h}"), "se"] for h in e_post])
        e = np.concatenate([e_pre, e_post])
        b, s = np.concatenate([b_pre, b_post]), np.concatenate([s_pre, s_post])
        q = sa[(sa["outcome"] == y) & sa["e"].between(-8, 5)].sort_values("e")
        ax.axhline(0, color=MID, lw=0.6, zorder=1)
        ax.axvline(-0.5, color=LIGHT, lw=0.8, ls=(0, (3, 2)), zorder=1)
        ax.errorbar(q["e"] + 0.18, pct(q["est"]),
                    yerr=[pct(q["est"]) - pct(q["est"] - 1.96 * q["se"]), pct(q["est"] + 1.96 * q["se"]) - pct(q["est"])],
                    fmt="s", ms=3.6, mfc="white", mec=MID, mew=0.8, ecolor=MID, elinewidth=0.8, capsize=0, zorder=2,
                    label="Sun and Abraham, year " + MINUS + "1 set to zero")
        ax.plot([-1.0 + 0.18], [0], "s", ms=3.6, mfc="white", mec=MID, mew=0.8, zorder=2)
        ax.errorbar(e - 0.18, pct(b), yerr=[pct(b) - pct(b - 1.96 * s), pct(b + 1.96 * s) - pct(b)], fmt="o", ms=3.8,
                    color=INK, ecolor=INK, elinewidth=0.9, capsize=0, zorder=3, label="Imputation estimator")
        ax.set_title(NAMES[y], fontsize=8, loc="left")
        ax.set_xticks(range(-8, 6))
        ax.set_xlabel("Years relative to first designation")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace("-", MINUS)))
    axes[0].set_ylabel("Effect, percent")
    h, lab = axes[1].get_legend_handles_labels()
    fig.legend(h[::-1], lab[::-1], loc="lower center", ncol=2, frameon=False, fontsize=7, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(out / f"figure2_event_study.{ext}", dpi=600, bbox_inches="tight")
    plt.close(fig)


ROBUST = [
    # (group, label, file, filters) ; filters select one row per outcome; outcome column may be renamed
    ("Estimator", "Imputation estimator", "results_main", dict(estimand="h0_5")),
    ("Estimator", "Callaway and Sant'Anna", "robust_estimators", dict(check="Callaway and Sant'Anna, doubly robust")),
    ("Estimator", "de Chaisemartin and D'Haultfœuille", "robust_estimators",
     dict(check="de Chaisemartin and D'Haultfoeuille")),
    ("Estimator", "Stacked", "robust_estimators", dict(check="stacked")),
    ("Estimator", "Entropy balancing", "robust_estimators", dict(check="entropy balancing")),
    ("Estimator", "2015 population weights", "robust_estimators", dict(check="2015 population weights")),
    ("Estimator", "Sun and Abraham", "robust_honest", dict(check="Sun and Abraham")),
    ("Estimator", "District-specific linear trends", "trends", dict(model="district trends", estimand="h0_5")),
    ("Rival explanation", "2020 and 2021 dropped", "robust_rival", dict(check="2020 and 2021 dropped")),
    ("Rival explanation", "One year of anticipation", "robust_rival", dict(check="one year of anticipation")),
    ("Rival explanation", "Capital cities dropped", "robust_rival", dict(check="capital cities dropped")),
    ("Rival explanation", "Burning-season months dropped", "robust_rival",
     dict(check="burning-season months dropped")),
    ("Rival explanation", "Neighbours of designated districts dropped", "robust_rival",
     dict(check="neighbours of designated districts dropped")),
    ("Rival explanation", "Urban centres as the unit", "robust_rival", dict(check="urban centre as the unit")),
    ("Coding and sample", "Part-district designations not counted", "robust_coding",
     dict(check="part-district designations not counted")),
    ("Coding and sample", "Indonesia dated by the 2022 cohort list", "robust_coding",
     dict(check="Indonesia dated by the 2022 cohort list")),
    ("Coding and sample", "Urban districts only", "robust_coding", dict(check="urban districts only")),
    ("Coding and sample", "Balanced panel", "robust_coding", dict(check="balanced panel")),
    ("Coding and sample", "Area-weighted outcome", "robust_coding", dict(check="area-weighted outcome")),
    ("Inference", "Conley errors, 100 km", "robust_inference", dict(check="Conley standard error, 100 km")),
    ("Inference", "Conley errors, 250 km", "robust_inference", dict(check="Conley standard error, 250 km")),
]
# The wild bootstrap by economy (14 clusters) gives a p-value only. Its analytic economy-clustered interval would disagree
# with that p-value, so the row is reported in the text and in Table S2, not in Figure 3.


def robust_rows(a):
    out = []
    for group, label, f, flt in ROBUST:
        df = a.get(f)
        for y in OUT:
            if df is None:
                continue
            q = df.copy()
            if label == "Area-weighted outcome":
                q["outcome"] = q["outcome"].str.replace("_area", "")
            if label.startswith("Burning") or label.startswith("Monthly"):
                q["outcome"] = q["outcome"].str.replace("ln_m_", "ln_")
            try:
                r = get(q, outcome=y, **flt)
            except KeyError:
                continue
            lo = r["ci_lo"] if "ci_lo" in r and np.isfinite(r["ci_lo"]) else r["est"] - 1.96 * r["se"]
            hi = r["ci_hi"] if "ci_hi" in r and np.isfinite(r["ci_hi"]) else r["est"] + 1.96 * r["se"]
            out.append(dict(group=group, label=label, outcome=y, est=r["est"], lo=lo, hi=hi))
    rr = a.get("robust_rival")
    if rr is not None:
        for y in OUT:
            q = rr[(rr["check"] == "economy dropped") & (rr["outcome"] == y)]
            if len(q):
                out.append(dict(group="Rival explanation", label="Economies dropped one at a time (range)", outcome=y,
                                est=np.nan, lo=q["est"].min(), hi=q["est"].max()))
    # keep each group together, in the order of ROBUST, so the range row sits with the other rival explanations
    order = {g: i for i, g in enumerate(dict.fromkeys(x[0] for x in ROBUST))}
    out = pd.DataFrame(out)
    return out.sort_values("group", key=lambda s: s.map(order), kind="stable").reset_index(drop=True)


def robust_figure(a, out):
    r = robust_rows(a)
    r.to_csv(out / "figure3_robustness.csv", index=False)
    labels = list(dict.fromkeys(r["label"]))
    groups = r.drop_duplicates("label").set_index("label")["group"]
    # y positions with a bold heading row above each group
    ypos, heads, yv, prev = {}, {}, 0.0, None
    for lab in labels:
        if groups[lab] != prev:
            if prev is not None:
                yv += 0.4
            heads[groups[lab]] = yv
            yv += 1
        ypos[lab] = yv
        yv += 1
        prev = groups[lab]
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 0.24 * yv + 1.0), sharey=True)
    for ax, y in zip(axes, OUT):
        q = r[r["outcome"] == y]
        main = q[q["label"] == "Imputation estimator"]["est"].iloc[0]
        ax.axvline(0, color=MID, lw=0.6, zorder=1)
        ax.axvline(pct(main), color=LIGHT, lw=0.8, ls=(0, (3, 2)), zorder=1)
        for _, x in q.iterrows():
            yy = ypos[x["label"]]
            if np.isfinite(x["est"]):
                ax.plot([pct(x["lo"]), pct(x["hi"])], [yy, yy], color=INK, lw=0.9, zorder=2)
                ax.plot(pct(x["est"]), yy, "o", ms=3.6, color=INK if x["label"] == "Imputation estimator" else INK,
                        mfc=INK if x["label"] == "Imputation estimator" else "white", mew=0.9, zorder=3)
            else:
                ax.plot([pct(x["lo"]), pct(x["hi"])], [yy, yy], color=MID, lw=3.0, solid_capstyle="butt", zorder=2)
        ax.set_title(NAMES[y], fontsize=8, loc="left")
        ax.set_xlabel("Effect, percent, years 0 to 5")
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace("-", MINUS)))
    ticks = sorted([(v, g, True) for g, v in heads.items()] + [(ypos[lab], lab, False) for lab in labels])
    axes[0].set_yticks([t[0] for t in ticks])
    axes[0].set_yticklabels([t[1] for t in ticks], fontsize=7)
    for tl, t in zip(axes[0].get_yticklabels(), ticks):
        if t[2]:
            tl.set_fontweight("bold")
    axes[0].invert_yaxis()
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(out / f"figure3_robustness.{ext}", dpi=600, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- supplement

def supplement_robustness(a):
    """Table S2: every robustness row with the estimate, interval, p and note."""
    parts = [a[k].assign(part=k.replace("robust_", "")) for k in
             ("robust_estimators", "robust_rival", "robust_coding", "robust_inference", "robust_extras",
              "robust_honest") if k in a]
    t = pd.concat(parts, ignore_index=True)
    extra = []
    if "ri_cluster" in a:
        extra.append(a["ri_cluster"].rename(columns={"perm_sd": "se"}).assign(
            part="exploratory", check="randomisation inference in province blocks", ci_lo=np.nan, ci_hi=np.nan))
    if "trends" in a:
        extra.append(a["trends"].query("model == 'district trends' and estimand == 'h0_5'").assign(
            part="exploratory", check="district-specific linear trends", note=""))
    if "ntl_ceiling" in a:
        extra.append(a["ntl_ceiling"][a["ntl_ceiling"]["se"].notna()].assign(
            part="exploratory", check=lambda d: "night-time light, " + d["check"]))
    if extra:
        t = pd.concat([t] + extra, ignore_index=True)
    # p-value only for the economy wild bootstrap (see ROBUST) and the permutation tests
    p_only = t["check"].str.contains("wild bootstrap|randomisation inference")
    t.loc[p_only, ["ci_lo", "ci_hi"]] = np.nan
    t["Effect, percent (95% CI) [p]"] = [eff(e, lo, hi, p) if np.isfinite(e) and np.isfinite(lo) else
                                         (num(pct(e)) + (f" [{pval(p)}]" if np.isfinite(p) else "")
                                          if np.isfinite(e) else "")
                                         for e, lo, hi, p in zip(t["est"], t["ci_lo"], t["ci_hi"], t["p"])]
    t["Outcome"] = t["outcome"]
    return t[["part", "check", "group", "Outcome", "Effect, percent (95% CI) [p]", "n_obs", "n_clusters", "note"]]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    an, ex = Path(sys.argv[1]), Path(sys.argv[2])
    (ex / "tables").mkdir(parents=True, exist_ok=True)
    (ex / "figures").mkdir(parents=True, exist_ok=True)
    a = {f.stem: pd.read_csv(f) for f in an.glob("*.csv")}

    rows, header, note = table2(a)
    flat(rows, header).to_csv(ex / "tables" / "table2_effects.csv", index=False)
    write_table(rows, header, "Table II. Effects of smart city designation on PM2.5 and NO2", note,
                ex / "tables" / "table2_effects.docx", widths=[6.2, 5.4, 5.4])
    rows, header, note = table3(a)
    flat(rows, header).to_csv(ex / "tables" / "table3_models_focal.csv", index=False)
    write_table(rows, header, "Table III. Effects by programme model and in the four focal economies", note,
                ex / "tables" / "table3_models_focal.docx", widths=[5.0, 2.4, 4.8, 4.8])
    event_figure(a, ex / "figures")
    robust_figure(a, ex / "figures")
    s2 = supplement_robustness(a)
    s2.to_csv(ex / "tables" / "tableS2_robustness.csv", index=False)
    print(open(ex / "tables" / "table2_effects.csv").read())
    print(open(ex / "tables" / "table3_models_focal.csv").read())


if __name__ == "__main__":
    main()
