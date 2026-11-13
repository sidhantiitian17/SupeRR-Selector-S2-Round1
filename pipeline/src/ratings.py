"""Player-rating engine shared by the ranking, validation and report steps."""
import numpy as np
import pandas as pd
from config import (HIGH_PRESSURE_QUANTILE, LOW_PRESSURE_QUANTILE, MIN_PRESSURE_BALLS_BAT,
                    MIN_PRESSURE_BALLS_BOWL, MIN_PRESSURE_MATCHES, MIN_BASELINE_BALLS,
                    W_QUALITY, W_UPLIFT, W_CONSIST, OUT, VALUE_LENS, MODEL, CONSIST_LENS, MIN_UPLIFT_WEIGHT, BLEND_DIRECT)

ROLE = {
    "bat": dict(pid="striker_id", name="striker_name", val="bat_val", wpa="bat_wpa", w="w_bat", mask="faced",
                min_hp=MIN_PRESSURE_BALLS_BAT),
    "bowl": dict(pid="bowler_id", name="bowler_name", val="bowl_val", wpa="bowl_wpa", w="w_bowl", mask=None,
                 min_hp=MIN_PRESSURE_BALLS_BOWL),
}


def load():
    d = pd.read_parquet(OUT / "deliveries_value.parquet")
    d["NAIVE"] = (((d.innings == 2) & (d.rrr >= 9)) | (d.over_no >= 17) | ((d.wkts_before >= 4) & (d.over_no <= 10))).astype(float)
    # split the per-ball value into a run component and a wicket component so each can be
    # shrunk according to its own (very different) signal-to-noise ratio
    d["bat_r"] = d.bat_runs - d.E_bat_runs
    d["bat_w"] = -d.Wc * (d.striker_out.astype(int) - d.P_out)
    d["bowl_r"] = d.E_bowl_runs - d.bowl_runs
    d["bowl_w"] = d.Wc * (d.bowler_wkt.astype(int) - d.P_bwkt)
    # context-neutral win value: WPA divided by the leverage of the delivery (WPA/LI).
    # Expressed in win-probability *percentage points* per ball at average leverage.
    # LI is floored at 0.25 so near-dead deliveries cannot explode the ratio, and the value is
    # centred within (innings x phase x pressure-decile) cells so that an average player scores 0
    # in every context (removes WP-model drift between contexts; iteration 3 in the report).
    li = d.LI_c.clip(lower=0.25)
    cell = [d.innings, d.phase, pd.qcut(d.PI, 10, labels=False)]
    for role, mask in [("bat", d.faced), ("bowl", pd.Series(True, index=d.index))]:
        raw = 100 * d[f"{role}_wpa"] / li
        mu = raw[mask].groupby([c[mask] for c in cell]).transform("mean")
        d[f"{role}_wpali"] = (raw - mu.reindex(d.index)).where(mask)
    return d


def flag_pressure(d, pcol="PI", hp_q=HIGH_PRESSURE_QUANTILE, rt_q=LOW_PRESSURE_QUANTILE):
    if d[pcol].nunique() <= 2:
        hp = d[pcol] >= 1
        rt = ~hp
    else:
        hp = d[pcol] >= d[pcol].quantile(hp_q)
        rt = d[pcol] <= d[pcol].quantile(rt_q)
    return hp.values, rt.values


def eb_shrink(sum_v, sum_w, sum_v2, min_n=30):
    """Empirical-Bayes (normal-normal) shrinkage of per-ball means toward the league mean (0)."""
    n = sum_w
    mean = sum_v / n.clip(lower=1e-9)
    var_i = (sum_v2 / n.clip(lower=1e-9) - mean ** 2).clip(lower=1e-9)
    ok = n >= min_n
    sigma2 = np.average(var_i[ok], weights=n[ok])              # within-player per-ball noise
    # DerSimonian-Laird method-of-moments estimate of true between-player variance
    nk, mk = n[ok], mean[ok]
    mbar = np.average(mk, weights=nk)
    Q = np.sum(nk * (mk - mbar) ** 2) / sigma2
    denom = nk.sum() - (nk ** 2).sum() / nk.sum()
    tau2 = max((Q - (len(nk) - 1)) * sigma2 / denom, 1e-6)
    k = sigma2 / tau2
    return mean * n / (n + k), k


def eb_means(mean, n, sigma2, min_n=30):
    """EB shrinkage of player means (noise var sigma2/n) toward 0; DerSimonian-Laird tau^2."""
    ok = (n >= min_n) & mean.notna()
    nk, mk = n[ok], mean[ok]
    mbar = np.average(mk, weights=nk)
    Q = np.sum(nk * (mk - mbar) ** 2) / sigma2
    denom = nk.sum() - (nk ** 2).sum() / nk.sum()
    tau2 = max((Q - (len(nk) - 1)) * sigma2 / denom, 1e-9)
    k = sigma2 / tau2
    return (mean * n / (n + k)).fillna(0), k


def agg(d, role, mask, val_col):
    r = ROLE[role]
    x = d[mask]
    if r["mask"]:
        x = x[x[r["mask"]]]
    w0 = x[r["w"]] * (x["pw"] if "pw" in x else 1.0)   # pw = optional continuous pressure weight
    w = w0 * (x["mw"] if "mw" in x else 1.0)            # mw = bootstrap match weight
    v = x[val_col] * w
    g = pd.DataFrame({"pid": x[r["pid"]].values, "v": v.values, "w": w.values, "v2": (x[val_col] ** 2 * w).values,
                      "match": x.match_id.values, "legal": x.is_legal.values,
                      "mw": (x["mw"].values if "mw" in x else np.ones(len(x))), "vm": (x[val_col] * w0).values})
    out = g.groupby("pid").agg(sum_v=("v", "sum"), sum_w=("w", "sum"), sum_v2=("v2", "sum"),
                                balls=("legal", "sum"), deliveries=("v", "size"))
    pmg = g.groupby(["pid", "match"]).agg(v=("vm", "sum"), mw=("mw", "first"))
    pm = pmg.v
    pmg = pmg[pmg.mw > 0]
    out["matches"] = pmg.mw.groupby(level=0).sum()
    out["pos_matches"] = (pmg.mw * (pmg.v > 0)).groupby(level=0).sum()
    out[["matches", "pos_matches"]] = out[["matches", "pos_matches"]].fillna(0)
    return out, pm


def rate(d, role="bat", pcol="PI", val=VALUE_LENS, hp_q=HIGH_PRESSURE_QUANTILE, rt_q=LOW_PRESSURE_QUANTILE,
         weights=None, min_hp=None, min_matches=MIN_PRESSURE_MATCHES,
         eligible=None, hp=None, rt=None, model=MODEL, cons_val=CONSIST_LENS):
    r = ROLE[role]
    if hp is None:
        hp, rt = flag_pressure(d, pcol, hp_q, rt_q)
    if model == "blend":
        # Pressure rating = average of (a) what he actually did under pressure (direct EB) and
        # (b) the hierarchical forecast (own overall level + shrunk pressure deviation).
        kw = dict(pcol=pcol, val=val, hp_q=hp_q, rt_q=rt_q, min_hp=min_hp, min_matches=min_matches,
                  eligible=eligible, hp=hp, rt=rt, cons_val=cons_val)
        e1, t1 = rate(d, role, weights=(1, 0, 0), model="direct", **kw)
        _, t2 = rate(d, role, weights=(1, 0, 0), model="hier", **kw)
        t = t1.copy()
        t["hp_direct"], t["hp_hier"] = t1.hp_val, t2.hp_val.reindex(t1.index)
        t["rt_direct"] = t1.rt_val
        t["hp_val"] = BLEND_DIRECT * t.hp_direct + (1 - BLEND_DIRECT) * t.hp_hier
        return finish(t, role, weights, e1.attrs)
    if val == "val":   # component-wise shrinkage: runs part + wicket part
        comps = [f"{role}_r", f"{role}_w"]
    elif val == "val_joint":
        comps = [r["val"]]
    else:
        comps = [{"wpa": r["wpa"], "wpali": f"{role}_wpali"}.get(val, val)]
    kH, kR = [], []
    allm = np.ones(len(d), bool)
    for i, c in enumerate(comps):
        Hc, pmc = agg(d, role, hp, c)
        Rc, _ = agg(d, role, rt, c)
        if model == "hier":
            # Hierarchical: pressure performance = own overall level + (shrunk) pressure deviation.
            Ac, _ = agg(d, role, allm, c)
            base, kA = eb_shrink(Ac.sum_v, Ac.sum_w, Ac.sum_v2)
            mA = Ac.sum_v / Ac.sum_w
            s2 = np.average((Ac.sum_v2 / Ac.sum_w - mA ** 2).clip(lower=1e-9)[Ac.sum_w >= 30], weights=Ac.sum_w[Ac.sum_w >= 30])
            out = []
            for X in (Hc, Rc):
                dev = X.sum_v / X.sum_w - mA.reindex(X.index)
                neff = 1 / (1 / X.sum_w - 1 / Ac.sum_w.reindex(X.index)).clip(lower=1e-9)   # X is a subset of all balls
                dsh, kd = eb_means(dev, neff, s2)
                out.append((base.reindex(X.index) + dsh, kd))
            (sh, k1), (sr, k2) = out
        else:
            sh, k1 = eb_shrink(Hc.sum_v, Hc.sum_w, Hc.sum_v2)
            sr, k2 = eb_shrink(Rc.sum_v, Rc.sum_w, Rc.sum_v2)
        kH.append(k1); kR.append(k2)
        if i == 0:
            H, R, pm = Hc.copy(), Rc.copy(), pmc
            H["hp_val"], R["rt_val"] = sh, sr
        else:
            H["sum_v"] += Hc.sum_v; H["hp_val"] += sh
            R["sum_v"] += Rc.sum_v; R["rt_val"] += sr
            pm = pm + pmc
    t = H.join(R[["rt_val", "balls", "sum_v", "sum_w"]].rename(columns={"balls": "rt_balls", "sum_v": "rt_sum_v", "sum_w": "rt_sum_w"}), how="left")
    t["rt_val"] = t.rt_val.fillna(0)
    t["hp_raw"] = t.sum_v / t.sum_w
    t["rt_raw"] = t.rt_sum_v / t.rt_sum_w
    t["uplift"] = t.hp_val - t.rt_val
    if cons_val is not None:   # match-level consistency is judged in win-probability currency
        _, pm = agg(d, role, hp, {"wpali": f"{role}_wpali", "val_r": f"{role}_r"}.get(cons_val, cons_val))
    # ---- match-level reliability (role-specific, chosen by split-half reliability in s05) ----
    # pm = player's net pressure value in each match.  Thresholds = league quartiles of pm.
    mwm = d.groupby("match_id").mw.first() if "mw" in d else None
    mw = pm.index.get_level_values(1).map(mwm).values if mwm is not None else np.ones(len(pm))
    big, fail = pm.quantile(0.75), pm.quantile(0.25)
    n = pd.Series(mw, index=pm.index).groupby(level=0).sum()
    n_big = ((pm > big) * mw).groupby(level=0).sum()
    n_fail = ((pm < fail) * mw).groupby(level=0).sum()
    t["impact_rate"] = (n_big + 1) / (n + 4)          # how often he produces a decisive pressure contribution
    t["no_fail_rate"] = 1 - (n_fail + 1) / (n + 4)     # how rarely he is the reason a pressure moment is lost
    t["pos_rate"] = (t.pos_matches + 3) / (t.matches + 6)
    t["consistency"] = t.impact_rate if role == "bat" else t.no_fail_rate
    t["hp_direct"], t["rt_direct"] = t.hp_val, t.rt_val
    mh = min_hp if min_hp is not None else r["min_hp"]
    if eligible is None:
        t["eligible"] = (t.balls >= mh) & (t.matches >= min_matches) & (t.rt_balls.fillna(0) >= MIN_BASELINE_BALLS)
    else:
        t["eligible"] = t.index.isin(eligible)
    return finish(t, role, weights, dict(kH=kH, kR=kR))


def finish(t, role, weights, attrs):
    # uplift always compares the player's *observed* pressure level with his *observed* usual level
    t["uplift"] = t.hp_direct - t.rt_direct
    e = t[t.eligible].copy()
    e[["hp_val", "uplift", "consistency"]] = e[["hp_val", "uplift", "consistency"]].fillna(0)
    z = lambda s: (s - s.mean()) / s.std(ddof=0)
    wq, wu, wc = weights if weights is not None else load_weights(role)
    e["score"] = wq * z(e.hp_val) + wu * z(e.uplift) + wc * z(e.consistency)
    # Gate: a top ranking must be earned under pressure - players whose observed pressure
    # performance is below league average are ordered after every player who delivered.
    e["delivered"] = e.hp_raw > 0
    e["rank"] = (e.score + 100 * e.delivered.astype(int)).rank(ascending=False, method="first").astype(int)
    e.attrs.update(attrs)
    return e.sort_values("rank"), t


def load_weights(role):
    """Composite weights proportional to each component's split-half reliability (written by s05)."""
    import json
    f = OUT / "weights.json"
    if f.exists():
        return tuple(json.loads(f.read_text())[role])
    return (W_QUALITY, W_UPLIFT, W_CONSIST)


def names(d):
    a = d.groupby("striker_id").striker_name.agg(lambda s: s.mode().iat[0])
    b = d.groupby("bowler_id").bowler_name.agg(lambda s: s.mode().iat[0])
    return pd.concat([a, b]).groupby(level=0).first()
