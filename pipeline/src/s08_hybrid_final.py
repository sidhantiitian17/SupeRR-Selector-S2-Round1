"""Final hybrid ratings: chosen method per role (from s07), bootstrap, specification support, evidence."""
import json
import numpy as np
import pandas as pd
from config import OUT, SEED
from hybrid import prep, candidates, a_tables, b_score
from ratings import names, flag_pressure

BOOT = 300
d, HP, RT = prep()
nm = names(d)
sel = pd.read_csv(OUT / "hyb_selection.csv", index_col=0)
chosen = {r: sel[(sel.role == r) & sel.chosen].index[0] for r in ["bat", "bowl"]}
near = {r: sel[(sel.role == r) & (sel.worst_cell >= sel[sel.role == r].worst_cell.max() - 0.05) & (sel.index != "random")].index.tolist() for r in ["bat", "bowl"]}
json.dump({"chosen": chosen, "near_best": near}, open(OUT / "hyb_chosen.json", "w"), indent=2)
print(chosen)
rng = np.random.default_rng(SEED)
mids = d.match_id.unique()


def top(x, role, hp, rt, name, frac=1.0, n=10):
    s = candidates(x, role, hp, rt, frac)[name].dropna().sort_values(ascending=False)
    return s


final = {}
for role in ["bat", "bowl"]:
    s = top(d, role, HP, RT, chosen[role])
    e, t = a_tables(d, role, HP, RT, 1.0)
    B = b_score(d, role)
    tab = pd.DataFrame({"score": s}).join(t[["hp_val", "hp_raw", "rt_raw", "uplift", "consistency", "balls", "matches"]]).join(B)
    tab["rank"] = np.arange(1, len(tab) + 1)
    # ---- bootstrap (Poisson match weights) ----
    R = []
    for b in range(BOOT):
        mw = pd.Series(rng.poisson(1.0, len(mids)), index=mids)
        db = d.assign(mw=d.match_id.map(mw).values)
        sb = top(db, role, HP, RT, chosen[role])
        R.append(pd.Series(np.arange(1, len(sb) + 1), index=sb.index))
        if b % 50 == 0:
            print(role, "boot", b, flush=True)
    R = pd.concat(R, axis=1).reindex(tab.index)
    tab["p_top10"] = (R <= 10).mean(axis=1)
    tab["rank_p05"] = R.quantile(0.05, axis=1)
    tab["rank_p95"] = R.quantile(0.95, axis=1)
    tab["boot_median_rank"] = R.median(axis=1)
    # ---- specification support ----
    specs = {}
    for nmspec in near[role]:
        specs[f"method: {nmspec}"] = top(d, role, HP, RT, nmspec).index[:10]
    masks = {"IPL only": d.comp_kind.eq("IPL").values, "T20I only": d.comp_kind.eq("T20I").values,
             "excl. Associate opposition": ~(d.bat_tier.eq("ASSOC") | d.bowl_tier.eq("ASSOC")).values,
             "chases only": d.innings.eq(2).values, "first innings only": d.innings.eq(1).values}
    for k, m in masks.items():
        x = d[m]
        f = x.match_id.nunique() / len(mids)
        specs[k] = top(x, role, HP[m], RT[m], chosen[role], frac=f).index[:10]
    for q in (0.65, 0.75):
        h2, r2 = flag_pressure(d, "PI", hp_q=q)
        specs[f"A pressure = top {int(round((1-q)*100))}%"] = top(d.assign(hpA=h2), role, h2, r2, chosen[role]).index[:10]
    dd = d.copy(); dd["w_bat"] = 1.0; dd["w_bowl"] = 1.0
    specs["no opposition down-weighting"] = top(dd, role, HP, RT, chosen[role]).index[:10]
    sp = pd.DataFrame({k: tab.index.isin(v) for k, v in specs.items()}, index=tab.index)
    tab["specs_in_top10"] = sp.sum(axis=1)
    tab["n_specs"] = sp.shape[1]
    sp.insert(0, "player", tab.index.map(nm))
    sp.head(30).to_csv(OUT / f"hyb_specs_{role}.csv")
    tab.insert(0, "player", tab.index.map(nm))
    tab.to_csv(OUT / f"hyb_ratings_{role}.csv")
    final[role] = tab
    print(tab.head(15).round(3).to_string())
pd.DataFrame({"rank": range(1, 11), "batter": final["bat"].player.head(10).values,
              "bowler": final["bowl"].player.head(10).values}).to_csv(OUT / "FINAL_TOP10_HYBRID.csv", index=False)
print(pd.read_csv(OUT / "FINAL_TOP10_HYBRID.csv").to_string(index=False))
