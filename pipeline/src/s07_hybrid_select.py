"""Held-out tournament that chooses the hybrid.

Every candidate ranks players on TRAINING matches only; its top 10 are then scored on
UNSEEN matches against 8 targets (2 pressure definitions x 4 measures, so neither solution's
own target dominates).  Schemes: 30 random half-splits and 6 past->future cuts.
Gain = (mean held-out value of the selected 10 - pool mean) / pool SD.
Rule (fixed in advance, from solution B): choose the candidate with the best WORST cell
(16 cells = 8 targets x 2 schemes); among candidates within 0.03 of it, take the best mean.
Constraint (from the brief): only candidates whose score contains the pressure-vs-usual-level
comparison are eligible to be chosen.  The best unconstrained candidate is also reported so the
cost of the constraint is visible.
"""
import numpy as np
import pandas as pd
from config import OUT, SEED
from hybrid import prep, candidates, targets, has_usual

d, HP, RT = prep()
rng = np.random.default_rng(SEED)
mids = d.match_id.unique()
order = d.groupby("match_id").match_date.first().sort_values().index.to_numpy()
splits = [("random", rng.choice(mids, len(mids) // 2, replace=False)) for _ in range(30)]
splits += [("future", order[: int(q * len(order))]) for q in (0.5, 0.57, 0.64, 0.71, 0.78, 0.85)]

rows = []
for k, (scheme, train_ids) in enumerate(splits):
    tr = d.match_id.isin(set(train_ids)).values
    frac = tr.mean()
    a, b = d[tr], d[~tr]
    for role in ["bat", "bowl"]:
        T = targets(b, role)
        for name, s in candidates(a, role, HP[tr], RT[tr], frac).items():
            sel = s.dropna().sort_values(ascending=False).index[:10]
            g = (T.reindex(sel).mean() - T.mean()) / T.std()
            rows.append(dict(split=k, scheme=scheme, role=role, method=name, **g.to_dict()))
        sel = rng.choice(T.index.to_numpy(), 10, replace=False)
        rows.append(dict(split=k, scheme=scheme, role=role, method="random", **((T.reindex(sel).mean() - T.mean()) / T.std()).to_dict()))
    print("split", k, scheme, flush=True)

R = pd.DataFrame(rows)
R.to_csv(OUT / "hyb_tournament_raw.csv", index=False)
tc = [c for c in R.columns if "|" in c and c not in ("method",)]
res = []
for role in ["bat", "bowl"]:
    cells = R[R.role == role].groupby(["method", "scheme"])[tc].mean()
    cell = cells.unstack("scheme")
    se = R[R.role == role].groupby(["method", "scheme"])[tc].sem().unstack("scheme")
    summ = pd.DataFrame({"worst_cell": cell.min(axis=1), "mean_cell": cell.mean(axis=1),
                         "random_mean": cells.xs("random", level="scheme").mean(axis=1).reindex(cell.index),
                         "future_mean": cells.xs("future", level="scheme").mean(axis=1).reindex(cell.index),
                         "worst_cell_name": cell.idxmin(axis=1).astype(str)})
    summ["role"] = role
    summ["has_usual"] = [has_usual(k) for k in summ.index]
    def pick(pool):
        best = pool.worst_cell.max()
        tied = pool[pool.worst_cell >= best - 0.03]
        return tied.mean_cell.idxmax()
    cand = summ.drop("random")
    summ["chosen"] = summ.index == pick(cand[cand.has_usual])
    summ["best_unconstrained"] = summ.index == pick(cand)
    res.append(summ.sort_values("worst_cell", ascending=False))
    cell.to_csv(OUT / f"hyb_cells_{role}.csv")
S = pd.concat(res)
S.to_csv(OUT / "hyb_selection.csv")
pd.set_option("display.width", 220)
print(S.round(3).to_string())
