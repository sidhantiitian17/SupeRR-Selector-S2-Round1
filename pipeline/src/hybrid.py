"""Hybrid scoring engine: combines solution A (context-adjusted, shrunk pressure rating with
usual-level and consistency components) with solution B (multi-cut-off pressure strike-rate
ensemble for batters; shrunk pressure economy + WPA for bowlers; within-innings leverage
percentile; regular-player pool).  All scorers work on any subset of matches so they can be
evaluated on held-out matches."""
import numpy as np
import pandas as pd
import ratings
from ratings import load, rate, flag_pressure
from config import MIN_PRESSURE_BALLS_BAT, MIN_PRESSURE_MATCHES, MIN_BASELINE_BALLS

PID = {"bat": "striker_id", "bowl": "bowler_id"}


def prep():
    d = load()
    d["pct"] = d.groupby(["match_id", "innings"]).LI.rank(pct=True) * 100   # within-innings leverage percentile (B)
    hp, rt = flag_pressure(d, "PI")
    d["hpA"] = hp
    return d, hp, rt


def z(s):
    return (s - s.mean()) / s.std(ddof=0)


def W(x):
    return x["mw"] if "mw" in x else pd.Series(1.0, index=x.index)


def pool_B(x, role, cut):
    y = x[(x.pct >= cut) & (x.faced if role == "bat" else True)]
    s = W(y).groupby(y[PID[role]]).sum()
    s = s[s > 0]
    return s[s >= s.quantile(0.75)].index


def a_tables(x, role, hp, rt, frac):
    """Solution A on subset x: returns (eligible table e, all-player table t)."""
    ratings.MIN_BASELINE_BALLS = max(30, int(MIN_BASELINE_BALLS * frac))
    e, t = rate(x, role, hp=hp, rt=rt, min_hp=max(30, int(MIN_PRESSURE_BALLS_BAT * frac)),
                min_matches=max(4, int(round(MIN_PRESSURE_MATCHES * frac))))
    ratings.MIN_BASELINE_BALLS = MIN_BASELINE_BALLS
    return e, t


def b_score(x, role):
    """Solution B components (raw, all players)."""
    if role == "bat":
        f = x[x.faced]
        out = {}
        for cut in (75, 85):
            y = f[f.pct >= cut]
            w = W(y)
            out[f"sr{cut}"] = (y.bat_runs * w).groupby(y.striker_id).sum() / w.groupby(y.striker_id).sum()
        return pd.DataFrame(out)
    y = x[x.pct >= 70]
    w = W(y)
    n = w.groupby(y.bowler_id).sum()
    return pd.DataFrame({"neg_rpb": -(y.bowl_runs * w).groupby(y.bowler_id).sum() / n,
                         "wpa": (y.bowl_wpa * w).groupby(y.bowler_id).sum() / n, "n": n})


def b_rank_inputs(B, role, pool):
    B = B.reindex(pool)
    if role == "bat":
        return z(B.sr75) + z(B.sr85)
    n = B.n
    s = 0
    for c in ["neg_rpb", "wpa"]:
        v = B[c]
        sh = v.mean() + n / (n + 500) * (v - v.mean())
        s = s + z(sh)
    return s


def candidates(x, role, hp, rt, frac):
    """Return {name: score Series (higher = better)} for every candidate method."""
    e, t = a_tables(x, role, hp, rt, frac)
    B = b_score(x, role)
    pB = pool_B(x, role, 75 if role == "bat" else 70)
    pA = e.index
    out = {"A: solution A (shipped)": e.score + 100 * e.delivered,
           "B: solution B recipe": b_rank_inputs(B, role, pB)}
    # simple baselines (start of the iteration journey)
    if role == "bat":
        f = x[x.faced & (x.pct >= 80)]
        raw = f.groupby("striker_id").bat_runs.mean()
        vol = x[x.faced & (x.pct >= 75)].groupby("striker_id").size()
    else:
        f = x[x.pct >= 80]
        raw = -f.groupby("bowler_id").bowl_runs.mean()
        vol = x[x.pct >= 70].groupby("bowler_id").size()
    out["BASE: volume (most pressure balls)"] = vol.reindex(pB)
    out["BASE: naive raw pressure SR / economy"] = raw.reindex(pB)
    for pname, pool in [("poolA", pA), ("poolB", pB), ("poolA+B", pA.union(pB))]:
        bq = b_rank_inputs(B, role, pool)
        aq = t.hp_val.reindex(pool)
        up = t.uplift.reindex(pool).fillna(0)
        co = t.consistency.reindex(pool).fillna(t.consistency.median())
        obs = t.hp_raw.reindex(pool)
        # A's full composite (rating + usual-level uplift + consistency) blended with B
        ac = e.score.reindex(pool)
        if ac.notna().sum() > 10:
            for wb in (0.33, 0.5, 0.67):
                out[f"HA(composite) wB={wb} | {pname}"] = (1 - wb) * z(ac.fillna(ac.min())) + wb * z(bq)
        for wb in (0.33, 0.5, 0.67, 0.8, 1.0):
            base = (1 - wb) * z(aq) + wb * z(bq)
            out[f"H wB={wb} | {pname}"] = base
            out[f"H wB={wb} +U+C | {pname}"] = 0.8 * z(base) + 0.1 * z(up) + 0.1 * z(co)
        # gate: must have delivered above league average under pressure (A's rule)
        for wb in (0.5, 0.67, 0.8):
            out[f"H wB={wb} gated | {pname}"] = (1 - wb) * z(aq) + wb * z(bq) + 100 * (obs > 0)
            # same, plus an explicit pressure-vs-usual-level term (the brief's comparison)
            for wu in (0.1, 0.15, 0.2):
                g = z((1 - wb) * z(aq) + wb * z(bq))
                out[f"H wB={wb} gated +U{wu} | {pname}"] = (1 - wu) * g + wu * z(up) + 100 * (obs > 0)
    return out


def has_usual(name):
    """Does the candidate's score contain the pressure-vs-usual-level comparison the brief asks for?"""
    return ("+U" in name) or name.startswith("HA(composite)") or name.startswith("A:")


def targets(y, role):
    """Held-out pressure performance, both pressure definitions x 4 measures, >=30 pressure balls."""
    x = y[y.faced] if role == "bat" else y
    out = {}
    for lab, m in [("A-def", x.hpA), ("B-def", x.pct >= 80)]:
        g = x[m].groupby(PID[role])
        n = g.size()
        if role == "bat":
            T = {"strike rate": g.bat_runs.mean(), "runs above exp": g.bat_val.mean(),
                 "WPA/ball": g.bat_wpa.mean(), "dismissal-avoid": -g.striker_out.mean()}
        else:
            T = {"economy": -g.bowl_runs.mean(), "runs saved vs exp": g.bowl_val.mean(),
                 "WPA/ball": g.bowl_wpa.mean(), "wickets/ball": g.bowler_wkt.mean()}
        for k, v in T.items():
            out[f"{lab} | {k}"] = v[n >= 30]
    return pd.DataFrame(out)


from recipes import describe, components  # noqa: E402,F401  (re-exported)
