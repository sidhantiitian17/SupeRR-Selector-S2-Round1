#!/usr/bin/env python3
"""Build data/watchlist.js: (1) a 2025-26 recent-form watchlist chosen by a fixed rule,
(2) a review of Rajasthan Royals players' IPL 2026 pressure numbers (why they are not in the official top 10).

    python3 -I scripts/build_watchlist.py <hybrid/outputs> <project root>

The official top 10 is NOT changed by anything here.
Rule (fixed before looking at names):
  * deliveries from calendar years 2025-2026, IPL + T20I
  * at least 120 pressure balls (pressure = top 30% of all balls by Pressure Index, the model's official definition)
  * score = pressure-ball value per 100 balls, shrunk toward the mean (Empirical Bayes, as in the official method)
  * recent rank <= 10, in the recent top 10 in >= 50% of 300 bootstrap resamples, and not in the official top 10
"""
import json, pathlib, sys
import numpy as np, pandas as pd

OUT, ROOT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
d = pd.read_parquet(OUT / "deliveries_value.parquet")
d["hp"] = d.PI >= d.PI.quantile(0.70)   # official pressure definition of the model (top 30% Pressure Index), same as the report
t = (ROOT / "data/clutch_data.js").read_text(); D = json.loads(t[t.index("{"):t.rindex("}") + 1])
CUT = {"bat": 75, "bowl": 70}; PID = {"bat": "striker_id", "bowl": "bowler_id"}; NM = {"bat": "striker_name", "bowl": "bowler_name"}
VAL = {"bat": "bat_val", "bowl": "bowl_val"}; MIN_BALLS, P_MIN, B = 120, 0.5, 1000
rng = np.random.default_rng(7)


RECENT = {}


def recent(role):
    off = {p["id"]: p for p in D[role]}
    x = d[d.year >= 2025]; x = x[x.faced] if role == "bat" else x
    p, u = x[x.hp], x[~x.hp]
    g = p.groupby(PID[role]).agg(name=(NM[role], "last"), n=(VAL[role], "size"), v=(VAL[role], "mean"), m=("match_id", "nunique"))
    g = g.join(u.groupby(PID[role])[VAL[role]].mean().rename("uv"))
    if role == "bat":
        g = g.join(p.groupby(PID[role]).bat_runs.mean().mul(100).rename("pm")).join(u.groupby(PID[role]).bat_runs.mean().mul(100).rename("um"))
    else:
        ec = lambda z: z.groupby(PID[role]).apply(lambda q: 6 * q.bowl_runs.sum() / max(q.is_legal.sum(), 1))
        g = g.join(ec(p).rename("pm")).join(ec(u).rename("um"))
    s2 = p.groupby(PID[role])[VAL[role]].var().median()
    q = g[g.n >= 60]; mu = q.v.mean(); tau2 = max(q.v.var() - (s2 / q.n).mean(), 1e-6)
    shr = lambda m, n: mu + (m - mu) * tau2 / (tau2 + s2 / n)
    e = g[g.n >= MIN_BALLS].copy(); e["shr"] = shr(e.v, e.n)
    e["rk"] = e.shr.rank(ascending=False, method="first").astype(int)
    ids = e.index.values; vals = {i: p.loc[p[PID[role]] == i, VAL[role]].values for i in ids}; top = np.zeros(len(ids))
    for _ in range(B):
        sc = np.array([shr(rng.choice(vals[i], len(vals[i])).mean(), len(vals[i])) for i in ids])
        top += (-sc).argsort().argsort() < 10
    e["ptop"] = top / B
    pick = e[(e.rk <= 10) & (e.ptop >= P_MIN) & ~e.index.map(lambda i: i in off and off[i]["rank"] <= 10)].sort_values("rk")
    near = e[(e.rk <= 12) & (e.ptop < P_MIN) & ~e.index.map(lambda i: i in off and off[i]["rank"] <= 10)].sort_values("rk")
    row = lambda i, r: dict(id=int(i), name=r["name"], role=role, team=off[i]["team"] if i in off else "", official=off[i]["rank"] if i in off else None,
                            n=int(r.n), m=int(r.m), v=round(100 * r.v, 1), gap=round(100 * (r.v - r.uv), 1), pm=round(float(r.pm), 2), um=round(float(r.um), 2),
                            rk=int(r.rk), ptop=round(float(r.ptop), 2))
    RECENT[role] = dict(rank={int(i): int(r.rk) for i, r in e.iterrows()}, n=len(e))
    return [row(i, r) for i, r in pick.iterrows()], [row(i, r) for i, r in near.iterrows()], len(e)


bat, bat_near, n_bat = recent("bat")
bowl, bowl_near, n_bowl = recent("bowl")

# ------------------------------------------------------------------ RR review: IPL 2026 pressure numbers
x = d[(d.year == 2026) & (d.comp_kind == "IPL")]
def bat26(g):
    g = g[g.faced]; p, u = g[g.hp], g[~g.hp]
    return dict(m=int(g.match_id.nunique()), runs=int(g.bat_runs.sum()), pb=int(len(p)), pm=round(100 * p.bat_runs.mean(), 1) if len(p) else None,
                um=round(100 * u.bat_runs.mean(), 1) if len(u) else None, pout=int(p.striker_out.sum()), v=round(100 * p.bat_val.mean(), 1) if len(p) else None)
def bowl26(g):
    p, u = g[g.hp], g[~g.hp]; ec = lambda z: round(6 * z.bowl_runs.sum() / max(z.is_legal.sum(), 1), 2)
    return dict(m=int(g.match_id.nunique()), w=int(g.bowler_wkt.sum()), pb=int(len(p)), pm=ec(p) if len(p) else None, um=ec(u) if len(u) else None,
                pw=int(p.bowler_wkt.sum()), v=round(100 * p.bowl_val.mean(), 1) if len(p) else None)
Bt = {i: bat26(g) for i, g in x.groupby("striker_id")}; Bw = {i: bowl26(g) for i, g in x.groupby("bowler_id")}
rank_of = lambda tab, i: (1 + sum(1 for k, s in tab.items() if s["pb"] >= 40 and s["v"] is not None and s["v"] > tab[i]["v"]), sum(1 for s in tab.values() if s["pb"] >= 40))

RR = [(3298, "bowl"), (6819, "bat"), (7260, "bat"), (6423, "bat"), (3297, "bat"), (152, "bat"), (7503, "bowl"), (2411, "bowl")]
f1 = lambda v: "n/a" if v is None else f"{v:+.1f}"


def review(o, role, s26, r26, rec_rank, n_rec):
    """Every number in the text is read from the data; nothing is typed by hand."""
    c = o["s"]["combined"]; bat = role == "bat"; se = {z["y"]: z["v"] for z in o["seasons"]}
    unit = "strike rate" if bat else "economy"
    better = (c["pm"] > c["um"]) if bat else (c["pm"] < c["um"])
    t = [f"Official #{o['rank']} {'batter' if bat else 'bowler'}; top 10 in {100 * o['ptop10']:.1f}% of 300 resamples and in {o['specs']} of {o['nspecs']} model versions."]
    t.append(f"2022-26 under pressure: {unit} {c['pm']} vs {c['um']} usual ({'better' if better else 'not better'} under pressure); "
             f"runs {'above expected' if bat else 'saved'} per 100 pressure balls {f1(c['rae'])}.")
    if se: t.append("By season: " + ", ".join(f"{y} {f1(v)}" for y, v in sorted(se.items())) + ".")
    if s26 and s26["pb"]:
        line = (f"IPL 2026: {s26['runs']} runs in {s26['m']} matches; under pressure {s26['pm']} vs {s26['um']} usual"
                if bat else f"IPL 2026: {s26['w']} wickets in {s26['m']} matches; under pressure economy {s26['pm']} vs {s26['um']} usual")
        line += f", value {f1(s26['v'])} per 100 pressure balls" + (f" ({r26[0]} of {r26[1]} with 40+ pressure balls)." if r26 else f" on only {s26['pb']} pressure balls.")
        t.append(line)
    else:
        t.append("Did not play enough IPL 2026 pressure balls to judge last season.")
    t.append(f"Recent form 2025-26: #{rec_rank} of {n_rec} eligible." if rec_rank else "Fewer than 120 pressure balls in 2025-26, so not eligible for the recent-form list.")
    return " ".join(t)


off = {p["id"]: p for k in ("bat", "bowl") for p in D[k]}
offr = {(p["id"], k): p for k in ("bat", "bowl") for p in D[k]}
rr = []
for i, role in RR:
    o = offr[(i, role)]
    s = (Bt if role == "bat" else Bw).get(i)
    r = rank_of(Bt if role == "bat" else Bw, i) if s and s["pb"] >= 40 else None
    rec = RECENT[role]
    rr.append(dict(id=i, name=o["name"], role=role, official=o["rank"], clutch=o["clutch"], ptop=o["ptop10"], photo=o["photo"],
                   s26=s, r26=list(r) if r else None, seasons=o["seasons"],
                   text=review(o, role, s, list(r) if r else None, rec["rank"].get(i), rec["n"])))

v = next(p for p in D["bat"] if p["name"] == "Vaibhav Sooryavanshi")
out = dict(rule=dict(years="2025-2026", min_balls=MIN_BALLS, p_min=P_MIN, resamples=B, n_bat=n_bat, n_bowl=n_bowl),
           bat=bat, bowl=bowl, near=bat_near + bowl_near, rr=rr, rr_in_list=dict(name=v["name"], rank=v["rank"], ptop=v["ptop10"]))
(ROOT / "data/watchlist.js").write_text("window.CLUTCH_WATCH = " + json.dumps(out, separators=(",", ":")) + ";\n")
print("watchlist bat", [p["name"] for p in bat], "bowl", [p["name"] for p in bowl])
print("near", [p["name"] for p in out["near"]])
