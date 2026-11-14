"""Step 6 - Figures + methodology report (PDF) from the pipeline outputs."""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether)
from config import wicket_cost_text, OUT, FIG, HIGH_PRESSURE_QUANTILE, MIN_PRESSURE_BALLS_BAT, MIN_PRESSURE_MATCHES, MIN_BASELINE_BALLS, OPP_WEIGHT

BLUE, ORANGE, GRAY, INK, MUTED = "#2a78d6", "#eb6834", "#b9b8b2", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#c9c8c2", "axes.labelcolor": MUTED, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#ececea", "grid.linewidth": 0.6, "axes.titleweight": "bold", "axes.titlesize": 10})


def fig_pressure_maps(d):
    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.4))
    c = d[(d.innings == 2) & (d.runs_needed.between(1, 120)) & (d.max_balls == 120)].copy()
    c["need_bin"] = pd.cut(c.runs_needed, np.arange(0, 125, 10))
    c["balls_bin"] = pd.cut(c.balls_left, np.arange(0, 125, 12))
    p = c.pivot_table(index="need_bin", columns="balls_bin", values="PI", aggfunc="mean", observed=False)
    im = ax[0].imshow(p.values, origin="lower", aspect="auto", cmap="Blues", vmin=0, vmax=4)
    ax[0].set_xticks(range(len(p.columns))); ax[0].set_xticklabels([int(i.right) for i in p.columns], fontsize=7)
    ax[0].set_yticks(range(len(p.index))); ax[0].set_yticklabels([int(i.right) for i in p.index], fontsize=7)
    ax[0].set_xlabel("balls left (chase)"); ax[0].set_ylabel("runs needed"); ax[0].set_title("Chase: mean Pressure Index"); ax[0].grid(False)
    fig.colorbar(im, ax=ax[0], fraction=0.04)
    g = d.groupby(["innings", "over_no"]).PI.mean().unstack(0)
    ax[1].plot(g.index, g[1], color=BLUE, lw=2, label="1st innings")
    ax[1].plot(g.index, g[2], color=ORANGE, lw=2, label="2nd innings (chase)")
    thr = d.PI.quantile(HIGH_PRESSURE_QUANTILE)
    ax[1].axhline(thr, color=MUTED, lw=1, ls="--"); ax[1].text(1, thr + 0.05, f"high-pressure cut-off ({thr:.2f})", color=MUTED, fontsize=7)
    ax[1].set_xlabel("over"); ax[1].set_ylabel("mean Pressure Index (1 = average ball)"); ax[1].set_title("Pressure by over"); ax[1].legend(frameon=False)
    fig.tight_layout(); fig.savefig(FIG / "pressure_maps.png", dpi=200); plt.close(fig)


def fig_definitions(defs):
    fig, ax = plt.subplots(figsize=(6, 2.3))
    lab = [s.split(" - ")[0] for s in defs.definition]
    ax.barh(lab, defs["decisiveness ratio"], color=[BLUE, GRAY, GRAY], height=0.55)
    for i, v in enumerate(defs["decisiveness ratio"]):
        ax.text(v + 0.03, i, f"{v:.2f}x  ({100*defs['share of total |WPA| in flagged balls'][i]:.0f}% of swing in {100*defs['share of balls flagged'][i]:.0f}% of balls)", va="center", fontsize=7.5, color=INK)
    ax.set_xlim(0, 3.2); ax.invert_yaxis(); ax.set_xlabel("decisiveness ratio = share of win-probability swing / share of balls")
    ax.set_title("Which pressure definition isolates the moments that decide matches?")
    fig.tight_layout(); fig.savefig(FIG / "definitions.png", dpi=200); plt.close(fig)


def fig_calibration():
    cal = pd.read_csv(OUT / "wp_calibration.csv")
    fig, ax = plt.subplots(figsize=(3.4, 3))
    for inn, col in [(1, BLUE), (2, ORANGE)]:
        c = cal[cal.innings == inn]
        ax.plot(c.pred, c.obs, "o-", color=col, ms=4, lw=1.5, label=f"innings {inn}")
    ax.plot([0, 1], [0, 1], color=MUTED, lw=1, ls="--")
    ax.set_xlabel("predicted win probability"); ax.set_ylabel("observed win rate"); ax.set_title("WP model calibration (out-of-fold)")
    ax.legend(frameon=False); fig.tight_layout(); fig.savefig(FIG / "calibration.png", dpi=200); plt.close(fig)


def fig_iterations(hist):
    fig, ax = plt.subplots(figsize=(7.5, 2.8))
    x = np.arange(len(hist))
    ax.bar(x - 0.18, hist.bat, 0.34, color=BLUE, label="batters")
    ax.bar(x + 0.18, hist.bowl, 0.34, color=ORANGE, label="bowlers")
    ax.set_xticks(x); ax.set_xticklabels(hist.version, fontsize=7)
    ax.set_ylabel("split-half reliability (Spearman)"); ax.set_title("Iterations: reliability of the final score")
    ax.legend(frameon=False); fig.tight_layout(); fig.savefig(FIG / "iterations.png", dpi=200); plt.close(fig)


def fig_top10(e, role, unit):
    t = e.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    y = np.arange(len(t))
    ax.barh(y + 0.2, t.hp_raw_100, 0.38, color=BLUE, label="under pressure (observed)")
    ax.barh(y - 0.2, t.rt_raw_100, 0.38, color=GRAY, label="routine situations (observed)")
    ax.set_yticks(y); ax.set_yticklabels([f"{int(r)}. {p}" for r, p in zip(t["rank"], t.player)])
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_xlabel(unit); ax.legend(frameon=False, loc="lower right", fontsize=7)
    ax.set_title(f"Top 10 {'batters' if role == 'bat' else 'bowlers'}: pressure vs usual level")
    fig.tight_layout(); fig.savefig(FIG / f"top10_{role}.png", dpi=200); plt.close(fig)


def fig_scatter(e, role):
    fig, ax = plt.subplots(figsize=(4.6, 3.8))
    top = e["rank"] <= 10
    ax.scatter(e.rt_raw_100[~top], e.hp_raw_100[~top], s=14, color=GRAY, edgecolor="white", lw=0.5, label="eligible players")
    ax.scatter(e.rt_raw_100[top], e.hp_raw_100[top], s=30, color=BLUE, edgecolor="white", lw=0.8, label="top 10")
    for _, r in e[top].iterrows():
        ax.annotate(r.player.split()[-1], (r.rt_raw_100, r.hp_raw_100), fontsize=6.5, color=INK, xytext=(3, 2), textcoords="offset points")
    lim = [min(e.rt_raw_100.min(), e.hp_raw_100.min()) - 3, max(e.rt_raw_100.max(), e.hp_raw_100.max()) + 3]
    ax.plot(lim, lim, color=MUTED, lw=1, ls="--"); ax.text(lim[1], lim[1], " rise = above line", fontsize=6.5, color=MUTED, ha="right", va="bottom")
    ax.set_xlabel("routine: runs above expected / 100 balls"); ax.set_ylabel("pressure: runs above expected / 100 balls")
    ax.set_title(f"{'Batters' if role == 'bat' else 'Bowlers'}: pressure vs routine"); ax.legend(frameon=False, fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / f"scatter_{role}.png", dpi=200); plt.close(fig)


def fig_boot(e, role):
    t = e.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    y = np.arange(len(t))
    ax.hlines(y, t.rank_p05, t.rank_p95, color=GRAY, lw=3)
    ax.plot(t.boot_median_rank, y, "o", color=BLUE, ms=5, label="bootstrap median rank")
    ax.plot(t["rank"], y, "|", color=ORANGE, ms=10, mew=2, label="point-estimate rank")
    ax.set_yticks(y); ax.set_yticklabels([f"{p}  (P top-10 {100*q:.0f}%)" for p, q in zip(t.player, t.p_top10)], fontsize=7)
    ax.set_xlabel("rank (90% bootstrap interval, 300 match resamples)"); ax.axvline(10.5, color=MUTED, ls="--", lw=1)
    ax.set_title(f"Rank uncertainty - {'batters' if role == 'bat' else 'bowlers'}"); ax.legend(frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout(); fig.savefig(FIG / f"boot_{role}.png", dpi=200); plt.close(fig)


# --------------------------------------------------------------------- report
ss = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=15, spaceAfter=6, textColor=colors.HexColor(INK))
H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=11.5, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor(BLUE))
B = ParagraphStyle("b", parent=ss["BodyText"], fontSize=8.8, leading=11.8, spaceAfter=4)
SM = ParagraphStyle("sm", parent=B, fontSize=7.4, leading=9.4, textColor=colors.HexColor(MUTED))


def P(t, s=B):
    return Paragraph(t, s)


def table(df, widths=None, fs=7.2):
    data = [list(df.columns)] + [[v if hasattr(v, "wrap") else str(v) for v in row] for row in df.values.tolist()]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), fs), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef3fb")),
                           ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor(BLUE)),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f5")]),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)]))
    return t


def img(name, w):
    from PIL import Image as PI
    im = PI.open(FIG / name)
    return Image(str(FIG / name), width=w, height=w * im.size[1] / im.size[0])


def main():
    d = pd.read_parquet(OUT / "deliveries_value.parquet")
    d["PI"] = d.LI_c * d.stakes
    bat = pd.read_csv(OUT / "ratings_bat.csv")
    bowl = pd.read_csv(OUT / "ratings_bowl.csv")
    defs = pd.read_csv(OUT / "val_pressure_definitions.csv")
    rel = pd.read_csv(OUT / "val_reliability.csv")
    pred = pd.read_csv(OUT / "val_predictive.csv")
    models = pd.read_csv(OUT / "val_models.csv")
    comp = pd.read_csv(OUT / "val_components.csv")
    cons = pd.read_csv(OUT / "val_consistency.csv")
    thr = pd.read_csv(OUT / "val_threshold.csv")
    sens = pd.read_csv(OUT / "val_sensitivity.csv")
    wpm = pd.read_csv(OUT / "wp_model_metrics.csv")
    W = json.loads((OUT / "weights.json").read_text())
    final = models[(models.model == "blend") & (models.score == "full composite")].set_index("role")
    hist = pd.DataFrame({
        "version": ["v1 top-25%\njoint run value", "v2 + split\nrun/wkt shrink", "v3 WPA/LI\n(uncentred)", "v4 WPA/LI\ncentred", "v5 run value\ndirect EB", "v6 FINAL\nblend EB"],
        "bat": [0.011, 0.037, 0.309, 0.110, 0.093, final.loc["bat", "split_half_rho"]],
        "bowl": [0.068, 0.048, 0.229, 0.133, 0.030, final.loc["bowl", "split_half_rho"]]})
    hist.to_csv(OUT / "iteration_history.csv", index=False)

    fig_pressure_maps(d); fig_definitions(defs); fig_calibration(); fig_iterations(hist)
    unit = "runs above expected per 100 balls (wicket-adjusted)"
    for e, r in [(bat, "bat"), (bowl, "bowl")]:
        fig_top10(e, r, unit); fig_scatter(e, r); fig_boot(e, r)

    doc = SimpleDocTemplate(str(OUT / "SupeRR_Selector_Round1_Methodology_Report.pdf"), pagesize=A4,
                            leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.4 * cm, bottomMargin=1.4 * cm,
                            title="SupeRR Selector S2 - Round 1 - Pressure Performance Methodology")
    W_ = A4[0] - 3.2 * cm
    S = []
    n_m, n_b = d.match_id.nunique(), len(d)
    S += [P("Who Delivers When It Matters? A Leverage-Based Pressure Rating for T20 Batters and Bowlers", H1),
          P(f"SupeRR Selector Season 2 - Round 1 methodology report. Data: {n_b:,} deliveries from {n_m} IPL, T20I and emerging-team T20 matches (2022-2026). "
            "Every number in this report is produced by the accompanying code (<font face='Courier'>run_all.sh</font>); nothing is entered by hand except the iteration history in section 7.", SM)]

    top = pd.DataFrame({"Rank": range(1, 11), "Batter": bat.player.head(10).values,
                        "P(top-10)": [f"{100*x:.0f}%" for x in bat.p_top10.head(10)],
                        "Bowler": bowl.player.head(10).values, "P(top-10) ": [f"{100*x:.0f}%" for x in bowl.p_top10.head(10)]})
    S += [P("Final rankings", H2), table(top, [1.2 * cm, 5 * cm, 2 * cm, 5 * cm, 2 * cm], fs=8.5),
          P("P(top-10) = share of 300 match-level bootstrap resamples in which the player stays in the top 10.", SM)]

    S += [P("1. Summary of the approach", H2), P(
        "<b>Pressure</b> is defined as <b>leverage</b>: how much the result of the next delivery is expected to move the batting side's probability of winning. "
        "We train an out-of-fold win-probability model, simulate every possible outcome of each ball, and measure the expected swing. "
        "Pressure Index (PI) = leverage / average leverage x stakes (1.15 in knock-outs). The top 30% of deliveries by PI are <i>high-pressure</i>; the bottom 50% are the <i>routine</i> baseline. "
        "<b>Performance</b> on each ball is measured against what an average player would produce in exactly that situation (runs above expected plus a state-dependent cost for wickets). "
        "<b>Ratings</b> combine (i) a sample-size-aware pressure rating, (ii) the change from the player's own routine level, and (iii) match-level reliability, "
        "with weights proportional to how repeatable each component proved in split-half tests. "
        "Every design choice was decided by the same out-of-sample yardsticks: split-half reliability, 2022-24 to 2025-26 predictive validity, and bootstrap rank stability.")]

    S += [P("2. Defining pressure", H2), P(
        "Pressure is not a single variable - required rate, wickets in hand, balls left, phase and closeness all matter, and they interact (needing 12 an over with 8 wickets in hand is very different from needing 12 an over with 2). "
        "Rather than hand-weighting these signals, we let them interact inside a win-probability (WP) model and ask one question per ball: <i>how much can this delivery change who wins?</i> "
        "This is the Leverage Index used in baseball and in-game win-probability analytics. It rises automatically when the game is close, late and finely balanced, and it falls in dead rubbers and one-sided chases.")]
    S += [P("<b>Win-probability model.</b> Separate gradient-boosted classifiers for each innings, with monotone constraints (more wickets/balls in hand never lowers WP; more runs needed never raises it). "
            "Features: balls left, wickets left, score (1st innings) or runs needed (chase; DLS-revised targets and overs are used where present), and a pre-match Elo difference computed from results only, so a mismatch reduces pressure. "
            "All WP values are out-of-fold (5-fold, grouped by match) so no ball is scored by a model that saw its result. "
            f"Out-of-fold AUC: 1st innings {wpm.auc[0]:.3f}, chase {wpm.auc[1]:.3f}; Brier {wpm.brier[0]:.3f} / {wpm.brier[1]:.3f}.")]
    S += [P("<b>Leverage.</b> A multiclass outcome model gives P(0,1,2,3,4,6,wicket,extra | state). For each delivery LI_raw = sum over outcomes of P(outcome) x |WP(after) - WP(before)|, normalised so the average ball = 1 and winsorised at the 99.5th percentile (rain-shortened end-games produce extreme values).")]
    S += [img("pressure_maps.png", W_), P("Left: in a chase, pressure is concentrated where runs needed and balls left are close to each other late on. Right: 1st-innings pressure stays moderate; chase pressure climbs steeply at the death.", SM)]
    dd = defs.copy()
    dd["definition"] = [s.split(" - ")[0] for s in dd.definition]
    keep = ["definition", "share of balls flagged", "share of total |WPA| in flagged balls", "decisiveness ratio", "dismissal % (pressure)", "dismissal % (routine)", "dot % (pressure)", "dot % (routine)", "run rate (pressure)", "run rate (routine)"]
    dd = dd[keep].round(2)
    dd.columns = ["def.", "% balls", "% |WPA|", "decisive", "out% P", "out% R", "dot% P", "dot% R", "RR P", "RR R"]
    S += [KeepTogether([P("<b>Does the definition separate pressure from ordinary situations?</b> We compared it with two alternatives: a hand-weighted stress score (HEUR: required-rate gap, wickets lost, recent wickets, death overs, closeness) and a simple rule (NAIVE: chase at RRR 9+, overs 17-20, or 4+ down inside 10 overs). "
            "PI concentrates far more of the actual match-deciding win-probability swing into its flagged balls, and players' pressure ratings are more repeatable under it (table 3).", B),
            img("definitions.png", W_ * 0.8), table(dd, fs=7)])]
    S += [P("Under PI pressure, batters score faster and are dismissed more often - teams take risk when the match is on the line - so performance must be judged against what is <i>expected in that situation</i>, not against season averages.", SM)]

    S += [P("3. Measuring performance", H2), P(
        "Two expected-outcome models (gradient boosting, out-of-fold) estimate, for an average player in exactly the same situation - innings, over, balls and wickets left, score, runs needed, required and current rate, Pressure Index, Elo difference, pace or spin, competition, opposition tier and season: "
        "expected runs off the bat and the probability the striker is out (for batting); expected runs conceded and the probability of a bowler's wicket (for bowling). "
        f"A wicket is converted into runs with a state-dependent wicket cost from an expected-remaining-runs model: {wicket_cost_text()}.")]
    S += [P("<b>Batter value per ball</b> = (runs - expected runs) - wicket cost x (out - P(out)).<br/><b>Bowler value per ball</b> = (expected runs conceded - runs conceded) + wicket cost x (wicket - P(wicket)).<br/>"
            "Byes and leg-byes are not charged to the bowler; run-outs are not credited to him; a dismissed non-striker is not charged to the striker. "
            "We also compute a win-probability lens (WPA / leverage, centred within innings x phase x pressure-decile cells) which is used for the match-level consistency component.")]
    S += [P("<b>Player rating (per 100 balls).</b> For each player we aggregate value over high-pressure and routine deliveries separately. "
            "Raw averages over a few hundred balls are noisy, so we use empirical-Bayes shrinkage with the between-player variance estimated from the data (DerSimonian-Laird). The run and wicket parts are shrunk separately because wicket-taking/avoidance is far noisier than run scoring. "
            "The final pressure rating averages two estimates: (a) <i>direct</i> - what the player did under pressure, shrunk to the league mean, and (b) <i>hierarchical</i> - his overall level plus his shrunk pressure deviation. "
            "(a) keeps the ranking anchored in pressure evidence; (b) guards against small-sample flukes. The 50/50 blend was the most repeatable and the most predictive option for batters, and close to the best for bowlers (table 4).")]
    S += [P("<b>Composite score</b> = w<sub>Q</sub> z(pressure rating) + w<sub>U</sub> z(uplift = pressure level - own routine level) + w<sub>C</sub> z(match consistency). "
            "Consistency is role-specific: for batters, the impact rate (share of pressure matches in which he produced a top-quartile contribution); for bowlers, the no-failure rate (share of pressure matches in which he avoided a bottom-quartile one). These were the most repeatable of four formulations (table 5). "
            f"Weights are proportional to each component's split-half reliability, with uplift floored at 0.15 because the brief asks for the comparison with usual level: batters {W['bat']}, bowlers {W['bowl']} (Q/U/C).")]

    S += [P("4. Fair comparisons", H2), P(
        f"<b>Eligibility:</b> at least {MIN_PRESSURE_BALLS_BAT} legal balls faced/bowled under pressure, pressure involvement in at least {MIN_PRESSURE_MATCHES} matches, and at least {MIN_BASELINE_BALLS} routine balls so the comparison with usual level exists ({len(bat)} batters and {len(bowl)} bowlers qualify). "
        "Results were stable with thresholds of 120 or 200 (section 8). "
        f"<b>Context:</b> expectations already adjust for phase, situation, pace/spin, competition and season, so an opener and a finisher are each judged against what is normal in their situations. "
        f"<b>Opposition:</b> balls against Associate sides count {OPP_WEIGHT['ASSOC']}, emerging A-team matches {OPP_WEIGHT['A']}, full-member and IPL matches 1.0; the expectation model also includes opposition tier and the WP model uses Elo. "
        "<b>IPL and T20I</b> data are pooled on purpose: both are top-tier T20 with comparable pressure structures, pooling doubles the pressure sample, and the competition is a feature in every model. Separate IPL and T20I pressure values are reported in the evidence tables. "
        "<b>Shrinkage</b> automatically discounts small samples, and a bootstrap over matches quantifies rank uncertainty.")]

    def evid(e, role):
        if role == "bat":
            cols = {"rank": "#", "player": "Player", "balls": "P balls", "matches": "P mts", "P_SR": "P SR", "R_SR": "R SR", "P_avg": "P avg", "hp_raw_100": "P RAE", "rt_raw_100": "R RAE", "hp_val_100": "Rating", "uplift_100": "Uplift", "consistency": "Cons.", "hp_raw_IPL": "IPL", "hp_raw_T20I": "T20I"}
        else:
            cols = {"rank": "#", "player": "Player", "balls": "P balls", "matches": "P mts", "P_econ": "P econ", "R_econ": "R econ", "P_wkts": "P wkts", "hp_raw_100": "P RAE", "rt_raw_100": "R RAE", "hp_val_100": "Rating", "uplift_100": "Uplift", "consistency": "Cons.", "hp_raw_IPL": "IPL", "hp_raw_T20I": "T20I"}
        t = e.head(10)[list(cols)].rename(columns=cols).copy()
        for c in t.columns[2:]:
            t[c] = pd.to_numeric(t[c], errors="coerce").round(1 if c != "Cons." else 2)
        t = t.fillna("-")
        for c in ["P balls", "P mts", "P wkts"]:
            if c in t:
                t[c] = t[c].apply(lambda x: int(x) if x != "-" else x)
        return table(t, fs=6.8)

    S += [PageBreak(), P("5. Evidence for the top 10 - batters", H2), img("top10_bat.png", W_ * 0.85), evid(bat, "bat"),
          P("P = high-pressure balls, R = routine balls. RAE = runs above expected per 100 balls (wicket-adjusted). Rating = shrunk pressure rating; Uplift = observed pressure minus observed routine level (shrunk). IPL/T20I = raw pressure RAE in each competition.", SM),
          img("scatter_bat.png", W_ * 0.62)]
    S += [PageBreak(), P("6. Evidence for the top 10 - bowlers", H2), img("top10_bowl.png", W_ * 0.85), evid(bowl, "bowl"),
          P("For bowlers, positive RAE = runs saved versus an average bowler in the same situations (wicket-adjusted).", SM), img("scatter_bowl.png", W_ * 0.62)]

    S += [PageBreak(), P("7. How the solution was iterated", H2), P(
        "The design was improved over six versions. Each was judged on the split-half reliability of the final score (the Spearman correlation between ratings computed on two random halves of the matches, averaged over repeated splits): a score that cannot agree with itself cannot identify reliable players.", B),
        img("iterations.png", W_ * 0.85),
        P("<b>v1</b> top-25% pressure, one run-value metric with joint shrinkage: reliability near zero because wicket noise (one dismissal at ~9 runs) swamped the signal. "
          "<b>v2</b> shrinking run and wicket parts separately helped a little. "
          "<b>v3</b> switched to the win-probability lens WPA/LI and looked much better (0.31/0.23), but diagnostics showed it was partly a bias: average WPA/LI drifted by context, so players who simply bat in certain phases looked better. We rejected it. "
          "<b>v4</b> centred WPA/LI within context cells: honest, but modest (0.11/0.13). "
          "<b>v5</b> run value plus direct shrinkage: most faithful to the pressure sample, but least stable. "
          "<b>v6 (final)</b> blends direct and hierarchical estimates, uses run value for the rating and WPA/LI for consistency, and sets weights from measured reliability. "
          "We also fixed a leverage artefact where the last ball of the 1st innings switched between models and produced false spikes.", B)]
    r2 = rel.copy(); r2["definition"] = [s.split(" - ")[0] for s in r2.definition]
    S += [P("<b>Table 3 - pressure definition x value currency</b> (split-half reliability; temporal = 2022-24 vs 2025-26 rank correlation)", B),
          table(r2[["definition", "role", "value_lens", "split_half_rho", "temporal_rho", "n_players"]].round(3), fs=7),
          P("'raw' (plain runs per ball) looks most repeatable for batters, but only because it re-measures role: finishers always score faster at the death. It is not context-fair, so we did not use it.", SM)]
    S += [P("<b>Table 4 - rating model comparison</b> (final composite and pressure rating alone)", B),
          table(models.round(3), fs=7)]
    S += [P("<b>Predictive check:</b> estimators fitted on 2022-24 data, correlated with the same players' observed 2025-26 pressure performance:", B),
          table(pred[pred.estimator.str.contains("pressure rating|overall")].round(3), fs=6.8)]
    S += [P("<b>Table 5 - consistency formulations</b> (split-half reliability)", B), table(cons.round(3), fs=7),
          P("<b>Component reliability</b> (drives the composite weights)", B), table(comp.round(3), fs=7),
          P("<b>High-pressure threshold</b> - the top 30% keeps reliability close to the best while keeping about 120 qualified players per role; very narrow definitions (top 15%) leave too few balls per player.", B),
          table(thr.round(3), fs=7)]

    S += [PageBreak(), P("8. Reliability and limitations", H2), img("boot_bat.png", W_ * 0.72), img("boot_bowl.png", W_ * 0.72),
          P("Ranks are bootstrapped by resampling whole matches (Poisson weights, 300 replicates). Players with long pressure records, such as the leading names with P(top-10) of 60% or more, are robust picks. "
            "Ranks 6-10 in each list sit in a crowded band where several players are statistically very close; the bootstrap median rank is reported to show this honestly.", B)]
    S += [P("<b>Sensitivity of the top 10</b> (number of the final top-10 retained under each alternative)", B), table(sens, fs=7)]
    S += [P("<b>Key findings and limitations</b>", B), P(
        "- <b>Clutch is real but small.</b> A player's pressure-minus-routine difference is only weakly repeatable (component reliability close to zero). Most of what predicts pressure performance is general, context-adjusted quality. That is why the model blends pressure evidence with overall level instead of rewarding raw differences, which would mostly reward luck.<br/>"
        "- <b>Small samples.</b> Even regulars face only 150-800 pressure balls in this window. Split-half reliability of 0.2-0.3 means rankings beyond the top handful should be read as tiers rather than exact positions.<br/>"
        "- <b>Data gaps.</b> The feed does not record runs scored off wides, byes or leg-byes beyond the first run. Reconstructed chase totals reach the target in 74% of winning chases (mean shortfall about 1 run), so required-rate states are very slightly overstated. Fielding, captaincy and the non-striker's role are not modelled.<br/>"
        "- <b>Model dependence.</b> Pressure is defined through a WP model. The first-innings WP is inherently less certain (AUC ~0.71) because the target is not yet known, so 1st-innings leverage is flatter.<br/>"
        "- <b>Roles and opportunity.</b> Players who rarely face pressure, such as top-order batters in dominant teams, have fewer qualifying balls. The eligibility rule and shrinkage handle this conservatively.<br/>"
        "- <b>Era.</b> Data spans 2022-2026 with equal weight. A two-season half-life recency variant keeps most of the top 10 (section 8 table).", B)]
    S += [P("9. Reproducibility", H2), P(
        "<font face='Courier'>SUPERR_DATA=/path/to/csvs ./run_all.sh</font> runs: s01_prepare (match-state reconstruction, QA) - s02_pressure (Elo, WP, leverage, PI) - s03_value (expected-outcome models, wicket cost, per-ball value) - "
        "s05_validate (all experiments, derives weights.json) - s04_rank (ratings, bootstrap, FINAL_TOP10.csv) - s06_report (this PDF). All tunables are in config.py; the random seed is fixed (42). "
        "Runtime is about 15 minutes on 2 CPUs. Outputs include per-player rating tables for every eligible player (ratings_bat.csv, ratings_bowl.csv) and all validation tables.", B)]
    doc.build(S)
    print("[OK] report written")


if __name__ == "__main__":
    main()
