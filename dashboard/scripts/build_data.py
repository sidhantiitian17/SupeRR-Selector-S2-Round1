"""Turn the hybrid pipeline outputs into the compact data bundle the website reads.

Single source of truth:  outputs/hyb_ratings_{bat,bowl}.csv  (rank, score, bootstrap, spec support)
Real per-ball facts:      outputs/deliveries_value.parquet     (PI, WP, runs, wickets, values)

Usage:  python3 -I scripts/build_data.py  <hybrid_outputs_dir> <uploads_dir> <site_dir>
Writes: <site_dir>/data/clutch_data.js   (window.CLUTCH_DATA)  +  copies report/figures.
"""
import base64, json, sys, shutil
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path(sys.argv[1]); UP = Path(sys.argv[2]); SITE = Path(sys.argv[3])
TOPN = 120          # ranked list length shipped to the UI
SURR_N = 30         # players per role with ball-level arrays for the live Pressure Model explorer
rng = np.random.default_rng(42)

# ------------------------------------------------------------------ load
d = pd.read_parquet(OUT / "deliveries_value.parquet")
d["pct"] = d.groupby(["match_id", "innings"]).LI.rank(pct=True) * 100      # within-innings leverage percentile
d["date"] = pd.to_datetime(d.match_date)
# official pressure flag of the hybrid model (ratings.flag_pressure): top 30% of Pressure Index, all balls pooled.
# Every runs-above-expected number (RAE, seasons, trend, per-match value) uses it, exactly as the methodology report does.
d["hpA"] = d.PI >= d.PI.quantile(0.70)
def raw(name):  # accepts teams.csv or an uploader-prefixed copy like 9e2fca45-teams.csv
    p = UP / name
    return p if p.exists() else sorted(UP.glob(f"*-{name}"))[0]
teams = pd.read_csv(raw("teams.csv"))
matches = pd.read_csv(raw("matches.csv"))
tname = {(r.comp_id, r.team_id): r.team_name for r in teams.itertuples()}
d["bat_team"] = [tname.get((c, t), "") for c, t in zip(d.comp_id, d.batting_team_id)]
d["bowl_team"] = [tname.get((c, t), "") for c, t in zip(d.comp_id, d.bowling_team_id)]
CODES = {"Chennai Super Kings": "CSK", "Mumbai Indians": "MI", "Rajasthan Royals": "RR", "Punjab Kings": "PBKS",
         "Royal Challengers Bengaluru": "RCB", "Delhi Capitals": "DC", "Kolkata Knight Riders": "KKR",
         "Sunrisers Hyderabad": "SRH", "Gujarat Titans": "GT", "Lucknow Super Giants": "LSG"}
def code(n):
    if n in CODES: return CODES[n]
    return "".join(w[0] for w in n.split()).upper() if len(n.split()) > 1 and len(n) > 12 else n[:3].upper()
SHORT = {"United Arab Emirates": "UAE", "West Indies": "WI", "South Africa": "SA", "New Zealand": "NZ", "Sri Lanka": "SL",
         "Afghanistan": "AFG", "Bangladesh": "BAN", "Pakistan": "PAK", "England": "ENG", "Australia": "AUS", "India": "IND",
         "Zimbabwe": "ZIM", "Ireland": "IRE", "Netherlands": "NED", "Scotland": "SCO", "Nepal": "NEP", "Namibia": "NAM",
         "United States of America": "USA", "Oman": "OMA"}
def tcode(n): return CODES.get(n) or SHORT.get(n) or code(n)

# ------------------------------------------------------------------ pressure definition used for the evidence cards
# (identical to the methodology report's evidence tables: within-innings leverage percentile)
CUT = {"bat": 75, "bowl": 70}
PID = {"bat": "striker_id", "bowl": "bowler_id"}
NAME = {"bat": "striker_name", "bowl": "bowler_name"}
VAL = {"bat": "bat_val", "bowl": "bowl_val"}

PHASE_LABEL = {"PP": "Powerplay", "MID": "Middle overs", "DEATH": "Death overs"}
print("phases:", d.phase.unique())


def stats_for(g, role):
    """Pressure-vs-usual summary for one player's balls (already filtered to a competition)."""
    if role == "bat":
        g = g[g.faced]
        p, u = g[g.pct >= CUT[role]], g[g.pct < CUT[role]]
        if len(p) == 0: return None
        return dict(pb=int(len(p)), pruns=int(p.bat_runs.sum()), pouts=int(p.striker_out.sum()),
                    pm=round(100 * p.bat_runs.mean(), 1), um=round(100 * u.bat_runs.mean(), 1) if len(u) else None,
                    pdot=round(100 * (p.bat_runs == 0).mean(), 1), pbnd=round(100 * (p.is_four | p.is_six).mean(), 1),
                    ubnd=round(100 * (u.is_four | u.is_six).mean(), 1) if len(u) else None,
                    udot=round(100 * (u.bat_runs == 0).mean(), 1) if len(u) else None,
                    prate=round(100 * p.striker_out.mean(), 2), urate=round(100 * u.striker_out.mean(), 2) if len(u) else None,
                    ub=int(len(u)), rae=round(100 * g[g.hpA].bat_val.mean(), 1) if g.hpA.any() else None,
                    urae=round(100 * g[~g.hpA].bat_val.mean(), 1) if (~g.hpA).any() else None, na=int(g.hpA.sum()))
    p, u = g[g.pct >= CUT[role]], g[g.pct < CUT[role]]
    if len(p) == 0: return None
    pl, ul = p[p.is_legal], u[u.is_legal]
    if len(pl) == 0: return None
    return dict(pb=int(len(pl)), pruns=int(p.bowl_runs.sum()), pouts=int(p.bowler_wkt.sum()),
                pm=round(6 * p.bowl_runs.sum() / len(pl), 2), um=round(6 * u.bowl_runs.sum() / len(ul), 2) if len(ul) else None,
                pdot=round(100 * (p.bowl_runs == 0).mean(), 1), pbnd=round(100 * (p.bowl_runs >= 4).mean(), 1),
                ubnd=round(100 * (u.bowl_runs >= 4).mean(), 1) if len(u) else None,
                udot=round(100 * (u.bowl_runs == 0).mean(), 1) if len(u) else None,
                prate=round(100 * p.bowler_wkt.sum() / len(pl), 2), urate=round(100 * u.bowler_wkt.sum() / max(len(ul), 1), 2) if len(u) else None,
                ub=int(len(ul)), rae=round(100 * g[g.hpA].bowl_val.mean(), 1) if g.hpA.any() else None,
                urae=round(100 * g[~g.hpA].bowl_val.mean(), 1) if (~g.hpA).any() else None, na=int(g.hpA.sum()))


# ------------------------------------------------------------------ players
def build_role(role):
    r = pd.read_csv(OUT / f"hyb_ratings_{role}.csv").head(TOPN).copy()
    adj = r.score - 100 * (r.score > 50)               # remove the 'delivered' gate offset for display scaling
    lo, hi = adj.min(), adj.max()
    clutch = 100 * (adj - lo) / (hi - lo)
    clutch = clutch.cummin()                            # rank order is the source of truth; rating never rises down the list
    r["clutch"] = (clutch * 0.95 + 5).round(1)
    r["gated"] = r.score > 50 if role == "bowl" else True
    comp_stats, players = {}, []
    for row in r.itertuples():
        pid = row.pid
        x = d[d[PID[role]] == pid]
        last = x.sort_values("date").iloc[-1]
        ipl_x = x[x.comp_kind == "IPL"]
        # team: current franchise if the player featured in the latest IPL season, else national side
        if len(ipl_x) and ipl_x.year.max() >= 2025:
            lx = ipl_x.sort_values("date").iloc[-1]
            team = tcode(lx.bat_team if role == "bat" else lx.bowl_team)
        else:
            lx = x[x.comp_kind == "T20I"].sort_values("date").iloc[-1] if (x.comp_kind == "T20I").any() else last
            team = tcode(lx.bat_team if role == "bat" else lx.bowl_team)
        s_all = {c: stats_for(x if c == "combined" else x[x.comp_kind == c.upper()], role) for c in ("combined", "ipl", "t20i")}
        # per-season consistency: pressure value per 100 pressure balls, by calendar year
        seasons = []
        for yr, g in x.groupby("year"):
            gg = g[g.faced] if role == "bat" else g
            pp = gg[gg.hpA]
            if len(pp) >= 12:
                seasons.append(dict(y=int(yr), n=int(len(pp)), v=round(100 * float(pp[VAL[role]].mean()), 1)))
        # cumulative pressure value per 100 balls at the end of each half-year (trend)
        gg = x[x.faced] if role == "bat" else x
        pp = gg[gg.hpA].copy()
        pp["per"] = pp.date.dt.year.astype(str) + np.where(pp.date.dt.month <= 6, "H1", "H2")
        trend = []
        cum_v = cum_n = 0
        for per, g in pp.sort_values("date").groupby("per", sort=True):
            cum_v += g[VAL[role]].sum(); cum_n += len(g)
            if cum_n >= 20:
                trend.append(dict(p=per, v=round(100 * cum_v / cum_n, 1), n=int(cum_n)))
        # last 12 matches with >= 6 pressure balls
        ms = []
        for mid, g in pp.groupby("match_id"):
            if len(g) < 6: continue
            g0 = g.iloc[0]
            opp = g0.bowl_team if role == "bat" else g0.bat_team
            ms.append(dict(m=int(mid), dt=str(g0.date.date()), opp=tcode(opp), n=int(len(g)),
                           v=round(float(g[VAL[role]].sum()), 2),
                           r=int(g.bat_runs.sum() if role == "bat" else g.bowl_runs.sum()),
                           o=int(g.striker_out.sum() if role == "bat" else g.bowler_wkt.sum()),
                           comp=g0.comp_kind, st=g0.stage))
        ms.sort(key=lambda z: z["dt"])
        players.append(dict(
            id=int(pid), name=row.player, role=role, team=team, rank=int(row.rank), clutch=float(row.clutch),
            score=round(float(row.score - 100 * (row.score > 50)), 4),
            ptop10=round(float(row.p_top10), 3), rlo=round(float(row.rank_p05), 1), rhi=round(float(row.rank_p95), 1),
            rmed=round(float(row.boot_median_rank), 1), specs=int(row.specs_in_top10), nspecs=int(row.n_specs),
            cons=round(float(row.consistency), 3), uplift=round(float(row.uplift), 3), hpval=round(float(row.hp_val), 3),
            balls=int(row.balls), nmatches=int(row.matches), gated=bool(row.gated),
            s=s_all, seasons=seasons, trend=trend, ms=ms[-12:], best=sorted(ms, key=lambda z: -z["v"])[:3]))
    return players


bat = build_role("bat"); bowl = build_role("bowl")
print("players", len(bat), len(bowl), bat[0]["name"], bowl[0]["name"])

# photos: player_image_mapping.csv only lists names; pick up whatever webp already exists in assets/players
photos = {}
for f in (SITE / "assets" / "players").glob("*.webp"):
    pid = int(f.name.split("_")[0]); photos[pid] = f"assets/players/{f.name}"
for p in bat + bowl:
    p["photo"] = photos.get(p["id"])

# ------------------------------------------------------------------ phase shares of high-pressure deliveries
hp_thr = float(d.PI.quantile(0.70))
d["hp"] = d.PI >= hp_thr
d["seg"] = np.where((d.innings == 2) & (d.phase == "DEATH"), "Chase finish", d.phase.map(PHASE_LABEL))
phases = {}
for c in ("combined", "IPL", "T20I"):
    x = d[d.hp] if c == "combined" else d[d.hp & (d.comp_kind == c)]
    sh = x.seg.value_counts(normalize=True)
    phases[c.lower()] = [dict(label=k, value=round(100 * float(sh.get(k, 0)), 1)) for k in ["Powerplay", "Middle overs", "Death overs", "Chase finish"]]

# ------------------------------------------------------------------ league validation (pressure vs routine)
lo_thr = float(d.PI.quantile(0.50))
hp, rt = d[d.hp], d[d.PI <= lo_thr]
def lg(x):
    return dict(rr=round(6 * x.team_runs.sum() / x.is_legal.sum(), 2), dot=round(100 * (x.team_runs == 0).mean(), 1),
                wkt=round(100 * x.team_wkt.mean(), 2), bnd=round(100 * (x.is_four | x.is_six).mean(), 1), n=int(len(x)))
validation = dict(pressure=lg(hp), routine=lg(rt), thr_hp=round(hp_thr, 3), thr_rt=round(lo_thr, 3),
                  share_abs_wpa=round(float(hp.WPA.abs().sum() / d.WPA.abs().sum()), 3))
print("validation", validation)

# threshold explorer (landing slider): real league effect of calling the top (100-p)% of PI "high pressure"
thr = []
for q in range(50, 96, 5):
    t_ = float(d.PI.quantile(q / 100)); hi_ = d[d.PI >= t_]; lo_ = d[d.PI < t_]
    thr.append(dict(p=q, pi=round(t_, 3), rr_hi=lg(hi_)["rr"], rr_lo=lg(lo_)["rr"], wkt_hi=lg(hi_)["wkt"], wkt_lo=lg(lo_)["wkt"],
                    dot_hi=lg(hi_)["dot"], dot_lo=lg(lo_)["dot"], share_wpa=round(float(hi_.WPA.abs().sum() / d.WPA.abs().sum()), 3)))
validation["thr"] = thr

# ------------------------------------------------------------------ heat-map: mean PI by over x wickets lost
hm = d[d.over_no.between(1, 20)].copy()
hm["w"] = hm.wkts_before.clip(0, 9)
piv = hm.groupby(["over_no", "w"]).PI.mean().unstack().reindex(index=range(1, 21), columns=range(10))
heat = [[None if pd.isna(v) else round(float(v), 2) for v in row] for row in piv.values]
heat_n = hm.groupby(["over_no", "w"]).size().unstack().reindex(index=range(1, 21), columns=range(10)).fillna(0).astype(int).values.tolist()

# ------------------------------------------------------------------ transparent surrogate Pressure Index (live explorer)
# five 0-1 factors per delivery, derived only from match state
def factors(x):
    legal = x.legal_before.clip(0, 120).values
    ml = x.max_balls.fillna(120).values
    inn2 = (x.innings == 2).values
    rrr = x.rrr.fillna(0).values; crr = x.crr.fillna(0).values
    chase = 1 - np.clip(np.abs(rrr - crr) / 10.0, 0, 1)       # chase: how tight is required vs current run rate
    par = 8.2 * legal / 6.0                                   # par-score line for the first innings
    defend = 1 - np.clip(np.abs(par - x.score_before.values) / 35.0, 0, 1)   # defence: how close to par
    f1 = np.where(inn2, chase, defend)                        # run-rate / par tightness
    f2 = np.clip(x.wkts_before.values / 9.0, 0, 1)            # wickets lost (resource depletion)
    f3 = np.clip(legal / ml, 0, 1) ** 1.5                     # balls used / phase weight
    f4 = 1 - np.abs(x.WP.values - 0.5) * 2                    # contest closeness (win-probability model)
    f5 = np.where(inn2, 1.0, 0.45) * (1 + 0.25 * x.knock_out.values) / 1.25   # target context + stakes
    return np.vstack([f1, f2, f3, f4, f5]).T.clip(0, 1)

F = factors(d)
# default weights: non-negative least squares to the real model PI -> the surrogate is "the model, simplified"
from scipy.optimize import nnls
samp = rng.choice(len(d), 40000, replace=False)
w0, _ = nnls(np.c_[F[samp], np.ones(len(samp))][:, :5], d.PI.values[samp])
w0 = 0.7 * (w0 / w0.sum()) + 0.3 * 0.2        # shrink toward equal weights so every factor stays live in the explorer
sur0 = F @ w0
corr = float(np.corrcoef(sur0[samp], d.PI.values[samp])[0, 1])
spear = float(pd.Series(sur0[samp]).corr(pd.Series(d.PI.values[samp]), method="spearman"))
print("surrogate default weights", w0.round(3), "pearson", round(corr, 3), "spearman", round(spear, 3))

# global sample for the histogram / threshold (uniform 12k deliveries, factors quantised to bytes)
gs = rng.choice(len(d), 12000, replace=False)
gsamp = (F[gs] * 255).round().astype(np.uint8)

# ball-level arrays for the top-N players of each role (all their balls; quantised factors + outcome byte)
def pack(role):
    out = []
    for p in (bat if role == "bat" else bowl)[:SURR_N]:
        x = d[d[PID[role]] == p["id"]]
        if role == "bat": x = x[x.faced]
        idx = x.index.values
        fx = (F[d.index.get_indexer(idx)] * 255).round().astype(np.uint8)
        if role == "bat":
            runs = x.bat_runs.clip(0, 7).values; out_f = x.striker_out.values.astype(int); legal = np.ones(len(x), int)
        else:
            runs = x.bowl_runs.clip(0, 15).values; out_f = x.bowler_wkt.values.astype(int); legal = x.is_legal.values.astype(int)
        flags = (runs.astype(np.uint8)) | (out_f.astype(np.uint8) << 4) | (legal.astype(np.uint8) << 5)
        out.append(base64.b64encode(np.c_[fx, flags].astype(np.uint8).tobytes()).decode())
    return out

surrogate = dict(weights=[round(float(v), 4) for v in w0], pearson=round(corr, 3), spearman=round(spear, 3),
                 names=["Run-rate / par tightness", "Wickets lost", "Balls used (phase)", "Contest closeness", "Target & stakes"],
                 sample=base64.b64encode(gsamp.tobytes()).decode(), nsample=int(len(gs)),
                 bat=pack("bat"), bowl=pack("bowl"), batIds=[p["id"] for p in bat[:SURR_N]], bowlIds=[p["id"] for p in bowl[:SURR_N]])

# ------------------------------------------------------------------ match timelines (real per-ball PI + WP)
pick = []
ko = d[d.stage.isin(["Final", "Qualifier", "Eliminator"])].groupby("match_id").date.max().sort_values(ascending=False)
pick += list(ko.index[:14])
need = set(p["id"] for p in bat[:10]) | set(p["id"] for p in bowl[:10])
mm = d[(d.striker_id.isin(need) | d.bowler_id.isin(need)) & d.hp]
close = mm.groupby("match_id").size().sort_values(ascending=False)
for m in close.index:
    if m not in pick: pick.append(m)
    if len(pick) >= 36: break
mrow = matches.set_index("match_id")
timelines = []
for mid in pick:
    g = d[d.match_id == mid].sort_values(["innings", "innings_ball_num"])
    mr = mrow.loc[mid]
    comp = g.comp_kind.iloc[0]
    balls = []
    for r_ in g.itertuples():
        code_ = 9 if r_.is_wicket else int(min(r_.team_runs, 8))
        balls.append([int(r_.innings), int(r_.over_no), round(float(r_.PI), 2), round(float(r_.WP), 3), code_, r_.striker_name.split()[-1][:12], r_.bowler_name.split()[-1][:12]])
    timelines.append(dict(id=int(mid), date=str(mr.match_date)[:10], home=tcode(mr.home_team), away=tcode(mr.away_team), stage=str(mr.stage),
                          comp=comp, result=str(mr.result), balls=balls))
print("timelines", len(timelines), sum(len(t["balls"]) for t in timelines))

# ------------------------------------------------------------------ method evidence from the report's CSVs
cal = pd.read_csv(OUT / "wp_calibration.csv")
wpm = pd.read_csv(OUT / "wp_model_metrics.csv")
rel = pd.read_csv(OUT / "val_reliability.csv")
pdef = pd.read_csv(OUT / "val_pressure_definitions.csv")
sel = pd.read_csv(OUT / "hyb_selection.csv", index_col=0)
chosen = json.load(open(OUT / "hyb_chosen.json"))["chosen"]
wts = json.load(open(OUT / "weights.json"))
tour = {}
for role in ("bat", "bowl"):
    s = sel[sel.role == role]
    tour[role] = [dict(name=i, mean=round(float(r.mean_cell), 3), worst=round(float(r.worst_cell), 3), chosen=bool(r.chosen))
                  for i, r in s.sort_values("worst_cell", ascending=False).head(14).iterrows()
                  if "mean_cell" in s.columns]
meth = dict(
    wp=dict(auc1=round(float(wpm.auc[0]), 3), auc2=round(float(wpm.auc[1]), 3), brier1=round(float(wpm.brier[0]), 3), brier2=round(float(wpm.brier[1]), 3)),
    calib=[dict(i=int(r.innings), pred=round(float(r.pred), 3), obs=round(float(r.obs), 3), n=int(r.n)) for r in cal.itertuples()],
    pdef=[dict(name=str(r[1]), share=round(float(r[2]), 3), wpa=round(float(r[3]), 3), ratio=round(float(r[4]), 2)) for r in pdef.itertuples()],
    rel=[dict(role=r.role, lens=r.value_lens, split=round(float(r.split_half_rho), 3), temporal=None if pd.isna(r.temporal_rho) else round(float(r.temporal_rho), 3))
         for r in rel.itertuples() if r.definition.startswith("PI")],
    chosen=chosen, weights=wts, tour=tour)

# ------------------------------------------------------------------ league-wide summary numbers
summary = dict(balls=int(len(d)), matches=int(d.match_id.nunique()), ipl=int((d.comp_kind == "IPL").sum()), t20i=int((d.comp_kind == "T20I").sum()),
               hp_balls=int(d.hp.sum()), years=[int(d.year.min()), int(d.year.max())],
               players_ranked=[len(bat), len(bowl)])

bundle = dict(bat=bat, bowl=bowl, phases=phases, validation=validation, heat=heat, heatN=heat_n, surrogate=surrogate,
              timelines=timelines, method=meth, summary=summary, generated="from hybrid pipeline outputs (seed 42)")
(SITE / "data").mkdir(exist_ok=True)
js = "window.CLUTCH_DATA=" + json.dumps(bundle, separators=(",", ":"), ensure_ascii=False) + ";"
(SITE / "data" / "clutch_data.js").write_text(js)
print("clutch_data.js", round(len(js) / 1e6, 2), "MB")

# assets used by the Methodology page
(SITE / "assets" / "figures").mkdir(parents=True, exist_ok=True)
for f in ["hyb_journey.png", "hyb_iter_A.png", "calibration.png", "pressure_maps.png", "hyb_tournament_bat.png", "hyb_tournament_bowl.png", "hyb_boot_bat.png", "hyb_boot_bowl.png", "definitions.png"]:
    if (OUT / "figures" / f).exists(): shutil.copy(OUT / "figures" / f, SITE / "assets" / "figures" / f)
shutil.copy(OUT / "SupeRR_Selector_Round1_HYBRID_Methodology_Report.pdf", SITE / "assets" / "SupeRR_Selector_Round1_HYBRID_Methodology_Report.pdf")
shutil.copy(OUT / "FINAL_TOP10_HYBRID.csv", SITE / "data" / "FINAL_TOP10_HYBRID.csv")
print("done")
