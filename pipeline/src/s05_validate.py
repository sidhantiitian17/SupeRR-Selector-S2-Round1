"""Step 5 - Iterate & validate.  Every design choice is decided by the same
out-of-sample yardsticks rather than by taste:

  1. Decisiveness  - share of all win-probability swing (|WPA|) that falls on the
                     deliveries a definition labels "high pressure".
  2. Separation    - league-wide behaviour change (dismissal %, dot %, boundary %, run rate).
  3. Split-half reliability - Spearman rho between player ratings computed on two
                     disjoint random halves of the matches (repeated splits).
  4. Temporal validity - rating from 2022-24 vs rating from 2025-26 (same players).
  5. Sensitivity  - top-10 overlap under alternative settings.

Outputs: val_*.csv tables and weights.json (composite weights proportional to
component reliability) which s04_rank.py consumes.
"""
import json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from config import OUT, SEED
from ratings import load, rate, flag_pressure, agg

N_SPLITS = 16


def halves(d, n, seed):
    rng = np.random.default_rng(seed)
    mids = d.match_id.unique()
    for _ in range(n):
        half = set(rng.choice(mids, len(mids) // 2, replace=False))
        yield d.match_id.isin(half).values


def split_half(d, role, hp, rt, val, field="hp_val", n_splits=N_SPLITS, seed=SEED):
    e, _ = rate(d, role, hp=hp, rt=rt, val=val, min_hp=100, min_matches=8, weights=(1, 0, 0))
    elig = e.index
    rs = []
    for a in halves(d, n_splits, seed):
        ea, _ = rate(d[a], role, hp=hp[a], rt=rt[a], val=val, eligible=elig, weights=(1, 0, 0))
        eb, _ = rate(d[~a], role, hp=hp[~a], rt=rt[~a], val=val, eligible=elig, weights=(1, 0, 0))
        j = ea[[field]].join(eb[[field]], rsuffix="_b").dropna()
        rs.append(spearmanr(j.iloc[:, 0], j.iloc[:, 1]).statistic)
    return float(np.mean(rs)), float(np.std(rs)), len(elig)


def temporal(d, role, hp, rt, val, field="hp_val"):
    early = (d.year <= 2024).values
    ea, _ = rate(d[early], role, hp=hp[early], rt=rt[early], val=val, min_hp=80, min_matches=6, weights=(1, 0, 0))
    eb, _ = rate(d[~early], role, hp=hp[~early], rt=rt[~early], val=val, min_hp=80, min_matches=6, weights=(1, 0, 0))
    j = ea[[field]].join(eb[[field]], rsuffix="_b", how="inner")
    return float(spearmanr(j.iloc[:, 0], j.iloc[:, 1]).statistic), len(j)


def consistency_variants(d, role, h, elig):
    _, pm = agg(d, role, h, f"{role}_wpali")
    pm = pm[pm.index.get_level_values(0).isin(elig)]
    big, fail = pm.quantile(0.75), pm.quantile(0.25)
    g = pm.groupby(level=0)
    return pd.DataFrame({"positive-match rate": g.apply(lambda s: ((s > 0).sum() + 3) / (len(s) + 6)),
                         "impact rate (top-quartile matches)": g.apply(lambda s: ((s > big).sum() + 1) / (len(s) + 4)),
                         "no-failure rate (avoid bottom quartile)": g.apply(lambda s: 1 - ((s < fail).sum() + 1) / (len(s) + 4)),
                         "median match value": g.median()})


def predictive(d, hp, rt):
    """Which estimator, fitted on 2022-24, best predicts a player's 2025-26 pressure performance?"""
    early = (d.year <= 2024).values
    late = ~early
    allm = np.ones(early.sum(), bool)
    z = lambda s: (s - s.mean()) / s.std()
    rows = []
    for role in ["bat", "bowl"]:
        T = {}
        for val in ["val", "wpali"]:
            e, _ = rate(d[late], role, hp=hp[late], rt=rt[late], val=val, min_hp=80, min_matches=6, model="direct", weights=(1, 0, 0))
            T[f"future pressure {val}"] = e.hp_raw
        T = pd.DataFrame(T)
        E = {}
        for model in ["direct", "hier", "blend"]:
            for val in ["val", "wpali"]:
                e, _ = rate(d[early], role, hp=hp[early], rt=rt[early], val=val, min_hp=80, min_matches=6, model=model, weights=(1, 0, 0))
                E[f"{model} / {val}: pressure rating"] = e.hp_val
                E[f"{model} / {val}: uplift vs usual"] = e.uplift
        for val in ["val", "wpali"]:
            e, _ = rate(d[early], role, hp=allm, rt=rt[early], val=val, min_hp=80, min_matches=6, model="direct", weights=(1, 0, 0))
            E[f"overall (all balls) / {val}"] = e.hp_val
        E = pd.DataFrame(E)
        j = E.join(T, how="inner")
        for c in E.columns:
            rows.append(dict(role=role, estimator=c, n=len(j), **{t: spearmanr(j[c], j[t], nan_policy="omit").statistic for t in T.columns}))
    return pd.DataFrame(rows)


def main():
    d = load()
    d["raw_bat"] = d.bat_runs.astype(float)
    d["raw_bowl"] = -d.bowl_runs.astype(float) + 25 * d.bowler_wkt
    log = {}

    # ---------- A. pressure definitions ----------
    tot_abs = d.WPA.abs().sum()
    sep, rows = [], []
    defs = {"PI - leverage x stakes (chosen)": "PI", "HEUR - hand-weighted stress score": "HEUR", "NAIVE - rule based": "NAIVE"}
    for lab, col in defs.items():
        hp, rt = flag_pressure(d, col)
        f = d.faced.values
        x = d[f]
        hpf, rtf = hp[f], rt[f]
        sep.append({"definition": lab, "share of balls flagged": hp.mean(),
                    "share of total |WPA| in flagged balls": d.WPA.abs()[hp].sum() / tot_abs,
                    "decisiveness ratio": (d.WPA.abs()[hp].sum() / tot_abs) / hp.mean(),
                    "dismissal % (pressure)": 100 * x.striker_out[hpf].mean(), "dismissal % (routine)": 100 * x.striker_out[rtf].mean(),
                    "dot % (pressure)": 100 * (x.bat_runs[hpf] == 0).mean(), "dot % (routine)": 100 * (x.bat_runs[rtf] == 0).mean(),
                    "boundary % (pressure)": 100 * (x.is_four | x.is_six)[hpf].mean(), "boundary % (routine)": 100 * (x.is_four | x.is_six)[rtf].mean(),
                    "run rate (pressure)": 6 * d.team_runs[hp].sum() / d.is_legal[hp].sum(), "run rate (routine)": 6 * d.team_runs[rt].sum() / d.is_legal[rt].sum()})
        lenses = ["val", "wpali", "wpa", "raw"] if col == "PI" else ["val"]
        for role in ["bat", "bowl"]:
            for v in lenses:
                vv = f"raw_{role}" if v == "raw" else v
                sh, sd, n = split_half(d, role, hp, rt, vv, n_splits=10)
                tv, nt = temporal(d, role, hp, rt, vv)
                rows.append(dict(definition=lab, role=role, value_lens=v, split_half_rho=sh, sd=sd, n_players=n, temporal_rho=tv, n_temporal=nt))
                print(rows[-1], flush=True)
    pd.DataFrame(sep).to_csv(OUT / "val_pressure_definitions.csv", index=False)
    pd.DataFrame(rows).to_csv(OUT / "val_reliability.csv", index=False)

    # ---------- A2. predictive validity of rating models ----------
    hp, rt = flag_pressure(d, "PI")
    pv = predictive(d, hp, rt)
    pv.to_csv(OUT / "val_predictive.csv", index=False)
    print(pv.round(3).to_string())

    # ---------- B. high-pressure threshold ----------
    thr = []
    for q in [0.60, 0.70, 0.75, 0.80, 0.85]:
        hp, rt = flag_pressure(d, "PI", hp_q=q)
        for role in ["bat", "bowl"]:
            sh, sd, n = split_half(d, role, hp, rt, "val", n_splits=10)
            su, _, _ = split_half(d, role, hp, rt, "val", field="uplift", n_splits=10)
            thr.append(dict(top_share=f"top {int(round((1 - q) * 100))}%", role=role, quality_rho=sh, uplift_rho=su, n_players=n))
            print(thr[-1], flush=True)
    pd.DataFrame(thr).to_csv(OUT / "val_threshold.csv", index=False)

    # ---------- C. consistency formulations + component reliability -> weights ----------
    hp, rt = flag_pressure(d, "PI")
    cons_rows, comp_rows, weights = [], [], {}
    for role in ["bat", "bowl"]:
        e, _ = rate(d, role, hp=hp, rt=rt, min_hp=100, min_matches=8, weights=(1, 0, 0))
        acc = []
        for a in halves(d, N_SPLITS, SEED + 1):
            A = consistency_variants(d[a], role, hp[a], e.index)
            B = consistency_variants(d[~a], role, hp[~a], e.index)
            j = A.join(B, rsuffix="_b", how="inner")
            acc.append({c: spearmanr(j[c], j[c + "_b"]).statistic for c in A.columns})
        for k, v in pd.DataFrame(acc).mean().items():
            cons_rows.append(dict(role=role, formulation=k, split_half_rho=v))
        rel = {}
        for f in ["hp_val", "uplift", "consistency"]:
            sh, sd, n = split_half(d, role, hp, rt, "val", field=f)
            rel[f] = max(sh, 0.0)
            comp_rows.append(dict(role=role, component=f, split_half_rho=sh, sd=sd))
        # reliability-proportional weights, with a floor on the uplift term (the brief asks for it)
        from config import MIN_UPLIFT_WEIGHT
        rest = {k: v for k, v in rel.items() if k != "uplift"}
        wu = max(MIN_UPLIFT_WEIGHT, rel["uplift"] / sum(rel.values()))
        tot = sum(rest.values())
        weights[role] = [round((1 - wu) * rest["hp_val"] / tot, 3), round(wu, 3), round((1 - wu) * rest["consistency"] / tot, 3)]
    pd.DataFrame(cons_rows).to_csv(OUT / "val_consistency.csv", index=False)
    pd.DataFrame(comp_rows).to_csv(OUT / "val_components.csv", index=False)
    (OUT / "weights.json").write_text(json.dumps(weights, indent=2))
    print("weights", weights)

    # composite reliability with the derived weights
    comp2 = []
    for role in ["bat", "bowl"]:
        e, _ = rate(d, role, hp=hp, rt=rt, min_hp=100, min_matches=8)
        rs = []
        for a in halves(d, N_SPLITS, SEED + 2):
            ea, _ = rate(d[a], role, hp=hp[a], rt=rt[a], eligible=e.index)
            eb, _ = rate(d[~a], role, hp=hp[~a], rt=rt[~a], eligible=e.index)
            j = ea[["score"]].join(eb[["score"]], rsuffix="_b").dropna()
            rs.append(spearmanr(j.score, j.score_b).statistic)
        comp2.append(dict(role=role, component="composite score", split_half_rho=np.mean(rs), sd=np.std(rs)))
    pd.concat([pd.DataFrame(comp_rows), pd.DataFrame(comp2)]).to_csv(OUT / "val_components.csv", index=False)
    print(pd.DataFrame(comp2))

    # ---------- C2. model comparison on the final composite ----------
    mc = []
    early = (d.year <= 2024).values
    for model in ["direct", "hier", "blend"]:
        for role in ["bat", "bowl"]:
            for wname, w in [("pressure rating only", (1, 0, 0)), ("full composite", tuple(weights[role]))]:
                e, _ = rate(d, role, hp=hp, rt=rt, min_hp=100, min_matches=8, model=model, weights=w)
                rs = []
                for a in halves(d, 10, SEED + 3):
                    ea, _ = rate(d[a], role, hp=hp[a], rt=rt[a], eligible=e.index, model=model, weights=w)
                    eb, _ = rate(d[~a], role, hp=hp[~a], rt=rt[~a], eligible=e.index, model=model, weights=w)
                    j = ea[["score"]].join(eb[["score"]], rsuffix="_b")
                    rs.append(spearmanr(j.score, j.score_b).statistic)
                ee, _ = rate(d[early], role, hp=hp[early], rt=rt[early], min_hp=80, min_matches=6, model=model, weights=w)
                fut, _ = rate(d[~early], role, hp=hp[~early], rt=rt[~early], min_hp=80, min_matches=6, model="direct", weights=(1, 0, 0))
                j = ee[["score"]].join(fut[["hp_raw"]], how="inner")
                mc.append(dict(model=model, role=role, score=wname, split_half_rho=np.mean(rs),
                               predicts_2025_26_pressure=spearmanr(j.score, j.hp_raw).statistic, n_pred=len(j)))
                print(mc[-1], flush=True)
    pd.DataFrame(mc).to_csv(OUT / "val_models.csv", index=False)

    # ---------- D. sensitivity of the final top-10 ----------
    sens = []
    for role in ["bat", "bowl"]:
        base, _ = rate(d, role, hp=hp, rt=rt)
        top = set(base.index[:10])
        ov = lambda e: len(top & set(e.index[:10]))
        for q in [0.65, 0.75, 0.80]:
            h2, r2 = flag_pressure(d, "PI", hp_q=q)
            sens.append(dict(role=role, variant=f"pressure = top {int(round((1 - q) * 100))}% of balls", overlap=ov(rate(d, role, hp=h2, rt=r2)[0])))
        for w in [(1, 0, 0), (0.5, 0.25, 0.25), (1 / 3, 1 / 3, 1 / 3), (0.6, 0.2, 0.2), (0.4, 0.4, 0.2), (0.4, 0.2, 0.4)]:
            sens.append(dict(role=role, variant="weights Q/U/C = " + "/".join(f"{x:.2f}" for x in w), overlap=ov(rate(d, role, hp=hp, rt=rt, weights=w)[0])))
        for mh in [120, 200]:
            sens.append(dict(role=role, variant=f"min pressure balls = {mh}", overlap=ov(rate(d, role, hp=hp, rt=rt, min_hp=mh)[0])))
        dd = d.copy(); dd["w_bat"] = 1.0; dd["w_bowl"] = 1.0
        sens.append(dict(role=role, variant="no opposition down-weighting", overlap=ov(rate(dd, role, hp=hp, rt=rt)[0])))
        dd = d.copy(); w = 0.5 ** ((2026 - dd.year) / 2.0); dd["w_bat"] *= w; dd["w_bowl"] *= w
        sens.append(dict(role=role, variant="recency decay (half-life 2 seasons)", overlap=ov(rate(dd, role, hp=hp, rt=rt)[0])))
        h3, r3 = flag_pressure(d, "LI_c")
        sens.append(dict(role=role, variant="no knock-out stakes multiplier", overlap=ov(rate(d, role, hp=h3, rt=r3)[0])))
        sens.append(dict(role=role, variant="WPA/LI lens instead of run value", overlap=ov(rate(d, role, hp=hp, rt=rt, val="wpali")[0])))
        sens.append(dict(role=role, variant="direct model only (pressure sample only)", overlap=ov(rate(d, role, hp=hp, rt=rt, model="direct")[0])))
        sens.append(dict(role=role, variant="hierarchical model only", overlap=ov(rate(d, role, hp=hp, rt=rt, model="hier")[0])))
        ipl = (d.comp_kind == "IPL").values
        sens.append(dict(role=role, variant="IPL deliveries only", overlap=ov(rate(d[ipl], role, hp=hp[ipl], rt=rt[ipl], min_hp=100, min_matches=8)[0])))
    sens = pd.DataFrame(sens)
    sens.to_csv(OUT / "val_sensitivity.csv", index=False)
    print(sens.to_string())


if __name__ == "__main__":
    main()
