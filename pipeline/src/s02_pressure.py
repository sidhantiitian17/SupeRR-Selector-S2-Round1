"""Step 2 - Quantify pressure on every delivery.

Pressure Index (PI) = Leverage Index (LI) x stakes multiplier.

  * A win-probability (WP) model is trained per innings (gradient boosting with
    monotone constraints, grouped 5-fold CV so every WP is out-of-fold).
  * An outcome model gives P(dot,1,2,3,4,6,wicket,extra | state).
  * LI_raw(state) = sum_o P(o|state) * |WP(next_state_o) - WP(state)|
    i.e. the expected swing in the batting side's chance of winning that this
    single delivery will cause.  LI = LI_raw / mean(LI_raw)  (1.0 = average ball).
  * Knock-out matches get a 1.15 stakes multiplier.

A heuristic index (situational stress score) is also computed so the two
definitions can be compared in s05_validate.py.
"""
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
from config import OUT, SEED, path

LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=200,
           subsample=0.8, subsample_freq=1, colsample_bytree=0.9, reg_lambda=1.0,
           random_state=SEED, verbose=-1)


def elo_ratings(d):
    """Pre-match Elo for each side (K=24, home advantage ignored), from results only."""
    m = pd.read_csv(path("matches")).sort_values(["match_date", "match_id"])
    r, pre = {}, {}
    for row in m.itertuples():
        h, a = row.home_team_id, row.away_team_id
        rh, ra = r.get(h, 1500.0), r.get(a, 1500.0)
        pre[(row.match_id, h)], pre[(row.match_id, a)] = rh, ra
        if pd.isna(row.win_team_id) or row.win_team_id == 0 or "Abandon" in str(row.result) or "No Result" in str(row.result):
            continue
        eh = 1 / (1 + 10 ** ((ra - rh) / 400))
        sh = 1.0 if row.win_team_id == h else 0.0
        r[h], r[a] = rh + 24 * (sh - eh), ra - 24 * (sh - eh)
    d["elo_bat"] = [pre.get((mid, t), 1500.0) for mid, t in zip(d.match_id, d.batting_team_id)]
    d["elo_bowl"] = [pre.get((mid, t), 1500.0) for mid, t in zip(d.match_id, d.bowling_team_id)]
    d["elo_diff"] = d.elo_bat - d.elo_bowl
    return d


F1 = ["balls_left", "wkts_left", "score_before", "elo_diff"]
M1 = [1, 1, 1, 1]
F2 = ["balls_left", "wkts_left", "runs_needed", "elo_diff"]
M2 = [1, 1, -1, 1]
OUTCOMES = np.array([0, 1, 2, 3, 4, 6])  # classes 0-5 runs, 6 = wicket, 7 = extra (wide/no-ball)


def outcome_class(d):
    cls = np.select([d.team_wkt & d.is_legal, ~d.is_legal], [6, 7], default=-1)
    r = d.team_runs.clip(upper=6).replace(5, 4)
    runs_cls = np.searchsorted(OUTCOMES, r.values)
    return np.where(cls == -1, runs_cls, cls)


def wp_inn2(model, balls_left, wkts_left, runs_needed, elo_diff):
    """WP for chasing side with explicit terminal states."""
    X = pd.DataFrame({"balls_left": balls_left, "wkts_left": wkts_left, "runs_needed": runs_needed, "elo_diff": elo_diff})
    p = np.zeros(len(X))
    won = X.runs_needed <= 0
    dead = (~won) & ((X.wkts_left <= 0) | (X.balls_left <= 0))
    live = ~(won | dead)
    if live.any():
        p[live.values] = model.predict_proba(X.loc[live, F2])[:, 1]
    p[won.values] = 1.0
    p[(dead & (X.runs_needed == 1)).values] = 0.5  # tie -> super over coin flip
    return p


def wp_inn1(m1, m2, balls_left, wkts_left, score, elo_diff, max_balls2):
    X = pd.DataFrame({"balls_left": balls_left, "wkts_left": wkts_left, "score_before": score, "elo_diff": elo_diff})
    p = np.zeros(len(X))
    # Terminal states of innings 1 are scored with the same innings-1 model
    # (balls_left=0 / wkts_left=0 fall in the model's lowest bins).  Switching to
    # the chase model at the boundary created artificial leverage spikes on the
    # last ball of the innings (diagnosed in iteration 1, see report).
    X["balls_left"] = X.balls_left.clip(lower=0)
    X["wkts_left"] = X.wkts_left.clip(lower=0)
    return m1.predict_proba(X[F1])[:, 1]


def main():
    d = pd.read_parquet(OUT / "deliveries.parquet")
    d = elo_ratings(d)
    d["outcome"] = outcome_class(d)
    d["max_balls2"] = d.groupby("match_id").max_balls.transform("last")
    d["WP"] = np.nan
    d["LI_raw"] = np.nan
    lab = d.bat_won.notna()

    gkf = GroupKFold(n_splits=5)
    folds = list(gkf.split(d, groups=d.match_id))
    # outcome model features (state-dependent risk profile)
    FO = ["innings", "balls_left", "wkts_left", "score_before", "runs_needed", "elo_diff"]
    metrics = []
    for k, (tr, te) in enumerate(folds):
        tr_idx = d.index[tr]
        te_idx = d.index[te]
        trl = tr_idx[lab[tr_idx]]
        a1 = trl[d.loc[trl, "innings"] == 1]
        a2 = trl[d.loc[trl, "innings"] == 2]
        m1 = lgb.LGBMClassifier(**LGB, monotone_constraints=M1).fit(d.loc[a1, F1], d.loc[a1, "bat_won"].astype(int))
        m2 = lgb.LGBMClassifier(**LGB, monotone_constraints=M2).fit(d.loc[a2, F2], d.loc[a2, "bat_won"].astype(int))
        mo = lgb.LGBMClassifier(**{**LGB, "n_estimators": 200}, objective="multiclass").fit(d.loc[tr_idx, FO], d.loc[tr_idx, "outcome"])

        t = d.loc[te_idx]
        i1, i2 = (t.innings == 1).values, (t.innings == 2).values
        wp_now = np.zeros(len(t))
        wp_now[i1] = wp_inn1(m1, m2, t.balls_left[i1], t.wkts_left[i1], t.score_before[i1], t.elo_diff[i1], t.max_balls2[i1])
        wp_now[i2] = wp_inn2(m2, t.balls_left[i2], t.wkts_left[i2], t.runs_needed[i2], t.elo_diff[i2])
        P = mo.predict_proba(t[FO])
        li = np.zeros(len(t))
        for o in range(8):
            runs = OUTCOMES[o] if o < 6 else (0 if o == 6 else 1)
            dball = 0 if o == 7 else 1
            dwk = 1 if o == 6 else 0
            bl, wl = t.balls_left.values - dball, t.wkts_left.values - dwk
            nxt = np.zeros(len(t))
            nxt[i1] = wp_inn1(m1, m2, bl[i1], wl[i1], t.score_before.values[i1] + runs, t.elo_diff.values[i1], t.max_balls2.values[i1])
            nxt[i2] = wp_inn2(m2, bl[i2], wl[i2], t.runs_needed.values[i2] - runs, t.elo_diff.values[i2])
            li += P[:, o] * np.abs(nxt - wp_now)
        # WP after the actual delivery (same model -> consistent WPA)
        dball = t.is_legal.values.astype(int)
        bl, wl = t.balls_left.values - dball, t.wkts_left.values - t.team_wkt.values.astype(int)
        aft = np.zeros(len(t))
        aft[i1] = wp_inn1(m1, m2, bl[i1], wl[i1], t.score_before.values[i1] + t.team_runs.values[i1], t.elo_diff.values[i1], t.max_balls2.values[i1])
        aft[i2] = wp_inn2(m2, bl[i2], wl[i2], t.runs_needed.values[i2] - t.team_runs.values[i2], t.elo_diff.values[i2])
        d.loc[te_idx, "WP_after"] = aft
        d.loc[te_idx, "WP"] = wp_now
        d.loc[te_idx, "LI_raw"] = li
        for inn, msk in [(1, i1), (2, i2)]:
            y = t.bat_won.values[msk]
            ok = ~np.isnan(y)
            metrics.append(dict(fold=k, innings=inn, auc=roc_auc_score(y[ok], wp_now[msk][ok]),
                                brier=brier_score_loss(y[ok], wp_now[msk][ok]),
                                logloss=log_loss(y[ok], np.clip(wp_now[msk][ok], 1e-4, 1 - 1e-4))))
        print(f"fold {k} done")
    met = pd.DataFrame(metrics).groupby("innings")[["auc", "brier", "logloss"]].mean()
    print("[WP model, out-of-fold]\n", met.round(4))
    met.to_csv(OUT / "wp_model_metrics.csv")

    # calibration table
    cal = d[lab].assign(bin=pd.cut(d.WP, np.linspace(0, 1, 11), include_lowest=True))
    cal.groupby(["innings", "bin"], observed=True).agg(pred=("WP", "mean"), obs=("bat_won", "mean"), n=("WP", "size")).to_csv(OUT / "wp_calibration.csv")

    d["WPA"] = d.WP_after - d.WP  # batting side's win-probability added on this delivery

    # ---- Pressure Index ----
    d["LI"] = d.LI_raw / d.LI_raw.mean()
    d["stakes"] = np.where(d.knock_out == 1, 1.15, 1.0)
    d["PI"] = d.LI * d.stakes

    # ---- Heuristic alternative (for comparison only) ----
    # chase: required-rate gap, wickets in hand, balls left; 1st innings: wickets lost vs par + death overs
    gap = (d.rrr - d.crr.fillna(d.rrr)).clip(-6, 12).fillna(0)
    rec_w = d.groupby(["match_id", "innings"]).team_wkt.transform(lambda s: s.astype(int).shift(1, fill_value=0).rolling(12, min_periods=1).sum())
    h = (0.35 * np.where(d.innings == 2, gap / 6, 0) + 0.25 * (d.wkts_before / 10) + 0.2 * rec_w / 2
         + 0.2 * (d.over_no >= 16) + np.where(d.innings == 2, 0.3 * (1 - (d.WP - 0.5).abs() * 2), 0))
    d["HEUR"] = (h - h.min()) / (h - h.min()).mean()
    d["recent_wkts"] = rec_w

    d.drop(columns=["max_balls2"]).to_parquet(OUT / "deliveries_pressure.parquet", index=False)
    print(d.groupby(["innings", "phase"]).PI.describe().round(2))
    print("[OK] wrote deliveries_pressure.parquet")


if __name__ == "__main__":
    main()
