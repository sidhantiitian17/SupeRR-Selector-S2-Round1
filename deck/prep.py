"""Collect every number the deck shows from the pipeline outputs into deck/build/data.json."""
import pandas as pd, numpy as np, json, re, pathlib
HERE = pathlib.Path(__file__).resolve().parent
R = HERE.parent; O = R/"pipeline/outputs"
(HERE/"build").mkdir(exist_ok=True)
d = pd.read_parquet(O/"deliveries_value.parquet")
d["hp"] = d.PI >= d.PI.quantile(0.70)
teams = pd.read_csv(R/"data/raw/teams.csv"); tn = {(r.comp_id, r.team_id): r.team_name for r in teams.itertuples()}


def rr_gaps(d):
    """RR (team_id 3) vs the other IPL teams on pressure balls, IPL 2025-26, by phase (and pace/spin for bowling)."""
    y = d[(d.kind_ipl == 1) & (d.year.isin([2025, 2026])) & d.hp]
    rows = []
    for side, col, val, team in (("bat", "faced", "bat_val", "batting_team_id"), ("bowl", "is_legal", "bowl_val", "bowling_team_id")):
        for ph in ["PP", "MID", "DEATH"]:
            z = y[y.phase == ph]
            g = z.groupby(team).apply(lambda q: pd.Series({"v": q[val].sum() / q[col].sum() * 100, "rpo": q.team_runs.sum() / q[col].sum() * 6, "n": q[col].sum()}))
            g = g.sort_values("v", ascending=False)
            rows.append({"side": side, "seg": ph, "RR balls": int(g.loc[3, "n"]), "RR val/100": round(g.loc[3, "v"], 1), "median team": round(g.v.median(), 1),
                         "RR rank/10": list(g.index).index(3) + 1, "RR rpo": round(g.loc[3, "rpo"], 2), "median rpo": round(g.rpo.median(), 2)})
    return rows


def profiles(d):
    """Phase split of each top-10 player's pressure balls (Pressure Index top 30%), last IPL team, record vs spin."""
    top = pd.read_csv(O/"FINAL_TOP10_HYBRID.csv")
    res = {"bat": [], "bowl": []}
    for role, col, val, pid, team, names, nm in (("bat", "faced", "bat_val", "striker_id", "batting_team_id", "batter", "striker_name"),
                                                ("bowl", "is_legal", "bowl_val", "bowler_id", "bowling_team_id", "bowler", "bowler_name")):
        for i, name in enumerate(top[names]):
            q = d[d[nm] == name]; h = q[q.hp]; ph = {}
            for p in ["PP", "MID", "DEATH"]:
                z = h[h.phase == p]; n = int(z[col].sum())
                ph[p] = {"n": n, "share": round(n / h[col].sum() * 100), "v": round(float(z[val].sum()) / max(n, 1) * 100, 1),
                         "rpo": round(float(z.team_runs.sum()) / max(n, 1) * 6, 2) if role == "bowl" else round(float(z.bat_runs.sum()) / max(n, 1) * 100, 1)}
            last = q[q.kind_ipl == 1].sort_values("match_date").tail(1)
            iplteam = tn.get((int(last.comp_id.iloc[0]), int(last[team].iloc[0]))) if len(last) else None
            vs = None
            if role == "bat":
                s_ = h[h.is_spin == 1]; vs = {"n": int(s_.faced.sum()), "sr": round(float(s_.bat_runs.sum()) / max(s_.faced.sum(), 1) * 100, 1)}
            res[role].append({"rank": i + 1, "name": name, "id": int(q[pid].iloc[0]), "phases": ph, "last_ipl_team": iplteam,
                              "last_ipl_year": int(last.year.iloc[0]) if len(last) else None, "vs_spin": vs})
    return res

J = {}
J["n_matches"] = int(d.match_id.nunique()); J["n_balls"] = int(len(d))
J["pi_cut"] = float(d.PI.quantile(0.70))
v = d.groupby(["year", "comp_kind"]).match_id.nunique().unstack(fill_value=0)
J["volume"] = {str(k): {c: int(v.loc[k, c]) for c in v.columns} for k in v.index}
J["comp_kinds"] = list(map(str, v.columns))
J["n_players_bat"] = int(d.striker_id.nunique()); J["n_players_bowl"] = int(d.bowler_id.nunique())
# example chase: match 50349
m = d[(d.match_id == 50349)].sort_values(["innings", "innings_ball_num"])
c = m[m.innings == 2]
J["example"] = {"bat": tn[(int(c.comp_id.iloc[0]), int(c.batting_team_id.iloc[0]))], "bowl": tn[(int(c.comp_id.iloc[0]), int(c.bowling_team_id.iloc[0]))],
  "date": str(c.match_date.iloc[0])[:10], "target": int(c.target.iloc[0]), "bat_won": int(c.bat_won.iloc[0]),
  "balls": [{"i": i, "ov": int(r.over_no), "wp": round(float(r.WP), 4), "wpa": round(float(r.WP_after), 4), "pi": round(float(r.PI), 3), "hp": bool(r.hp),
             "need": int(r.runs_needed), "left": int(r.balls_left), "w": int(r.wkts_before), "runs": int(r.team_runs), "wk": int(r.team_wkt), "s": r.striker_name, "b": r.bowler_name}
            for i, r in enumerate(c.itertuples())]}
cal = pd.read_csv(O/"wp_calibration.csv"); J["calibration"] = {str(k): g[["pred", "obs", "n"]].round(4).values.tolist() for k, g in cal.groupby("innings")}
J["wp_metrics"] = pd.read_csv(O/"wp_model_metrics.csv").round(3).to_dict("records")
pdf = pd.read_csv(O/"val_pressure_definitions.csv"); J["definitions"] = pdf.round(4).to_dict("records")
J["threshold"] = pd.read_csv(O/"val_threshold.csv").round(4).to_dict("records")
# pressure map: mean PI by over x wickets lost, per innings
pm = {}
for inn in (1, 2):
    z = d[d.innings == inn]; z = z.assign(w=z.wkts_before.clip(upper=7))
    t = z.groupby(["over_no", "w"]).agg(pi=("PI", "mean"), n=("PI", "size")).reset_index()
    pm[str(inn)] = [[int(r.over_no), int(r.w), round(float(r.pi), 3), int(r.n)] for r in t.itertuples()]
J["pressure_map"] = pm
ph = d[d.hp].groupby("phase").size(); J["hp_phase_share"] = {k: round(float(v / ph.sum() * 100), 1) for k, v in ph.items()}
J["wicket_cost"] = d.groupby(["phase"]).Wc.mean().round(2).to_dict()
# shrinkage illustration (batters, eligible pool)
hb = pd.read_csv(O/"hyb_ratings_bat.csv")
J["shrink"] = [[r.player, int(r.balls), round(r.hp_raw * 100, 1), round(r.hp_val * 100, 1)] for r in hb.itertuples()]
# tournament scatter
s = pd.read_csv(O/"hyb_selection.csv")
J["tournament"] = [[r.method, r.role, round(r.worst_cell, 3), round(r.mean_cell, 3), bool(r.chosen), bool(r.has_usual)] for r in s.itertuples()]
# top 10 evidence + bootstrap/spec support
top = pd.read_csv(O/"FINAL_TOP10_HYBRID.csv"); J["top"] = {}
for role, col in (("bat", "batter"), ("bowl", "bowler")):
    ev = pd.read_csv(O/f"hyb_evidence_{role}.csv"); hr = pd.read_csv(O/f"hyb_ratings_{role}.csv").set_index("player")
    rows = []
    for i, name in enumerate(top[col]):
        e = ev[ev.player == name].iloc[0].to_dict(); h = hr.loc[name]
        e = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in e.items()}
        e.update(rank=i + 1, p_top10=round(float(h.p_top10) * 100), specs=int(h.specs_in_top10), n_specs=int(h.n_specs),
                 rank_p05=int(h.rank_p05), rank_p95=int(h.rank_p95), pid=int(e.pop("Unnamed: 0")))
        rows.append(e)
    J["top"][role] = rows
J["profiles"] = profiles(d)
J["rr_gaps"] = rr_gaps(d)
w = (R/"dashboard/data/watchlist.js").read_text(); J["watch"] = json.loads(w[w.index("{"): w.rindex("}") + 1])
J["chosen"] = json.load(open(O/"hyb_chosen.json"))["chosen"]
(HERE/"build/data.json").write_text(json.dumps(J, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print("ok", J["n_matches"], J["n_balls"], J["example"]["bat"], "vs", J["example"]["bowl"], J["example"]["target"], "pi_cut", round(J["pi_cut"], 3), J["hp_phase_share"], J["wicket_cost"])
print(J["top"]["bat"][0]); print(list(J["watch"].keys())); print(J["volume"])

# ---- extras: worked value example, PI histogram, player-pick detail
J = json.loads((HERE/"build/data.json").read_text())
c = d[(d.match_id == 50349) & (d.innings == 2)].sort_values("innings_ball_num")
ex = []
for r in c.tail(6).itertuples():
    ex.append(dict(s=r.striker_name, b=r.bowler_name, need=int(r.runs_needed), left=int(r.balls_left), w=int(r.wkts_before), runs=int(r.bat_runs),
                   E=round(float(r.E_bat_runs), 2), Pout=round(float(r.P_out), 3), Wc=round(float(r.Wc), 2), val=round(float(r.bat_val), 2),
                   bval=round(float(r.bowl_val), 2), pi=round(float(r.PI), 2), wp=round(float(r.WP), 3), wpa=round(float(r.WP_after), 3), out=int(r.striker_out)))
J["value_example"] = ex
hist, edges = np.histogram(d.PI.clip(upper=4), bins=40, range=(0, 4))
J["pi_hist"] = {"counts": hist.tolist(), "edges": edges.round(2).tolist()}
J["pi_median"] = float(d.PI.median())
pick = {}
for name in ["Mohsin Khan", "Josh Hazlewood"]:
    q = d[d.bowler_name == name]; h = q[q.hp]
    pick[name] = {"seasons": [{"y": int(y), "pb": int(g.is_legal.sum()), "econ": round(g.team_runs.sum() / g.is_legal.sum() * 6, 2), "w": int(g.bowler_wkt.sum()),
                               "v": round(g.bowl_val.sum() / g.is_legal.sum() * 100, 1)} for y, g in h.groupby("year")],
                  "matches": int(q.match_id.nunique()), "ipl_share": round(float(h.kind_ipl.mean() * 100)),
                  "death": {"pb": int(h[h.phase == "DEATH"].is_legal.sum()), "econ": round(h[h.phase == "DEATH"].team_runs.sum() / max(h[h.phase == "DEATH"].is_legal.sum(), 1) * 6, 2),
                            "w": int(h[h.phase == "DEATH"].bowler_wkt.sum())},
                  "pp": {"pb": int(h[h.phase == "PP"].is_legal.sum()), "econ": round(h[h.phase == "PP"].team_runs.sum() / max(h[h.phase == "PP"].is_legal.sum(), 1) * 6, 2),
                         "w": int(h[h.phase == "PP"].bowler_wkt.sum())}}
J["pick"] = pick
# league pressure economy by phase for IPL 2025-26 (reference line for RR slides)
y = d[(d.kind_ipl == 1) & (d.year >= 2025) & d.hp]
J["league_phase_econ"] = {ph: round(g.team_runs.sum() / g.is_legal.sum() * 6, 2) for ph, g in y.groupby("phase")}
(HERE/"build/data.json").write_text(json.dumps(J, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print(json.dumps(ex, indent=0)[:1500]); print(json.dumps(pick)); print(J["league_phase_econ"], J["pi_median"])
