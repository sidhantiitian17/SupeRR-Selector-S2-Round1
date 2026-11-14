#!/usr/bin/env python3
"""End-to-end check: every number the dashboard shows must come from the hybrid pipeline outputs.

    python3 -I scripts/verify_dashboard.py <hybrid/outputs> <project root>

Recomputes everything with its own code (it does not import build_data.py) and compares against
data/clutch_data.js and data/watchlist.js. Prints PASS/FAIL per check and exits 1 on any failure.
"""
import json, pathlib, sys, re
import numpy as np, pandas as pd

OUT, ROOT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
load = lambda f: (lambda t: json.loads(t[t.index("{"):t.rindex("}") + 1]))((ROOT / f).read_text())
D, W = load("data/clutch_data.js"), load("data/watchlist.js")
fails, n_checks = [], 0


def check(name, ok, detail=""):
    global n_checks
    n_checks += 1
    if not ok: fails.append(f"{name}: {detail}")


def close(a, b, tol):
    if a is None or b is None: return a is None and b is None
    return abs(float(a) - float(b)) <= tol


d = pd.read_parquet(OUT / "deliveries_value.parquet")
d["pct"] = d.groupby(["match_id", "innings"]).LI.rank(pct=True) * 100
d["hp"] = d.PI >= d.PI.quantile(0.70)

# ---------------------------------------------------------------- 1. official ranking = pipeline ranking
top = pd.read_csv(OUT / "FINAL_TOP10_HYBRID.csv")
for role, col in (("bat", "batter"), ("bowl", "bowler")):
    R = pd.read_csv(OUT / f"hyb_ratings_{role}.csv").head(120)
    dash = D[role]
    check(f"{role}: 120 ranked players", len(dash) == 120, len(dash))
    check(f"{role}: top 10 order = FINAL_TOP10_HYBRID.csv", [p["name"] for p in dash[:10]] == list(top[col]),
          [p["name"] for p in dash[:10]])
    for p, r in zip(dash, R.itertuples()):
        check(f"{role} {p['name']}: id/rank", p["id"] == r.pid and p["rank"] == r.rank, (p["id"], r.pid, p["rank"], r.rank))
        for k, v, tol in (("ptop10", r.p_top10, 1e-3), ("rlo", r.rank_p05, .05), ("rhi", r.rank_p95, .05), ("rmed", r.boot_median_rank, .05),
                          ("specs", r.specs_in_top10, 0), ("nspecs", r.n_specs, 0), ("uplift", r.uplift, 1e-3), ("cons", r.consistency, 1e-3),
                          ("balls", r.balls, 0), ("nmatches", r.matches, 0)):
            check(f"{role} {p['name']}: {k}", close(p[k], v, tol), (p[k], v))
    cl = [p["clutch"] for p in dash]
    check(f"{role}: Clutch Rating never rises down the official order", all(a >= b for a, b in zip(cl, cl[1:])))
    check(f"{role}: Clutch Rating 0-100", 0 <= min(cl) and max(cl) <= 100)

# ---------------------------------------------------------------- 2. top-10 evidence = methodology report table
for role in ("bat", "bowl"):
    E = pd.read_csv(OUT / f"hyb_evidence_{role}.csv").set_index("Unnamed: 0")
    for p in D[role][:10]:
        e, c = E.loc[p["id"]], p["s"]["combined"]
        if role == "bat":
            pairs = (("pb", e["P balls"], 0), ("pm", e["P SR"], .06), ("um", e["usual SR"], .06), ("rae", e["P RAE/100"], .06), ("urae", e["usual RAE/100"], .06))
        else:
            pairs = (("pb", e["P balls"], 0), ("pm", e["P econ"], .006), ("um", e["usual econ"], .006), ("rae", e["P RAE saved/100"], .06), ("urae", e["usual RAE/100"], .06))
        for k, v, tol in pairs:
            check(f"report table {p['name']}: {k}", close(c[k], v, tol), (c[k], round(float(v), 3)))

# ---------------------------------------------------------------- 3. per-player stats recomputed from deliveries (all 240 x 3 filters)
def stats(g, role):
    if role == "bat":
        g = g[g.faced]; p, u = g[g.pct >= 75], g[g.pct < 75]
        return dict(pb=len(p), pm=100 * p.bat_runs.mean(), um=100 * u.bat_runs.mean() if len(u) else None,
                    prate=100 * p.striker_out.mean(), rae=100 * g[g.hp].bat_val.mean() if g.hp.any() else None)
    p, u = g[g.pct >= 70], g[g.pct < 70]; pl, ul = p[p.is_legal], u[u.is_legal]
    return dict(pb=len(pl), pm=6 * p.bowl_runs.sum() / len(pl), um=6 * u.bowl_runs.sum() / len(ul) if len(ul) else None,
                prate=100 * p.bowler_wkt.sum() / len(pl), rae=100 * g[g.hp].bowl_val.mean() if g.hp.any() else None)
TOL = {"pb": 0, "pm": .06, "um": .06, "prate": .006, "rae": .06}
for role, pid in (("bat", "striker_id"), ("bowl", "bowler_id")):
    for p in D[role]:
        x = d[d[pid] == p["id"]]
        for comp in ("combined", "ipl", "t20i"):
            g = x if comp == "combined" else x[x.comp_kind == comp.upper()]
            mine, theirs = (stats(g, role) if len(g) else None), p["s"][comp]
            if theirs is None:
                check(f"{p['name']} {comp}: empty", mine is None or mine["pb"] == 0, mine); continue
            for k, tol in TOL.items():
                check(f"{p['name']} {comp}: {k}", close(theirs[k], mine[k], tol + (0.006 if role == "bowl" and k in ("pm", "um") else 0)), (theirs[k], mine[k]))
        # seasons, trend, matches
        gg = x[x.faced] if role == "bat" else x; pp = gg[gg.hp]; val = pp.bat_val if role == "bat" else pp.bowl_val
        for s in p["seasons"]:
            y = pp[pp.year == s["y"]]
            check(f"{p['name']} season {s['y']}", len(y) == s["n"] and close(s["v"], 100 * (y.bat_val if role == "bat" else y.bowl_val).mean(), .06), (s, len(y)))
        if p["trend"]:
            check(f"{p['name']} trend end = career value", close(p["trend"][-1]["v"], 100 * val.mean(), .06) and p["trend"][-1]["n"] == len(pp), (p["trend"][-1], len(pp)))
        for m in p["ms"]:
            y = pp[pp.match_id == m["m"]]
            check(f"{p['name']} match {m['m']}", len(y) == m["n"] and close(m["v"], (y.bat_val if role == "bat" else y.bowl_val).sum(), .006), (m, len(y)))

# ---------------------------------------------------------------- 4. league-level numbers
S = D["summary"]
check("deliveries", S["balls"] == len(d), (S["balls"], len(d)))
check("matches", S["matches"] == d.match_id.nunique(), (S["matches"], d.match_id.nunique()))
check("years", S["years"] == [int(d.year.min()), int(d.year.max())], S["years"])
wp = pd.read_csv(OUT / "wp_model_metrics.csv")
check("WP AUC inn 1 = 0.706", round(float(wp.auc[0]), 3) == 0.706); check("WP AUC inn 2 = 0.896", round(float(wp.auc[1]), 3) == 0.896)
check("high-pressure threshold", close(D["validation"]["thr_hp"], d.PI.quantile(.70), 1e-3), (D["validation"]["thr_hp"], d.PI.quantile(.70)))
check("routine threshold", close(D["validation"]["thr_rt"], d.PI.quantile(.50), 1e-3))

# ---------------------------------------------------------------- 5. hard-coded text claims vs the methodology report PDF
from pypdf import PdfReader
pdf = " ".join(" ".join(pg.extract_text().split()) for pg in PdfReader(str(OUT / "SupeRR_Selector_Round1_HYBRID_Methodology_Report.pdf")).pages)
_wc = d.groupby("phase").Wc.mean().round(1)
check("wicket cost in pages.js matches data", f"about {_wc['PP']:.1f} runs in the powerplay, {_wc['MID']:.1f} in the middle, {_wc['DEATH']:.1f} at the death" in (ROOT / "js/pages.js").read_text())
for claim in ("1.15 in knock-outs", f"{_wc['PP']:.1f} runs in the powerplay", f"{_wc['MID']:.1f} in the middle overs", f"{_wc['DEATH']:.1f} at the death", "0.67 x z(A composite) + 0.33",
              "0.90 x z[0.2 x z(A rating) + 0.8", "DerSimonian-Laird", "150 pressure balls, 12 matches, 150 usual balls",
              "30 random half-splits, 6 past-to-future cuts", "8 targets", "837 matches, 193,988 deliveries", "1st innings 0.706, chase 0.896"):
    check(f"report text contains '{claim}'", claim in pdf)
js = (ROOT / "js/pages.js").read_text()
check("0.32 / 0.21 SD claims match report", "0.321" in pdf and "0.213" in pdf and "0.32 SD" in js and "0.21 for bowlers" in js)

# ---------------------------------------------------------------- 6. watchlist: rule holds, numbers recompute
off10 = {p["id"] for k in ("bat", "bowl") for p in D[k][:10]}
for p in W["bat"] + W["bowl"]:
    check(f"watchlist {p['name']} not in official top 10", p["id"] not in off10)
    check(f"watchlist {p['name']} passes rule", p["rk"] <= 10 and p["ptop"] >= W["rule"]["p_min"] and p["n"] >= W["rule"]["min_balls"], p)
    pid = "striker_id" if p["role"] == "bat" else "bowler_id"
    x = d[(d.year >= 2025) & (d[pid] == p["id"])]; x = x[x.faced] if p["role"] == "bat" else x
    y = x[x.hp]; v = 100 * (y.bat_val if p["role"] == "bat" else y.bowl_val).mean()
    check(f"watchlist {p['name']} balls/value", len(y) == p["n"] and close(v, p["v"], .06), (len(y), p["n"], v, p["v"]))
for r in W["rr"]:
    nums = re.findall(r"[-+]?\d+\.\d", r["text"])
    check(f"RR review {r['name']}: text built from data (has numbers)", len(nums) > 4)
    o = next(p for p in D[r["role"]] if p["id"] == r["id"])
    check(f"RR review {r['name']}: official rank", f"Official #{o['rank']}" in r["text"])

print(f"{n_checks} checks, {len(fails)} failed")
for f in fails[:40]: print("FAIL", f)
sys.exit(1 if fails else 0)
