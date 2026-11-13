"""Step 4 - Final ratings, cluster (match-level) bootstrap and evidence tables."""
import numpy as np
import pandas as pd
from config import OUT, SEED, BOOTSTRAP_ITERS
from ratings import load, rate, names, flag_pressure, ROLE


def box(d, role, mask):
    r = ROLE[role]
    x = d[mask]
    if role == "bat":
        x = x[x.faced]
        g = x.groupby("striker_id")
        t = pd.DataFrame({"runs": g.bat_runs.sum(), "balls": g.is_legal.sum() + g.is_noball.sum(),
                          "outs": g.striker_out.sum(), "dots": g.bat_runs.apply(lambda s: (s == 0).sum()),
                          "bnd": g.is_four.sum() + g.is_six.sum(), "wpa": g.bat_wpa.sum()})
        t["SR"] = 100 * t.runs / t.balls
        t["avg"] = t.runs / t.outs.replace(0, np.nan)
        t["dot%"] = 100 * t.dots / t.balls
        t["bnd%"] = 100 * t.bnd / t.balls
    else:
        g = x.groupby("bowler_id")
        t = pd.DataFrame({"balls": g.is_legal.sum(), "runs": g.bowl_runs.sum(), "wkts": g.bowler_wkt.sum(),
                          "dots": x.assign(dot=(x.bowl_runs == 0) & x.is_legal).groupby("bowler_id").dot.sum(),
                          "wpa": g.bowl_wpa.sum()})
        t["econ"] = 6 * t.runs / t.balls
        t["bSR"] = t.balls / t.wkts.replace(0, np.nan)
        t["dot%"] = 100 * t.dots / t.balls
    return t


def main():
    d = load()
    nm = names(d)
    hp, rt = flag_pressure(d)
    rng = np.random.default_rng(SEED)
    matches = d.match_id.unique()
    res = {}
    for role in ["bat", "bowl"]:
        e, full = rate(d, role, hp=hp, rt=rt)
        elig = e.index
        # ---- Poisson cluster bootstrap over matches ----
        ranks = []
        for b in range(BOOTSTRAP_ITERS):
            mw = pd.Series(rng.poisson(1.0, len(matches)), index=matches)
            db = d.assign(mw=d.match_id.map(mw).values)
            eb, _ = rate(db, role, hp=hp, rt=rt, eligible=elig)
            ranks.append(eb["rank"])
        R = pd.concat(ranks, axis=1)
        e["boot_median_rank"] = R.median(axis=1)
        e["rank_p05"] = R.quantile(0.05, axis=1)
        e["rank_p95"] = R.quantile(0.95, axis=1)
        e["p_top10"] = (R <= 10).mean(axis=1)
        e["p_top20"] = (R <= 20).mean(axis=1)
        # ---- traditional evidence ----
        bh, br = box(d, role, hp), box(d, role, rt)
        e = e.join(bh.add_prefix("P_")).join(br.add_prefix("R_"))
        # interpretable run-currency lens (runs above expected per 100 balls, wicket-adjusted)
        ev, _ = rate(d, role, hp=hp, rt=rt, val="val", eligible=elig)
        e["runs_above_exp_100_P"] = ev.hp_raw * 100
        e["runs_above_exp_100_R"] = ev.rt_raw * 100
        # IPL vs T20I split of pressure value (raw per 100 balls)
        for kind in ["IPL", "T20I"]:
            k = hp & (d.comp_kind == kind).values
            ek, _ = rate(d, role, hp=k, rt=rt, eligible=elig)
            e[f"hp_raw_{kind}"] = ek.hp_raw.reindex(e.index) * 100
            e[f"hp_balls_{kind}"] = ek.balls.reindex(e.index)
        e.insert(0, "player", e.index.map(nm))
        # values are in win-probability percentage points per ball (at average leverage) -> per 100 balls
        e["hp_val_100"] = e.hp_val * 100
        e["rt_val_100"] = e.rt_val * 100
        e["uplift_100"] = e.uplift * 100
        e["hp_raw_100"] = e.hp_raw * 100
        e["rt_raw_100"] = e.rt_raw * 100
        e.to_csv(OUT / f"ratings_{role}.csv")
        res[role] = e
        print(f"\n===== TOP 10 {role.upper()} (eligible {len(e)}) =====")
        cols = ["player", "balls", "matches", "hp_raw_100", "hp_val_100", "rt_val_100", "uplift_100", "consistency", "runs_above_exp_100_P",
                "score", "boot_median_rank", "rank_p05", "rank_p95", "p_top10"]
        print(e[cols].head(15).round(2).to_string())
    top = pd.DataFrame({"rank": range(1, 11),
                        "batter": res["bat"].player.head(10).values,
                        "bowler": res["bowl"].player.head(10).values})
    top.to_csv(OUT / "FINAL_TOP10.csv", index=False)
    print("\n", top.to_string(index=False))


if __name__ == "__main__":
    main()
