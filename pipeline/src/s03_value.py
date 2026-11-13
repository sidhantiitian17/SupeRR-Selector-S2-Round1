"""Step 3 - Context-adjusted value of every delivery for the batter and the bowler.

For each delivery we estimate, out-of-fold, what an *average* player would
produce in exactly that situation (innings, balls/wickets left, score, chase
equation, pressure level, team strengths, pace/spin, competition, season):

  E_bat_runs, P_out         (balls faced by the striker)
  E_bowl_runs, P_bwkt       (deliveries bowled)

A wicket is converted to runs with a state-dependent wicket cost
  Wc(state) = ER(balls_left, wkts_left) - ER(balls_left, wkts_left - 1)
from an expected-remaining-runs model ER (innings-1 data).

  bat_val  = (runs - E_bat_runs) - Wc * (out - P_out)              (runs above expected)
  bowl_val = (E_bowl_runs - runs_conceded) + Wc * (wicket - P_bwkt)
"""
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import GroupKFold
from config import OUT, SEED, OPP_WEIGHT

P = dict(n_estimators=250, learning_rate=0.05, num_leaves=31, min_child_samples=300,
         subsample=0.8, subsample_freq=1, colsample_bytree=0.9, random_state=SEED, verbose=-1)
FEAT = ["innings", "over_no", "balls_left", "wkts_left", "score_before", "runs_needed", "rrr", "crr",
        "elo_diff", "LI_c", "is_spin", "kind_ipl", "kind_em", "opp_assoc", "own_assoc", "year"]


def main():
    d = pd.read_parquet(OUT / "deliveries_pressure.parquet")
    cap = d.LI.quantile(0.995)
    d["LI_c"] = d.LI.clip(upper=cap)                       # winsorised leverage (robust to rain-reduced end-games)
    d["PI"] = d.LI_c * d.stakes
    d["is_spin"] = (d.pace_or_spin == "Spin").astype(int)
    d["kind_ipl"] = (d.comp_kind == "IPL").astype(int)
    d["kind_em"] = (d.comp_kind == "EMERGING").astype(int)
    d["opp_assoc"] = (d.bowl_tier == "ASSOC").astype(int)
    d["own_assoc"] = (d.bat_tier == "ASSOC").astype(int)

    # ---- expected remaining runs (innings 1) -> wicket cost ----
    i1 = d[d.innings == 1].copy()
    i1["rem"] = i1.first_total - i1.score_before
    er = lgb.LGBMRegressor(**P, monotone_constraints=[1, 1, 0]).fit(i1[["balls_left", "wkts_left", "elo_diff"]], i1.rem)
    X0 = pd.DataFrame({"balls_left": d.balls_left, "wkts_left": d.wkts_left, "elo_diff": 0.0})
    X1 = X0.assign(wkts_left=(d.wkts_left - 1).clip(lower=0), balls_left=(d.balls_left - 1).clip(lower=0))
    X0b = X0.assign(balls_left=(d.balls_left - 1).clip(lower=0))
    d["Wc"] = (er.predict(X0b) - er.predict(X1)).clip(min=0)
    d.loc[d.wkts_left <= 1, "Wc"] = d.loc[d.wkts_left <= 1, "Wc"].clip(lower=d.Wc.quantile(0.5))  # last wicket ends the innings

    faced = d.faced.values
    for col in ["E_bat_runs", "P_out", "E_bowl_runs", "P_bwkt"]:
        d[col] = np.nan
    for tr, te in GroupKFold(n_splits=5).split(d, groups=d.match_id):
        tr_f = tr[faced[tr]]
        te_f = te[faced[te]]
        X = d[FEAT]
        m = lgb.LGBMRegressor(**P, objective="poisson").fit(X.iloc[tr_f], d.bat_runs.iloc[tr_f])
        d.loc[d.index[te_f], "E_bat_runs"] = m.predict(X.iloc[te_f])
        m = lgb.LGBMClassifier(**P).fit(X.iloc[tr_f], d.striker_out.iloc[tr_f].astype(int))
        d.loc[d.index[te_f], "P_out"] = m.predict_proba(X.iloc[te_f])[:, 1]
        m = lgb.LGBMRegressor(**P, objective="poisson").fit(X.iloc[tr], d.bowl_runs.iloc[tr])
        d.loc[d.index[te], "E_bowl_runs"] = m.predict(X.iloc[te])
        m = lgb.LGBMClassifier(**P).fit(X.iloc[tr], d.bowler_wkt.iloc[tr].astype(int))
        d.loc[d.index[te], "P_bwkt"] = m.predict_proba(X.iloc[te])[:, 1]
        print("fold done")

    d["bat_val"] = np.where(faced, (d.bat_runs - d.E_bat_runs) - d.Wc * (d.striker_out.astype(int) - d.P_out), np.nan)
    d["bowl_val"] = (d.E_bowl_runs - d.bowl_runs) + d.Wc * (d.bowler_wkt.astype(int) - d.P_bwkt)
    # win-probability lens: batter credited with WPA on balls he faces; bowler with -WPA
    d["bat_wpa"] = np.where(faced, d.WPA, np.nan)
    d["bowl_wpa"] = -d.WPA
    # opposition-strength weights (balls vs Associates count for less)
    d["w_bat"] = d.bowl_tier.map(OPP_WEIGHT)
    d["w_bowl"] = d.bat_tier.map(OPP_WEIGHT)

    print("calibration check (should be ~0):",
          round(np.nanmean(d.bat_val), 4), round(np.nanmean(d.bowl_val), 4))
    print("mean wicket cost by phase:\n", d.groupby(["innings", "phase"]).Wc.mean().round(2))
    d.to_parquet(OUT / "deliveries_value.parquet", index=False)
    print("[OK] wrote deliveries_value.parquet")


if __name__ == "__main__":
    main()
