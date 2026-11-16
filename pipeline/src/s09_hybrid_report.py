"""Methodology report for the final HYBRID solution (PDF)."""
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Spacer, PageBreak, KeepTogether
from config import wicket_cost_text, OUT, FIG, OPP_WEIGHT, MIN_PRESSURE_BALLS_BAT, MIN_PRESSURE_MATCHES, MIN_BASELINE_BALLS
from s06_report import (fig_pressure_maps, fig_definitions, fig_calibration, P, table, img, H1, H2, B, SM,
                        BLUE, ORANGE, GRAY, MUTED, INK)
from hybrid import prep, describe, components


def evidence(d, role, players):
    out = []
    for pid in players:
        if role == "bat":
            x = d[d.faced & (d.striker_id == pid)]
            p, o = x[x.pct >= 75], x[x.pct < 75]
            a = x[x.hpA]
            out.append({"P balls": len(p), "P runs": int(p.bat_runs.sum()), "P outs": int(p.striker_out.sum()),
                        "P SR": 100 * p.bat_runs.mean(), "usual SR": 100 * o.bat_runs.mean(),
                        "P balls/out": len(p) / max(p.striker_out.sum(), 1),
                        "P RAE/100": 100 * a.bat_val.mean(), "usual RAE/100": 100 * x[~x.hpA].bat_val.mean(),
                        "P WPA/ball %": 100 * p.bat_wpa.mean(), "IPL %": 100 * (p.comp_kind == "IPL").mean()})
        else:
            x = d[d.bowler_id == pid]
            p, o = x[x.pct >= 70], x[x.pct < 70]
            a = x[x.hpA]
            out.append({"P balls": int(p.is_legal.sum()), "P runs": int(p.bowl_runs.sum()), "P wkts": int(p.bowler_wkt.sum()),
                        "P econ": 6 * p.bowl_runs.sum() / p.is_legal.sum(), "usual econ": 6 * o.bowl_runs.sum() / o.is_legal.sum(),
                        "P RAE saved/100": 100 * a.bowl_val.mean(), "usual RAE/100": 100 * x[~x.hpA].bowl_val.mean(),
                        "P WPA/ball %": 100 * p.bowl_wpa.mean(), "IPL %": 100 * (p.comp_kind == "IPL").mean()})
    return pd.DataFrame(out, index=players)


def fig_tournament(sel, role, chosen):
    s = sel[sel.role == role]
    keep = ["A: solution A (shipped)", "B: solution B recipe", chosen, "random"]
    t = s.loc[keep]
    lab = ["Solution A", "Solution B", "HYBRID (chosen)", "Random 10"]
    fig, ax = plt.subplots(1, 2, figsize=(8.6, 2.5))
    for i, (c, title) in enumerate([("worst_cell", "Worst of 16 held-out cells"), ("mean_cell", "Mean of 16 held-out cells")]):
        cols = [GRAY, GRAY, BLUE, "#dddcd6"]
        ax[i].barh(lab, t[c], color=cols, height=0.55)
        for j, v in enumerate(t[c]):
            ax[i].text(v + (0.005 if v >= 0 else -0.005), j, f"{v:+.3f}", va="center", ha="left" if v >= 0 else "right", fontsize=7.5, color=INK)
        ax[i].axvline(0, color=MUTED, lw=1); ax[i].invert_yaxis(); ax[i].set_title(title)
        ax[i].set_xlabel("gain of selected 10 on unseen matches (pool SD)")
        lo, hi = min(t[c].min(), 0), max(t[c].max(), 0)
        ax[i].set_xlim(lo - 0.12 * (hi - lo + 0.1), hi + 0.25 * (hi - lo + 0.1))
    fig.suptitle(f"{'Batters' if role == 'bat' else 'Bowlers'}: held-out tournament", fontsize=10, fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG / f"hyb_tournament_{role}.png", dpi=200); plt.close(fig)


JOURNEY = [("random", "Random 10"), ("BASE: volume (most pressure balls)", "Most pressure balls"),
           ("BASE: naive raw pressure SR / economy", "Raw pressure SR / economy"),
           ("A: solution A (shipped)", "Solution A"), ("B: solution B recipe", "Solution B")]


def journey_rows(sel, role, ch, bu):
    s = sel[sel.role == role]
    rows = JOURNEY + ([(bu, "Best hybrid (unconstrained)")] if bu != ch else []) + [(ch, "FINAL hybrid")]
    return [(lab, s.loc[k, "worst_cell"], s.loc[k, "mean_cell"], s.loc[k, "random_mean"], s.loc[k, "future_mean"]) for k, lab in rows]


def fig_journey(sel, ch, bu):
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.2), sharey=False)
    for i, role in enumerate(["bat", "bowl"]):
        r = journey_rows(sel, role, ch[role], bu[role])
        lab = [x[0] for x in r]; mean = [x[2] for x in r]; worst = [x[1] for x in r]
        y = np.arange(len(r))[::-1]
        ax[i].barh(y + 0.18, mean, 0.34, color=[BLUE if l == "FINAL hybrid" else "#8fb4e6" for l in lab], label="mean of 16 cells")
        ax[i].barh(y - 0.18, worst, 0.34, color=[ORANGE if l == "FINAL hybrid" else "#f3b79c" for l in lab], label="worst of 16 cells")
        ax[i].set_yticks(y); ax[i].set_yticklabels(lab, fontsize=7.5); ax[i].axvline(0, color=MUTED, lw=1)
        ax[i].set_title("Batters" if role == "bat" else "Bowlers"); ax[i].set_xlabel("held-out gain of selected 10 (pool SD)")
    h, l = ax[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=7.5, loc="lower center", ncol=2)
    fig.suptitle("The journey on one yardstick: from simple baselines to the final hybrid", fontsize=10, fontweight="bold")
    fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(FIG / "hyb_journey.png", dpi=200); plt.close(fig)


def fig_iterA(hist):
    fig, ax = plt.subplots(figsize=(7.6, 2.6))
    x = np.arange(len(hist))
    ax.bar(x - 0.18, hist.bat, 0.34, color=BLUE, label="batters")
    ax.bar(x + 0.18, hist.bowl, 0.34, color=ORANGE, label="bowlers")
    ax.set_xticks(x); ax.set_xticklabels(hist.version, fontsize=6.8)
    ax.set_ylabel("split-half reliability"); ax.set_title("Phase 2: solution A's six versions (does the score agree with itself?)")
    ax.legend(frameon=False, fontsize=7); fig.tight_layout(); fig.savefig(FIG / "hyb_iter_A.png", dpi=200); plt.close(fig)


def fig_top10(ev, role, names_):
    t = ev.iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    y = np.arange(len(t))
    if role == "bat":
        a, b, xl = t["P SR"], t["usual SR"], "strike rate"
    else:
        a, b, xl = t["P econ"], t["usual econ"], "economy (runs per over, lower is better)"
    ax.barh(y + 0.2, a, 0.38, color=BLUE, label="high-pressure balls")
    ax.barh(y - 0.2, b, 0.38, color=GRAY, label="usual (ordinary) balls")
    ax.set_yticks(y); ax.set_yticklabels([f"{len(t) - i}. {n}" for i, n in enumerate(names_[::-1])])
    ax.set_xlabel(xl); ax.legend(frameon=False, fontsize=7, loc="lower right")
    ax.set_title(f"Top 10 {'batters' if role == 'bat' else 'bowlers'}: under pressure vs usual level")
    fig.tight_layout(); fig.savefig(FIG / f"hyb_top10_{role}.png", dpi=200); plt.close(fig)


def fig_boot(tab, role):
    t = tab.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    y = np.arange(len(t))
    ax.hlines(y, t.rank_p05, t.rank_p95, color=GRAY, lw=3)
    ax.plot(t.boot_median_rank, y, "o", color=BLUE, ms=5, label="bootstrap median rank")
    ax.plot(t["rank"], y, "|", color=ORANGE, ms=10, mew=2, label="final rank")
    ax.set_yticks(y); ax.set_yticklabels([f"{p} ({100*q:.0f}%, {s}/{n})" for p, q, s, n in zip(t.player, t.p_top10, t.specs_in_top10, t.n_specs)], fontsize=6.8)
    ax.axvline(10.5, color=MUTED, ls="--", lw=1); ax.set_xlabel("rank, 90% bootstrap interval")
    ax.set_title(f"Rank uncertainty - {'batters' if role == 'bat' else 'bowlers'}"); ax.legend(frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout(); fig.savefig(FIG / f"hyb_boot_{role}.png", dpi=200); plt.close(fig)


def main():
    d, HP, RT = prep()
    sel = pd.read_csv(OUT / "hyb_selection.csv", index_col=0)
    ch = json.load(open(OUT / "hyb_chosen.json"))["chosen"]
    bu = {r: sel[(sel.role == r) & sel.best_unconstrained].index[0] for r in ["bat", "bowl"]}
    n_cand = int(((sel.role == "bat") & (sel.index != "random")).sum())
    DOCS = OUT.parent / "docs"
    histA = pd.read_csv(DOCS / "iteration_log_solutionA.csv")
    h2h = {r: pd.read_csv(DOCS / f"h2h_A_vs_B_{r}.csv", index_col=0) for r in ["bat", "bowl"]}
    defs = pd.read_csv(OUT / "val_pressure_definitions.csv")
    wpm = pd.read_csv(OUT / "wp_model_metrics.csv")
    Wt = json.load(open(OUT / "weights.json"))
    import re
    m = re.search(r"\+U([0-9.]+)", ch["bowl"]); wu_b = float(m.group(1)) if m else 0.0
    tabs = {r: pd.read_csv(OUT / f"hyb_ratings_{r}.csv", index_col=0) for r in ["bat", "bowl"]}
    fig_pressure_maps(d.assign(PI=d.LI_c * d.stakes)); fig_definitions(defs); fig_calibration()
    fig_journey(sel, ch, bu); fig_iterA(histA)
    ev = {}
    for r in ["bat", "bowl"]:
        fig_tournament(sel, r, ch[r])
        t = tabs[r].head(10)
        ev[r] = evidence(d, r, t.index.tolist())
        fig_top10(ev[r], r, t.player.tolist())
        fig_boot(tabs[r], r)
        out = ev[r].copy(); out.insert(0, "player", t.player.values); out.to_csv(OUT / f"hyb_evidence_{r}.csv")

    doc = SimpleDocTemplate(str(OUT / "SupeRR_Selector_Round1_HYBRID_Methodology_Report.pdf"), pagesize=A4,
                            leftMargin=1.6 * cm, rightMargin=1.6 * cm, topMargin=1.4 * cm, bottomMargin=1.4 * cm,
                            title="SupeRR Selector S2 - Round 1 - Hybrid pressure-performance methodology")
    W_ = A4[0] - 3.2 * cm
    S = [P("Who Delivers When It Matters? A Hybrid, Prediction-Validated Pressure Rating", H1),
         P(f"SupeRR Selector Season 2 - Round 1 methodology report. Scope: IPL and T20I matches 2022-2026 ({d.match_id.nunique()} matches, {len(d):,} deliveries). "
           "Every number is produced by the accompanying code (<font face='Courier'>run_all.sh</font>, seed 42) from the supplied CSV files only.", SM)]
    bt, bw = tabs["bat"].head(10), tabs["bowl"].head(10)
    top = pd.DataFrame({"Rank": range(1, 11), "Batter": bt.player.values, "P(top-10)": [f"{100*x:.0f}%" for x in bt.p_top10],
                        "Specs": [f"{a}/{b}" for a, b in zip(bt.specs_in_top10, bt.n_specs)],
                        "Bowler": bw.player.values, "P(top-10) ": [f"{100*x:.0f}%" for x in bw.p_top10],
                        "Specs ": [f"{a}/{b}" for a, b in zip(bw.specs_in_top10, bw.n_specs)]})
    S += [P("Final rankings", H2), table(top, [1.1 * cm, 4.2 * cm, 1.8 * cm, 1.4 * cm, 4.2 * cm, 1.8 * cm, 1.4 * cm], fs=8.3),
          P("P(top-10): share of 300 match-level bootstrap resamples keeping the player in the top 10. Specs: number of alternative specifications (competition, innings, pressure threshold, opposition weighting, near-best methods) that also place him in the top 10.", SM)]

    S += [P("1. Approach in one paragraph", H2), P(
        "Pressure is <b>leverage</b>: how much the next delivery can swing the batting side's probability of winning, from an out-of-fold win-probability model. "
        "Two independently built solutions were developed. Solution A rates players on context-adjusted value (runs above what an average player would produce in the same situation, with a state-dependent cost for wickets), shrunk for sample size. "
        "Solution B rates batters on pressure strike rate over the highest-leverage balls and bowlers on shrunk pressure economy plus win probability added. "
        "Neither was best everywhere, so the final method is a <b>hybrid</b>, and the blend weight, player pool and optional components were all chosen in a held-out tournament: every candidate ranks players using some matches, and its top 10 is scored on matches it never saw. "
        "The rule, fixed in advance, is best worst case over 16 cells (8 targets x 2 validation schemes). Targets come from both solutions so neither side's yardstick dominates.")]

    contrib = pd.DataFrame([
        ["Pressure = leverage from a win-probability model", "both", "kept"],
        ["Pressure Index x knock-out stakes; top 30% = high pressure (context-adjusted rating)", "A", "kept"],
        ["Within-innings leverage percentile (75/85 batters, 70 bowlers) for the rate components", "B", "kept"],
        ["Runs above expected + state-dependent wicket cost; out-of-fold expectation models", "A", "kept (rating)"],
        ["Empirical-Bayes shrinkage; 50/50 direct + hierarchical blend", "A", "kept"],
        ["Pressure strike-rate ensemble (cut-offs 75 + 85), no shrinkage", "B", "kept (batters)"],
        ["Shrunk pressure economy + WPA (k = 500)", "B", "kept (bowlers)"],
        ["Eligibility: 150 pressure balls, 12 matches, 150 usual balls", "A", "won pool test"],
        ["Delivered-under-pressure gate (observed pressure value above average)", "A", "kept (bowlers)"],
        ["Scope IPL + T20I only (emerging A-team events excluded)", "B", "kept"],
        ["Method choice by held-out top-10 gain, maximin rule", "B", "kept"],
        ["Usual-level uplift (pressure level minus own usual level)", "A", "kept, both roles"],
        ["Match consistency (share of pressure matches with a top-quartile contribution)", "A", "kept (batters)"],
        ["Opposition down-weighting, Elo in WP model", "A", "kept"],
        ["Bootstrap rank intervals + specification support counts", "A + B", "kept"],
    ], columns=["Ingredient", "From", "Outcome"])
    S += [P("2. What the hybrid takes from each solution", H2), table(contrib, [10.5 * cm, 1.6 * cm, 3.2 * cm], fs=7.4)]

    S += [P("3. Defining pressure", H2), P(
        "The required rate, wickets in hand, balls left, phase and closeness interact, so they are combined inside a win-probability model rather than hand-weighted. "
        "Separate gradient-boosted models for each innings use monotone constraints, DLS-revised targets and overs, and a pre-match Elo difference, so mismatches carry less pressure. "
        f"All values are out-of-fold (5 folds grouped by match). AUC: 1st innings {wpm.auc[0]:.3f}, chase {wpm.auc[1]:.3f}. "
        "A multiclass outcome model gives P(0,1,2,3,4,6,wicket,extra) for each ball. Leverage = sum over outcomes of P(outcome) x |WP after - WP before|, normalised so the average ball = 1. "
        "Two views of the same leverage are used: the Pressure Index (leverage x 1.15 in knock-outs; top 30% of all balls = high pressure) for the context-adjusted rating, "
        "and the within-innings leverage percentile for the rate components (it stops every chase start from looking high-pressure)."),
        img("pressure_maps.png", W_)]
    dd = defs.copy(); dd["definition"] = [s.split(" - ")[0] for s in dd.definition]
    dd = dd[["definition", "share of balls flagged", "share of total |WPA| in flagged balls", "decisiveness ratio", "dismissal % (pressure)", "dismissal % (routine)", "run rate (pressure)", "run rate (routine)"]].round(2)
    dd.columns = ["definition", "% balls", "% of |WPA|", "decisiveness", "out% P", "out% R", "RR P", "RR R"]
    S += [KeepTogether([P("<b>Does it separate pressure from ordinary play?</b> Leverage puts about twice its share of the match-deciding win-probability swing into the balls it flags. A hand-weighted stress score and a simple rule-based definition both do much worse.", B),
                        img("definitions.png", W_ * 0.78), table(dd, fs=7)])]

    recipe_txt = (f"<b>Final batter score</b> = {describe(ch['bat'], 'bat')}, over regular pressure batters (at least {MIN_PRESSURE_BALLS_BAT} pressure balls, {MIN_PRESSURE_MATCHES} matches, {MIN_BASELINE_BALLS} usual balls). "
                  + (f"The A composite = {Wt['bat'][0]:.2f} x z(rating) + {Wt['bat'][1]:.2f} x z(uplift) + {Wt['bat'][2]:.2f} x z(match consistency), weights proportional to each component's split-half reliability with uplift floored at 0.15. " if components(ch['bat'])['composite'] else "")
                  + "Uplift = pressure level minus the player's own usual level; match consistency = share of pressure matches with a top-quartile win-probability contribution.<br/>"
                  + f"<b>Final bowler score</b> = {describe(ch['bowl'], 'bowl')}, same pool. "
                  + ("The gate term means a bowler whose observed pressure value is below league average cannot rank above one who delivered. " if components(ch['bowl'])['gate'] else "")
                  + "Both roles therefore score the comparison with usual level that the brief asks for.")
    S += [P("4. Measuring performance - the final recipes", H2), P(
        "<b>Context-adjusted rating (from A).</b> Out-of-fold models estimate what an average player would produce in exactly the same situation: innings, over, balls and wickets left, score, chase equation, Pressure Index, Elo, pace or spin, competition, opposition tier and season. "
        "Batter value per ball = (runs - expected) - wicket cost x (out - P(out)); bowler value = (expected conceded - conceded) + wicket cost x (wicket - P(wicket)). "
        f"The wicket cost comes from an expected-remaining-runs model: {wicket_cost_text()}. "
        "Run and wicket parts are shrunk separately (empirical Bayes, DerSimonian-Laird). The rating averages the direct pressure estimate with a hierarchical one (own overall level + shrunk pressure deviation). Balls against Associates count 0.5."),
        P("<b>Rate components (from B).</b> Batters: pressure strike rate at leverage percentile 75 and 85, each z-scored. Bowlers: minus runs per ball and win probability added per ball at percentile 70, each shrunk toward the pool mean with strength 500 and z-scored."),
        P(recipe_txt)]

    # ================= ITERATION JOURNEY =================
    jb = journey_rows(sel, "bat", ch["bat"], bu["bat"]); jw = journey_rows(sel, "bowl", ch["bowl"], bu["bowl"])
    db_, dw_ = {a[0]: a for a in jb}, {a[0]: a for a in jw}
    labs = list(dict.fromkeys([a[0] for a in jb if a[0] != "FINAL hybrid"] + [a[0] for a in jw if a[0] != "FINAL hybrid"] + ["FINAL hybrid"]))
    f = lambda D, l, i, fmt: (fmt.format(D[l][i]) if l in D else "same as final")
    jt = pd.DataFrame([[l, f(db_, l, 2, "{:.3f}"), f(db_, l, 1, "{:+.3f}"), f(dw_, l, 2, "{:.3f}"), f(dw_, l, 1, "{:+.3f}")] for l in labs],
                      columns=["Stage", "Bat mean", "Bat worst", "Bowl mean", "Bowl worst"])
    log = pd.DataFrame([
        ["0", "Simplest ideas", "Rank by raw pressure strike rate / economy, or by most pressure balls", "On their worst cell, volume and raw rates are no safer than random; finishers dominate because context is ignored"],
        ["1", "Define pressure", "Rule-based (chase RRR 9+, overs 17-20, early collapse) vs hand-weighted stress vs model leverage", "Leverage packs 2x its share of match-deciding swing into flagged balls; the rules ~1.2x. Leverage adopted"],
        ["2", "A v1", "Runs above expected, one joint shrinkage, top 25% pressure", "Reliability ~0.01-0.07: one dismissal (~9 runs) swamps the signal"],
        ["3", "A v2", "Shrink run and wicket parts separately", "Small gain (0.04 / 0.05)"],
        ["4", "A v3", "Switch to win-probability lens WPA/LI", "Looked great (0.31 / 0.23) but diagnostics showed context drift; rejected as a bias"],
        ["5", "A v4", "Centre WPA/LI within innings x phase x pressure cells", "Honest but modest (0.11 / 0.13)"],
        ["6", "A v5", "Run value + direct empirical-Bayes shrinkage", "Most faithful to the pressure sample, least stable"],
        ["7", "A v6", "Blend direct + hierarchical; reliability-weighted composite with usual-level & consistency", "0.22 / 0.17 reliability; 2022-24 to 2025-26 prediction validated"],
        ["8", "Solution B (independent)", "Strike rate / economy + WPA chosen purely by held-out prediction, maximin rule", "Strong on strike-rate targets; ignores dismissals and context; small batter samples"],
        ["9", "Head-to-head A vs B", "Same deliveries, same unseen splits, 8 targets", "No overall winner: A better at dismissal avoidance, B at strike rate; bowlers tied"],
        ["10", "Hybrid tournament", f"{n_cand} candidates mixing A and B, three pools, gates, extra terms", "Hybrid beats both parents on worst case and/or mean"],
        ["11", "Brief constraint", "Only candidates scoring pressure vs usual level may be chosen", "Bowler score now includes uplift; cost shown in section 6"],
    ], columns=["Step", "Version", "What changed", "What the data said"])
    S += [PageBreak(), P("5. How we got here - from a simple approach to the final hybrid", H2), P(
        "The final method was not designed in one go. We started from the simplest possible rankings and changed one thing at a time. "
        "Each version was judged on evidence: does the score agree with itself on different matches (split-half reliability), and does it pick players who perform under pressure in matches it never saw? "
        "Ideas that looked good but failed those checks were dropped, including some that flattered our early results.", B),
        table(log.apply(lambda c: c.map(lambda v: P(str(v), SM))), [0.9 * cm, 2.6 * cm, 6.2 * cm, 6.3 * cm], fs=6.9),
        P("<b>Phase 1 - simple baselines.</b> Ranking by volume (most pressure balls) or by raw pressure strike rate or economy can look fine on average, but on their worst held-out cell they are no safer than a random pick, because they confuse role with skill: death-over finishers always score faster.", B),
        P("<b>Phase 2 - solution A, six versions.</b> We built a leverage-based pressure index and a context-adjusted run value, then improved the reliability of the score version by version. "
          "We dropped the most flattering version (v3) because a diagnostic showed it was partly measuring context rather than skill.", B),
        img("hyb_iter_A.png", W_ * 0.85),
        P("<b>Phase 3 - an independent second solution and a fair fight.</b> Solution B was built separately and chose its scoring purely by held-out prediction. "
          f"On identical unseen splits neither dominated. For batters, A minus B was {h2h['bat'].loc['B-def | strike rate', 'mean']:+.2f} on strike rate "
          f"but {h2h['bat'].loc['A-def | dismissal-avoid', 'mean']:+.2f} on dismissal avoidance; bowlers were within one standard error on every run measure. Each had found something the other missed.", B),
        P("<b>Phase 4 - hybrid tournament.</b> We combined the two, and every candidate mix was scored on the same 16 held-out cells. "
          "The chart puts the whole journey on that single yardstick. Each step up is a measured improvement on matches the method never saw, not a change of opinion.", B),
        img("hyb_journey.png", W_), table(jt, fs=7.2),
        P("Mean = average gain over 8 targets x 2 schemes (30 random half-splits, 6 past-to-future cuts); worst = the weakest of those 16 cells. Same splits and targets for every row.", SM)]

    S += [PageBreak(), P("6. How the hybrid was chosen - held-out tournament", H2), P(
        "Schemes: 30 random half-splits of matches and 6 past-to-future cuts (train on the first 50-85% of matches by date, test on the rest). "
        "Targets, measured only on unseen matches for players with at least 30 pressure balls there: strike rate, runs above expected, win probability added per ball and dismissal avoidance for batters; "
        "economy, runs saved versus expected, win probability added and wickets per ball for bowlers. Each is measured under both pressure definitions, giving 8 targets x 2 schemes = 16 cells. "
        f"Gain = (mean target of the selected 10 - pool mean) / pool SD. {n_cand} candidates per role were tested: blend weights 0.33-1.0 between A's rating or A's full composite and B's components, three pool rules, with and without usual-level and consistency terms, with and without the gate, plus the simple baselines. "
        "Rule, fixed in advance: among candidates whose score contains the pressure-vs-usual comparison (the brief's requirement), take the best worst cell, and among those within 0.03 of it, the best mean.", B),
        img("hyb_tournament_bat.png", W_), img("hyb_tournament_bowl.png", W_)]
    def g(r, k, c):
        return sel[(sel.role == r)].loc[k, c]
    note = (f"Batters: hybrid worst {g('bat', ch['bat'], 'worst_cell'):+.3f} / mean {g('bat', ch['bat'], 'mean_cell'):.3f} vs A {g('bat', 'A: solution A (shipped)', 'worst_cell'):+.3f} / {g('bat', 'A: solution A (shipped)', 'mean_cell'):.3f} "
            f"and B {g('bat', 'B: solution B recipe', 'worst_cell'):+.3f} / {g('bat', 'B: solution B recipe', 'mean_cell'):.3f}. "
            f"Bowlers: hybrid {g('bowl', ch['bowl'], 'worst_cell'):+.3f} / {g('bowl', ch['bowl'], 'mean_cell'):.3f} vs A {g('bowl', 'A: solution A (shipped)', 'worst_cell'):+.3f} / {g('bowl', 'A: solution A (shipped)', 'mean_cell'):.3f} "
            f"and B {g('bowl', 'B: solution B recipe', 'worst_cell'):+.3f} / {g('bowl', 'B: solution B recipe', 'mean_cell'):.3f}. "
            "B keeps an edge on future strike-rate targets (it is built from strike rate), but its worst cells are far lower. "
            f"Cost of the brief's usual-level requirement: the best bowler candidate without it scores {g('bowl', bu['bowl'], 'worst_cell'):+.3f} / {g('bowl', bu['bowl'], 'mean_cell'):.3f}, "
            f"against {g('bowl', ch['bowl'], 'worst_cell'):+.3f} / {g('bowl', ch['bowl'], 'mean_cell'):.3f} for the chosen one.")
    show = []
    for r in ["bat", "bowl"]:
        s = sel[sel.role == r].copy(); s["role"] = r
        keep = list(dict.fromkeys(["A: solution A (shipped)", "B: solution B recipe", ch[r], bu[r]] + s.drop("random").head(5).index.tolist() + ["random"]))
        t = s.loc[keep, ["role", "worst_cell", "mean_cell", "random_mean", "future_mean"]].round(3)
        t.insert(0, "candidate", [("* " if k == ch[r] else "") + k for k in keep])
        show.append(t)
    S += [table(pd.concat(show).reset_index(drop=True), fs=6.8),
          P("* = chosen by the pre-stated rule: best worst cell, and among candidates within 0.03 of it, the best mean. " + note, SM)]

    def evtab(r):
        e = ev[r].copy(); e.insert(0, "player", tabs[r].head(10).player.values); e.insert(0, "#", range(1, 11))
        return table(e.round(1), fs=6.4)
    S += [PageBreak(), P("7. Evidence for the top 10 - batters", H2), img("hyb_top10_bat.png", W_ * 0.85), evtab("bat"),
          P("P = high-pressure (leverage percentile 75+), usual = all other balls. RAE = runs above expected per 100 balls under the Pressure Index definition (wicket-adjusted). WPA in percentage points per ball. Usual-level columns answer the brief's 'compared with their usual performance' question directly.", SM),
          PageBreak(), P("8. Evidence for the top 10 - bowlers", H2), img("hyb_top10_bowl.png", W_ * 0.85), evtab("bowl"),
          P("P = leverage percentile 70+. Positive RAE saved = fewer runs than an average bowler in the same situations (wicket-adjusted).", SM)]

    S += [PageBreak(), P("9. Fair comparisons", H2), P(
        "<b>Sample size:</b> the eligibility rule (from A) won the pool test against B's top-quartile pool. It removes 80-90-ball samples, and A's rating component is shrunk. "
        "<b>Context:</b> the A component is judged against an average player in the same situation, so openers and finishers are compared fairly. B's strike-rate component rewards what matters most in high-leverage overs. "
        f"<b>Opposition:</b> balls against Associates weighted {OPP_WEIGHT['ASSOC']}; Elo in the win-probability model. "
        "<b>IPL and T20I</b> are pooled; competition is a feature in every expectation model, and IPL-only and T20I-only re-rankings are part of the specification count. "
        "<b>Comparison with usual level:</b> every player's pressure and usual figures are reported side by side, and both scores contain an explicit uplift term: pressure level minus the player's own usual level. "
        "The term is deliberately modest, because the data show pressure performance behaves mostly like a stable skill rather than a switch that turns on.")]
    S += [P("10. Reliability and limitations", H2), img("hyb_boot_bat.png", W_ * 0.7), img("hyb_boot_bowl.png", W_ * 0.7), P(
        "- Ranks 1-4 in each list are well supported; places 7-10 sit in a crowded band. No method keeps more than about 6-7 of its 10 names across resamples, which is a limit of the data.<br/>"
        f"- Predictive power is real but modest: on unseen matches the final top 10 averages +{g('bat', ch['bat'], 'mean_cell'):.2f} pool SD for batters and +{g('bowl', ch['bowl'], 'mean_cell'):.2f} for bowlers, and the weakest cells (dismissal avoidance, wickets per ball) are slightly negative.<br/>"
        "- Team totals are rebuilt from bat runs plus the recorded extras: 404 of 406 winning chases (99.5%) reach the target; the two exceptions are rain-reduced DLS matches whose revised target is not in the feed.<br/>"
        "- First-innings win probability is inherently uncertain (AUC ~0.71), so first-innings leverage is flatter.<br/>"
        "- Players whose pressure balls come mostly from one competition carry extra cross-competition uncertainty.", B)]
    S += [P("11. Reproducibility", H2), P(
        "<font face='Courier'>SUPERR_DATA=/path/to/csvs ./run_all.sh</font> runs: s01_prepare - s02_pressure - s03_value - s05_validate - s04_rank (solution A for reference) - "
        "s07_hybrid_select (tournament) - s08_hybrid_final (final lists, bootstrap, specs) - s09_hybrid_report (this PDF). Seed 42; all tunables are in config.py; the hybrid recipes are in hybrid.py. "
        "docs/ holds the recorded development logs used in section 5 (solution A's version history and the A-vs-B head-to-head), each produced by code in the earlier solution packages.", B)]
    doc.build(S)
    print("[OK] hybrid report written")


if __name__ == "__main__":
    main()
