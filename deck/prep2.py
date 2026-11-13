import pandas as pd, numpy as np, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
d = pd.read_parquet(HERE.parent / "pipeline/outputs/deliveries_value.parquet"); d["hp"] = d.PI >= d.PI.quantile(0.70)
J = json.loads((HERE / "build/data.json").read_text())
q = d[d.striker_name == "Heinrich Klaasen"]; h = q[q.hp]
def bat(g): 
    b = g.faced.sum(); return {"pb": int(b), "sr": round(g.bat_runs.sum() / max(b, 1) * 100, 1), "outs": int(g.striker_out.sum()), "v": round(g.bat_val.sum() / max(b, 1) * 100, 1)}
k = {"seasons": [dict(y=int(y), **bat(g)) for y, g in h.groupby("year")], "phases": {p: bat(g) for p, g in h.groupby("phase")},
     "spin": bat(h[h.is_spin == 1]), "pace": bat(h[h.is_spin == 0]), "usual": bat(q[~q.hp]), "pressure": bat(h),
     "matches": int(q.match_id.nunique()), "ipl_share": round(float(h.kind_ipl.mean() * 100)),
     "chase": bat(h[h.innings == 2]), "setting": bat(h[h.innings == 1])}
# RR middle-overs batting under pressure vs spin (IPL 2025-26)
y = d[(d.kind_ipl == 1) & (d.year >= 2025) & d.hp & (d.phase == "MID")]
rr = y[y.batting_team_id == 3]; lg = y
k["rr_mid"] = {"rr_spin": bat(rr[rr.is_spin == 1]), "lg_spin": bat(lg[lg.is_spin == 1]), "rr_all": bat(rr), "lg_all": bat(lg)}
J["pick_bat"] = k
(HERE / "build/data.json").write_text(json.dumps(J, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print(json.dumps(k, indent=0))
