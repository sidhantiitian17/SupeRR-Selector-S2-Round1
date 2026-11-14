"""Chapters 16-22 and appendices."""
from rlib import *
import deck as dk   # FIT / AVAIL tables used on the deck (same wording, one source)

TB, TW = D["top"]["bat"], D["top"]["bowl"]


def pcards(rows, role):
    out = []
    for r in rows:
        img = photo(r["pid"])
        im = f'<img src="{img}"/>' if img else '<div style="width:54px;height:54px;border-radius:10px;background:#efe9f5"></div>'
        if role == "bat":
            line = f'SR {r["P SR"]:.0f} under pressure vs {r["usual SR"]:.0f} usual · {r["P balls"]} pressure balls · {r["P outs"]} outs'
        else:
            line = f'Economy {r["P econ"]:.1f} under pressure vs {r["usual econ"]:.1f} usual · {r["P balls"]} pressure balls · {r["P wkts"]} wkts'
        col = PINK if role == "bat" else BLUE
        out.append(f'<div class="pcard">{im}<div style="flex:1"><div style="display:flex;justify-content:space-between"><b style="font-family:Archivo">{r["rank"]}. {r["player"]}</b>'
                   f'{chip(f"{r["p_top10"]}% top-10", col)}</div><div class="small m">{line}</div><div class="small m">{r["specs"]}/{r["n_specs"]} specifications agree</div></div></div>')
    return '<div class="grid2" style="gap:8px">' + "".join(out) + "</div>"


# =============================================================================================== 16
def ch16():
    bt = table(["#", "Batter", "Pressure balls", "SR pressure", "SR usual", "Balls per out (pressure)", "Runs above exp. /100 (pressure)", "IPL share"],
               [[r["rank"], r["player"], r["P balls"], f'{r["P SR"]:.1f}', f'{r["usual SR"]:.1f}', f'{r["P balls/out"]:.1f}', f'{r["P RAE/100"]:+.1f}', f'{r["IPL %"]:.0f}%'] for r in TB], num=(2, 3, 4, 5, 6, 7))
    wt = table(["#", "Bowler", "Pressure balls", "Economy pressure", "Economy usual", "Wickets", "Runs saved /100 (pressure)", "IPL share"],
               [[r["rank"], r["player"], r["P balls"], f'{r["P econ"]:.2f}', f'{r["usual econ"]:.2f}', r["P wkts"], f'{r["P RAE saved/100"]:+.1f}', f'{r["IPL %"]:.0f}%'] for r in TW], num=(2, 3, 4, 5, 6, 7))
    return chapter("16", "The answer", "Results: the top 10 batters and bowlers",
                   "These are the final lists from <code>FINAL_TOP10_HYBRID.csv</code>. Each player is shown with his record under pressure next to his usual record, which is the comparison the brief asks for.") + f"""
<h2>Batters</h2>
{pcards(TB, "bat")}
<div style="height:8px"></div>
{bt}
<p class="small m">Pressure here = the report's evidence view (within-innings leverage percentile ≥ 75); usual = all other balls. Runs above expected uses the Pressure Index definition and includes the wicket cost.</p>
<h3>What the batting list says</h3>
<ul><li><b>Vaibhav Sooryavanshi</b> is a clear #1: a strike rate of 245 under pressure (207 usual) and only 8 dismissals in 192 pressure balls. He stays top 10 in 94% of resamples. He is already a Rajasthan Royals player.</li>
<li><b>Most of the list are attacking top-order players</b> (Priyansh Arya, Abhishek Sharma, Travis Head, Finn Allen, Phil Salt). In T20, fast scoring on high-leverage balls in the powerplay is one of the biggest pressure skills.</li>
<li><b>The middle-order specialists</b> are Heinrich Klaasen, Suryakumar Yadav and Dewald Brevis; <b>Rovman Powell</b> is the finisher. These matter most for RR (Chapter 17).</li>
<li><b>The biggest rises</b> are Dewald Brevis (strike rate 188 under pressure vs 142 usually) and Rovman Powell (178 vs 138).</li></ul>
<h2>Bowlers</h2>
{pcards(TW, "bowl")}
<div style="height:8px"></div>
{wt}
<p class="small m">Pressure = within-innings leverage percentile ≥ 70. Positive runs saved = fewer runs than an average bowler in the same situations, wicket-adjusted.</p>
<h3>What the bowling list says</h3>
<ul><li><b>Josh Hazlewood</b> is #1: economy 7.6 under pressure against 8.6 usually, 48 wickets in 504 pressure balls, top 10 in all 39 specifications.</li>
<li><b>Spin and pace are both represented</b>: Mujeeb, Abrar, Mahedi, Varun and Nawaz bowl spin; Hazlewood, Mohsin, Bumrah, Taskin and Rauf bowl pace.</li>
<li><b>Several are mostly T20I players</b> (IPL share under 2%): Mujeeb, Abrar, Mahedi, Taskin, Nawaz, Rauf. Their ratings carry a little more cross-competition uncertainty, and three of them (Pakistan players) are not in the IPL auction pool.</li>
<li><b>Bumrah is #5, not #1</b>, partly because his usual level is even higher than his pressure level (uplift −0.19): he is brilliant all the time rather than better under pressure. The bowler score includes the uplift term, so this is the brief's comparison at work.</li></ul>
</section>"""


# =============================================================================================== 17
def ch17():
    g = D["rr_gaps"]
    seg = {"PP": "Powerplay", "MID": "Middle overs", "DEATH": "Death overs"}
    gt = table(["RR", "Phase", "Pressure balls", "Value /100 pressure balls", "Median team", "Rank of 10", "RR runs/over", "Median runs/over"],
               [["Batting" if r["side"] == "bat" else "Bowling", seg[r["seg"]], r["RR balls"], f'{r["RR val/100"]:+.1f}', f'{r["median team"]:+.1f}',
                 f'<b class="{"gd" if r["RR rank/10"] <= 3 else ("bd" if r["RR rank/10"] >= 7 else "")}">#{r["RR rank/10"]}</b>', f'{r["RR rpo"]:.2f}', f'{r["median rpo"]:.2f}'] for r in g], num=(2, 3, 4, 5, 6, 7))
    fitc = {"core": GOOD, "high": PINK, "mid": WARN, "low": "#8a7f9c", "bench": "#8a7f9c"}
    flab = {"core": "CORE", "high": "HIGH FIT", "mid": "SITUATIONAL", "low": "LOW FIT", "bench": "BENCHMARK"}
    ft = table(["Player", "Team / availability", "Fit", "Why"], [[p, f'{dk.AVAIL[p][0]} · {dk.AVAIL[p][1]}', chip(flab[dk.FIT[p][0]], fitc[dk.FIT[p][0]]), dk.FIT[p][1]] for p in list(dk.FIT)])
    w = D["watch"]
    wl = table(["Player", "Team", "Recent rank", "Stable in"], [[p["name"], p["team"], f'#{p["rk"]}', f'{p["ptop"]:.0%}'] for p in w["bat"] + w["bowl"]], num=(2, 3))
    a = next(r for r in w["rr"] if r["name"] == "Jofra Archer")
    pl = Flow(680, 300)
    pl.node("rr", 6, 115, 120, 70, "RR · IPL 2027", "", "d", align="center")
    for i, (k, t1, t2, kind) in enumerate([("p1", "1 · Retain the powerplay engine", "Vaibhav Sooryavanshi: #1 batter, 94% of resamples, keeps RR's #1 powerplay.", "g"),
                                            ("p2", "2 · Fix the middle overs (Gap 1)", "Klaasen (SR 197 vs spin under pressure) → Suryakumar → Brevis, in order of fit and availability.", "p"),
                                            ("p3", "3 · Death + new-ball pace (Gaps 2–3)", "Indian slot: Mohsin Khan. Overseas: Hazlewood if released; auction-pool option: Taskin Ahmed.", "p"),
                                            ("p4", "4 · Don't buy another opener", "Abhishek, Head, Allen, Salt, Priyansh are elite but play RR's strongest phase.", "n")]):
        pl.node(k, 190, 6 + i * 74, 484, 64, t1, t2, kind)
        pl.edge("rr", k, "r", "l", ta=0.2 + i * 0.2)
    return chapter("17", "Using the answer", "From a ranking to a plan for Rajasthan Royals",
                   "A list of the best pressure players is not a squad plan. RR need players who fix their actual weaknesses, and who can actually be bought. We measured RR's own pressure record phase by phase, matched each top-10 player to those gaps, and checked availability.") + f"""
<h2>Step 1: where does RR lose pressure moments?</h2>
<p>We used the same value-per-ball measure on RR's IPL 2025–26 matches only, split by phase, and ranked RR among the 10 IPL teams (value per 100 pressure balls; #1 = best).</p>
{gt}
{stats([("#1", "Powerplay batting: RR's strength (+33.0 vs median +10.4)"), ("#7", "Middle-overs batting: Gap 1 (−1.6 vs +9.1)"), ("#8", "Death bowling: Gap 2 (−14.2 vs −1.5)"), ("#7", "Powerplay bowling: Gap 3 (−12.6 vs −7.9)")])}
<p class="small m">Context: RR finished 9th in IPL 2025 (4 wins) and 4th in IPL 2026 (8 wins), per Cricxtasy and MyKhel.</p>
<h2>Step 2: does each top-10 player fix a gap?</h2>
<p>For each player we split his pressure balls by phase (powerplay, middle, death) and looked at his value in each. A player whose pressure work is mostly in RR's strong phase is a \"low fit\" however good he is.</p>
{ft}
<h2>Step 3: can RR actually get him?</h2>
<p>The IPL 2027 cycle has a mini-auction, so most players stay with their franchises. The dates below are from BCCI as reported by CricTracker and Sportsdigest in November 2026:</p>
{table(["Date", "What happens", "What it means for RR"], [["17 Nov 2026", "Retention and release lists due", "Keep the core (Vaibhav)"], ["23 Nov 2026", "Player registration closes", "Shows who is in the auction pool"],
                                                         ["9 Dec 2026", "Trade window closes", "Route for contracted targets (Klaasen, Suryakumar, Hazlewood)"], ["16 Dec 2026", "Mini-auction, Goa", "Last chance before the 2028 mega auction"]])}
<h2>Step 4: the recommendation</h2>
{fig(pl.svg(), "<b>Figure 17.1</b> Four moves in priority order, each tied to a measured gap.")}
<h2>The watchlist (recent form)</h2>
<p>The official list uses 2022–26. To be fair to players in form, we also ranked 2025–26 only (at least 120 pressure balls) and kept players who are top 10 there in at least 50% of 1,000 resamples and are not in the official list. This is context, not a change to the list.</p>
{wl}
<h2>A hard case: Jofra Archer</h2>
<p>RR's own strike bowler comes out <b>#{a["official"]}</b> among bowlers and is top 10 in only {a["ptop"] * 100:.1f}% of resamples. Under pressure his runs saved per 100 balls swing by season: {" · ".join(f'{s["y"]} {s["v"]:+.1f}' for s in a["seasons"])}. In IPL 2026 he took {a["s26"]["w"]} wickets in {a["s26"]["m"]} matches, with a pressure economy of {a["s26"]["pm"]:.2f} against {a["s26"]["um"]:.2f} usually. He is a valuable all-phase bowler, but his pressure numbers are not stable enough to call him RR's death-overs fix. We kept him out of the top 10 because the data say so (Chapter 19).</p>
</section>"""


# =============================================================================================== 18
def ch18():
    k = D["pick_bat"]; r = next(x for x in TB if x["player"] == "Heinrich Klaasen"); rm = k["rr_mid"]
    img = photo(4260)
    return chapter("18", "Annexure B", "The player pick we are backing: Heinrich Klaasen",
                   "If RR can make one batting move, it should be the player who best fixes their biggest gap: middle-overs pressure batting, especially against spin.") + f"""
<div style="display:grid;grid-template-columns:150px 1fr;gap:14px;align-items:start">
<div style="background:#221b30;border-radius:12px;height:190px;position:relative;overflow:hidden"><img src="{img}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:contain;object-position:bottom"/></div>
<div>{stats([(f'#{r["rank"]}', "official batter rank"), (f'{r["p_top10"]}%', "top 10 in resamples"), (f'{r["specs"]}/{r["n_specs"]}', "specifications agree"), (f'{k["pressure"]["v"]:+.1f}', "runs above expected per 100 pressure balls")], cols=2)}</div></div>
{fig(panel("He fixes RR's biggest batting gap", "strike rate against spin in the middle overs under pressure (RR and league: IPL 2025–26; Klaasen: 2022–26)",
           ch.hbars([("RR vs spin", rm["rr_spin"]["sr"], "#f43f5e"), ("League vs spin", rm["lg_spin"]["sr"], "#6e6680"), ("Klaasen vs spin", k["spin"]["sr"], PINK)], 640, 200, maxv=220, fmt="{:.0f}", label_w=160), 640, 200),
     "<b>Figure 18.1</b> RR's middle-order scores at 135 against spin under pressure; the league scores at 148; Klaasen at 197.")}
<div class="grid2">{panel("Positive in every season", "runs above expected per 100 pressure balls", ch.season_bars(k["seasons"], 330, 240, PINK), 330, 240)}
<div>{table(["", "Under pressure", "Usual"], [["Strike rate", f'<b class="pk">{k["pressure"]["sr"]:.1f}</b>', f'{k["usual"]["sr"]:.1f}'], ["Runs above exp. /100", f'<b class="pk">{k["pressure"]["v"]:+.1f}</b>', f'{k["usual"]["v"]:+.1f}'],
                                                  ["Balls per dismissal", f'{k["pressure"]["pb"] / k["pressure"]["outs"]:.1f}', f'{k["usual"]["pb"] / k["usual"]["outs"]:.1f}'], ["Balls", k["pressure"]["pb"], k["usual"]["pb"]]], num=(1, 2))}
<p class="small m">Pressure = top 30% Pressure Index, 2022–26. The leverage-percentile view gives the same picture: SR {r["P SR"]:.1f} vs {r["usual SR"]:.1f}.</p></div></div>
<h2>The honest case</h2>
<ul><li><b>Right phases.</b> {k["phases"]["MID"]["pb"]} middle-overs pressure balls at {k["phases"]["MID"]["v"]:+.1f}/100 and {k["phases"]["DEATH"]["pb"]} death balls at {k["phases"]["DEATH"]["v"]:+.1f}: exactly where RR rank 7th and 5th.</li>
<li><b>Both innings.</b> Chasing {k["chase"]["v"]:+.1f}/100, setting {k["setting"]["v"]:+.1f}/100.</li>
<li><b>Not a one-season wonder.</b> Positive every season 2022–26; 2025 was quiet ({k["seasons"][3]["v"]:+.1f}), 2026 back to {k["seasons"][4]["v"]:+.1f}.</li>
<li><b>The price of attacking.</b> He gets out more often under pressure (every {k["pressure"]["pb"] / k["pressure"]["outs"]:.1f} balls vs {k["usual"]["pb"] / k["usual"]["outs"]:.1f}). That cost is already charged inside his +{k["pressure"]["v"]:.1f} value through the wicket cost.</li>
<li><b>The route.</b> He holds an overseas slot and an SRH contract, so it is a trade before 9 December or a release. Fallback: Dewald Brevis (64% middle overs, +26.4/100, young).</li></ul>
{box("why", "<p>We did not pick the #1 batter. Vaibhav is already RR's, and the next names are openers, RR's strongest phase. The best pick for a team is the best player <i>for its gap</i>, not the best player overall.</p>")}
</section>"""


# =============================================================================================== 19
def ch19():
    m = [("The result that looked too good", "Solution A v3 jumped to 0.31 reliability, far ahead of every earlier version. A diagnostic showed it was measuring match context, not skill.", "We dropped it, even though it flattered our results.", BAD),
         ("Two teams, no winner", "Solutions A and B were built separately. On the same unseen matches, A won on dismissals and B on strike rate. Each side wanted its own method to win.", "We wrote the selection rule first, then ran the tournament and accepted its answer.", WARN),
         ("\"Why isn't Archer in?\"", "RR's own strike bowler came out #45. It was tempting to nudge the method until he appeared in the top 10 of a deck made for RR.", "We stayed with the data and added a clearly labelled watchlist and an Archer review instead.", JER),
         ("Dashboard ≠ report", "A judge-facing chart showed Vaibhav at +76.9; the report said +48.7. Two pressure definitions had crept into different parts of the work.", "We unified on the report's definition and built a verifier: 10,172 checks, 0 failed.", PINK)]
    cards = "".join(f'<div class="nobreak" style="border:2px solid {c};border-radius:12px;padding:10px 12px;margin-bottom:10px"><div style="font-family:Archivo;font-weight:850;font-size:12pt">{i + 1}. {a}</div><p style="margin:5px 0">{w_}</p><p style="margin:0;color:{c};font-weight:700">→ {d}</p></div>' for i, (a, w_, d, c) in enumerate(m))
    rows = [("Pressure definition", "Overs 17–20 + required rate 9+ (the obvious rule)", "Win-probability leverage, validated (2.06× decisive share)"),
            ("Rating", "Raw pressure strike rate", "Context-adjusted value, shrunk, + pressure SR, chosen on unseen matches"),
            ("Best-looking version", "A v3 (0.31 reliability)", "Rejected: it measured context"),
            ("RR's own players", "Nudge Archer into the top 10", "Official list untouched; watchlist + RR review shown separately"),
            ("Dashboard numbers", "Two pressure definitions mixed", "Generated from the pipeline and checked: 10,172 checks"),
            ("Choosing the method", "Pick the version we liked best", "Pre-stated rule on 16 held-out cells: best worst case, then best mean")]
    return chapter("19", "Annexure C", "War-room moments",
                   "Four moments where the easy answer was wrong, and what the data made us do instead. If a beginner remembers one chapter, it should be this one.") + f"""
{cards}
<h2>The easy answer vs what we shipped</h2>
{table(["Decision", "Easy answer", "Shipped"], rows, "pinkh")}
{box("kid", "<p>Every one of these moments has the same shape: a result that was convenient or flattering, and a check that showed it was wrong. The habit that saved us each time was to ask \"<b>why</b> does this look so good?\" before believing it.</p>")}
<h2>How the dashboard verifier works</h2>
<p>After moment 4, every number shown on the dashboard is generated by scripts from the pipeline outputs, and a separate script (<code>verify_dashboard.py</code>) recomputes each one from <code>deliveries_value.parquet</code> and the rating tables. It also checks the method claims against the text of the methodology PDF. The current build passes 10,172 checks with 0 failures. Any future change that breaks a number fails the build.</p>
</section>"""


# =============================================================================================== 20
def ch20():
    alt = table(["Alternative", "What it does", "Why we did not use it alone"], [
        ["Raw averages / strike rates in the death overs", "Treats overs 16–20 as \"pressure\"", "Flags many dead balls, misses early collapses; 41% of real pressure is in the middle overs; finishers win by role, not skill."],
        ["Total win probability added (WPA)", "Adds up every ball's change in win chance", "Rewards players who happen to bat in tight finishes; extremely noisy; our WPA lens repeated worse than run value."],
        ["Win probability ÷ leverage (WPA/LI)", "Context-neutral win value", "Our v3: looked great, but drifted with context. Used only for consistency, after centring."],
        ["One machine-learning model that predicts \"clutch\"", "Train a model to output a rating", "There is no label for \"clutch\" to train on. Any model would learn our definition back."],
        ["Expert opinion / reputation", "Ask who is clutch", "Not reproducible; biased toward famous players (e.g. Archer)."],
        ["Solution A alone", "Context-adjusted, shrunk", "Safest, but lower average gain on strike-rate targets."],
        ["Solution B alone", "Pressure SR, economy + WPA", "Highest average for batters, but its worst cell (−0.19) means it sometimes picks players who get out a lot."]])
    trade = table(["Trade-off", "What we chose", "What it costs"], [
        ["Safety vs average gain", "Best worst case first (maximin)", "Bowlers: mean 0.213 instead of 0.228 for the best unconstrained method"],
        ["Brief's usual-level comparison vs pure prediction", "Must include an uplift term", "A little average gain for bowlers (shown in Chapter 13)"],
        ["Pooling IPL + T20I vs IPL only", "Pool, with competition as a feature", "Some T20I-heavy players carry extra uncertainty; 3 of the top-10 bowlers are not in the IPL pool"],
        ["Shrinkage vs raw numbers", "Shrink", "Players with few balls but genuine talent (e.g. young players) are held back until they prove it"],
        ["Strict eligibility vs coverage", "150 pressure balls, 12 matches", "Exciting newcomers with short careers are excluded from the official list (covered by the watchlist)"],
        ["Run value vs win value", "Runs for the rating, win probability for pressure and consistency", "The rating does not fully capture \"won the match\" moments; consistency partly brings them back"]])
    return chapter("20", "Judgement", "Why this approach, and what we gave up",
                   "Every method makes trade-offs. This chapter puts our approach next to the obvious alternatives and lists what we gave up to get what we wanted.") + f"""
<h2>Compared with the alternatives</h2>
{alt}
<h2>Why ours is better for this brief</h2>
<ol><li><b>It measures pressure, not phase.</b> Leverage catches twice its share of decisive swing; the death-overs rule catches 1.2×.</li>
<li><b>It compares like with like.</b> Every ball is judged against an average player in the same situation, so openers, anchors and finishers compete fairly.</li>
<li><b>It does not reward luck.</b> Shrinkage, minimum samples, match-level bootstrap.</li>
<li><b>It was chosen by unseen matches, with the rule written first.</b> Neither our opinions nor either solution's own target decided it.</li>
<li><b>It answers every part of the brief.</b> Pressure vs usual level is reported for every player and scored for both roles; uncertainty is shown; the RR plan is tied to measured gaps.</li></ol>
<h2>The trade-offs we accepted</h2>
{trade}
</section>"""


# =============================================================================================== 21
def ch21():
    return chapter("21", "Honesty", "Limitations, and how accuracy could improve",
                   "No method is perfect, and T20 cricket is noisy. Here is what our method cannot do, and what we would try next.") + f"""
<h2>Limitations</h2>
{table(["Limitation", "Effect", "Size"], [
        ["Predictive power is modest", "The top 10 does better than a typical player on unseen matches, but not by a huge margin", "+0.3 to +0.45 pool SD on average; dismissal/wicket targets are the noisiest"],
        ["Ranks 7–10 are close calls", "Small changes in data or settings swap them with the next few players", "No method keeps more than ~6–7 of its 10 names across resamples"],
        ["First-innings win probability is uncertain", "First-innings leverage is flatter, so first-innings pressure is harder to spot", "AUC 0.71 vs 0.90 in chases"],
        ["Missing extra runs in the feed", "Rebuilt chases fall slightly short", "About 1.1 runs on average in the 26% of winning chases that do not reach the target"],
        ["Cross-competition mix", "Players whose pressure balls are mostly T20I (or mostly IPL) are compared through features, not head to head", "Affects several top-10 bowlers"],
        ["No venue, pitch or weather", "A good score at one ground is a poor one at another", "Partly absorbed by the expected-runs models, not explicitly"],
        ["No partner or matchup effects", "A batter's partner and the specific bowler matter", "Not modelled"],
        ["Fielding and all-round value not included", "The lists are pure batting or pure bowling", "Out of scope of the brief"],
        ["Uplift is weakly repeatable", "\"Rises to the occasion\" is mostly not a stable trait in this data", "Split-half ρ between about −0.10 and +0.16"]])}
<h2>Can accuracy improve?</h2>
<p>Yes, but probably not by much from cleverer maths on the same data. The main limit is the amount of pressure data per player, not the model. In order of expected benefit:</p>
<ol><li><b>More data per player.</b> Add other T20 leagues (BBL, PSL, SA20, CPL, The Hundred) and domestic T20. More pressure balls per player would raise reliability more than any modelling change.</li>
<li><b>Better first-innings win probability.</b> A par-score model by venue and season would sharpen first-innings leverage, where the AUC is lowest.</li>
<li><b>Venue and conditions.</b> Add ground, pitch and dew as features in the expected-runs models.</li>
<li><b>Matchups.</b> Model batter-vs-bowler-type (left-arm spin, express pace) under pressure. Our Klaasen analysis shows how useful this is.</li>
<li><b>A single Bayesian model.</b> Replace the separate shrinkage steps with one hierarchical model with player, phase and competition effects. Cleaner, but slower and harder to explain.</li>
<li><b>Ball-tracking data.</b> Line, length and speed would let us value the quality of a delivery, not just its outcome. The <code>bowl_speed</code> column was too patchy (0 in 38.7% of rows) to try.</li>
<li><b>Age curves.</b> Young players improve and older ones decline. An age adjustment would help an auction look forward.</li></ol>
{box("warn", "<p>Each improvement must go through the same tournament. It is easy to add features that make the training data look better and the unseen matches look worse. That trap is exactly what the tournament is for.</p>")}
</section>"""


# =============================================================================================== 22
def ch22():
    tree = """SupeRR-Selector-S2-Round1/
├─ README.md               step-by-step guide
├─ reproduce.sh            one command, end to end
├─ requirements.txt        pinned package versions
├─ data/raw/               the six CSVs
├─ pipeline/
│  ├─ run_all.sh           s01 → s09 in order
│  ├─ src/config.py        every tunable number, seed 42
│  ├─ src/s01 … s09        the steps (see Chapter 4)
│  ├─ src/ratings.py       shrinkage, composite, gate (Solution A engine)
│  ├─ src/hybrid.py        Solution B pieces, candidates, targets
│  └─ outputs/             parquet tables, CSVs, figures, methodology PDF
├─ dashboard/              site, build scripts, verifier, dist/
├─ deck/                   slide sources (HTML/SVG) → PNG, PDF, PPTX
└─ report/                 this guide (HTML → PDF)"""
    arch = Flow(680, 260)
    arch.node("csv", 6, 100, 100, 60, "data/raw", "6 CSVs", "n")
    arch.node("pipe", 140, 20, 170, 220, "pipeline/src", "s01 prepare → s02 pressure → s03 value → s05 validate → s04 Solution A → s07 tournament → s08 final → s09 report", "b")
    arch.node("out", 344, 100, 120, 60, "outputs/", "parquet + CSV + PDF", "v")
    arch.node("dash", 500, 10, 174, 70, "dashboard", "build_data → watchlist → verifier (10,172 checks) → single file", "p")
    arch.node("deck", 500, 95, 174, 60, "deck", "prep → HTML/SVG → PNG/PDF/PPTX", "n")
    arch.node("vc", 500, 175, 174, 70, "Vercel", "live site, auto-deploys from GitHub main", "j")
    arch.edge("csv", "pipe").edge("pipe", "out").edge("out", "dash", "r", "l").edge("out", "deck").edge("dash", "vc", "b", "t", color="#8a7f9c").edge("deck", "dash", "t", "b", color="#c9bfd6", dash=True)
    return chapter("22", "Do it yourself", "Architecture and reproducing everything yourself",
                   "Everything in this guide can be rebuilt from the raw files with one command. This chapter shows how the pieces fit and walks a beginner through running it.") + f"""
{fig(arch.svg(), "<b>Figure 22.1</b> How the parts connect. The pipeline writes outputs; the dashboard and deck read only from those outputs, so they cannot disagree with the method.")}
<h2>The repository</h2>
<pre>{esc(tree)}</pre>
<h2>Step by step for a beginner</h2>
<ol><li><b>Install</b> Python 3.11 or newer and git. Use Linux or macOS (on Windows, use WSL or Git Bash). You need about 2 GB of free memory.</li>
<li><b>Get the code and data.</b><pre>git clone https://github.com/sidhantiitian17/SupeRR-Selector-S2-Round1.git
cd SupeRR-Selector-S2-Round1</pre></li>
<li><b>Install the packages</b> (exact versions are pinned).<pre>python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt</pre></li>
<li><b>Run everything</b> (about 45–60 minutes on a 2-core machine, then about 2 minutes for the dashboard).<pre>./reproduce.sh</pre></li>
<li><b>Check the answer.</b> <code>pipeline/outputs/FINAL_TOP10_HYBRID.csv</code> should list Vaibhav Sooryavanshi and Josh Hazlewood at #1, and the run should end with <code>10172 checks, 0 failed</code>.</li>
<li><b>Explore.</b> Open <code>dashboard/dist/under-pressure-rating.html</code> in a browser, or visit the live site.</li></ol>
{box("why", "<p>We tested this from a clean clone: deleting all outputs and re-running reproduced all 40 data files, tables and figures exactly. The methodology PDF's text was identical on all 10 pages; only its creation timestamp differs. This works because the random seed is fixed (42), package versions are pinned, and every random step (cross-validation folds, splits, bootstrap) uses that seed.</p>")}
<h2>To change a setting</h2>
<p>Every tunable number is in <code>pipeline/src/config.py</code> (Appendix C). Change one, re-run <code>./reproduce.sh</code>, and compare <code>FINAL_TOP10_HYBRID.csv</code>. If you want to test a new idea fairly, add it as a candidate in <code>hybrid.py</code> and let the tournament judge it.</p>
<h2>The dashboard</h2>
<p>The dashboard is plain HTML, CSS and JavaScript with SVG charts: no framework and nothing to install. It has an overview, batter and bowler tables with player profiles, a pressure-model explainer, a player comparison, a match-by-match pressure view, the watchlist and RR review, the methodology, and a Reproduce section with this project's deck, links and steps. <code>build_single_file.py</code> packs it into one HTML file (about 13 MB) that works offline.</p>
<h2>Live links</h2>
<ul><li>Dashboard: <b>https://superr-under-pressure-rating.vercel.app</b></li><li>Code, data and results: <b>https://github.com/sidhantiitian17/SupeRR-Selector-S2-Round1</b></li></ul>
</section>"""


# =============================================================================================== appendices
def appendix():
    gl = [("AUC", "Chance that a model ranks a random winner above a random loser. 0.5 = guessing, 1 = perfect."),
          ("Bootstrap", "Re-drawing the data at random many times to see how much a result changes."),
          ("Brier score", "Average squared gap between a predicted probability and what happened (0 or 1). Lower is better."),
          ("Calibration", "Whether predicted probabilities match real frequencies (70% predictions come true 70% of the time)."),
          ("Cross-validation (grouped, out-of-fold)", "Training on some matches and predicting others, so no prediction comes from a model that saw that match."),
          ("Decisiveness", "Share of match-deciding swing on flagged balls divided by share of balls flagged."),
          ("Elo", "A team strength rating updated after every result."),
          ("Empirical Bayes / shrinkage", "Pulling noisy averages toward the overall average, more for small samples."),
          ("Expected runs", "What an average player would score on this ball in this exact situation."),
          ("Gain (tournament)", "How far above the pool average a method's top 10 performed on unseen matches, in pool standard deviations."),
          ("Gradient boosting / LightGBM", "Many small decision trees, each fixing the errors of the previous ones."),
          ("Leverage (LI)", "Expected size of the change in win probability caused by the next ball; 1.0 = an average ball."),
          ("Maximin", "Choose the option whose worst result is best."),
          ("Monotone constraint", "A rule forcing a model's output to move in one direction as an input grows."),
          ("Pool", "The eligible players a method ranks."),
          ("Pressure Index (PI)", "Leverage × 1.15 in knock-outs; top 30% of balls = high pressure."),
          ("Spearman ρ", "Correlation between two rankings; +1 = same order, 0 = unrelated."),
          ("Split-half reliability", "How well ratings from two random halves of the matches agree."),
          ("Uplift", "A player's pressure level minus his usual level."),
          ("WPA (win probability added)", "Change in the batting side's win probability caused by one ball."),
          ("Wicket cost", "Runs a team loses on average by losing a wicket in this situation."),
          ("Within-innings percentile", "Where a ball's leverage ranks inside its own innings (0–100)."),
          ("z-score", "(value − pool average) / pool standard deviation.")]
    fs = """Win probability      WP = LightGBM(balls left, wickets left, score or runs needed, Elo diff), out-of-fold, monotone
Leverage             LI_raw = sum_o P(o|state) |WP(after o) - WP(now)| ;  LI = LI_raw / mean(LI_raw) ; capped at 99.5th pct
Pressure Index       PI = LI x (1.15 if knock-out else 1.00) ;  high pressure: PI >= 1.114 (top 30%) ; usual: bottom 50%
Wicket cost          Wc = ER(balls left, wickets left) - ER(balls left, wickets left - 1), >= 0
Batter value         (runs - E[runs]) - Wc x (out - P(out))
Bowler value         (E[runs conceded] - runs conceded) + Wc x (wicket - P(wicket))
Shrinkage            shrunk = mean x n / (n + k),  k = sigma2 / tau2  (DerSimonian-Laird), runs and wickets separately
Rating               0.5 x direct + 0.5 x (shrunk overall + shrunk pressure deviation)
Uplift               pressure level - usual level
Consistency          bat: (big matches + 1)/(matches + 4) ; bowl: 1 - (bad matches + 1)/(matches + 4)
A composite          bat 0.511 z(rating) + 0.15 z(uplift) + 0.339 z(consistency) ; bowl 0.665 / 0.15 / 0.185
B batter             z(SR at pct >= 75) + z(SR at pct >= 85)
B bowler             z(shrunk -runs/ball) + z(shrunk WPA/ball) at pct >= 70, shrunk v = mean + n/(n+500)(v - mean)
FINAL batter         0.67 z(A composite) + 0.33 z(B batter)                          pool: 150 P balls, 12 matches, 150 usual balls
FINAL bowler         0.9 z(0.2 z(A rating) + 0.8 z(B bowler)) + 0.1 z(uplift) + 100 x [observed pressure value > 0]
Tournament gain      (mean target of top 10 - pool mean) / pool SD on unseen matches ; rule: best worst of 16 cells, then best mean within 0.03
Bootstrap            300 resamples, Poisson(1) weight per match ; P(top 10) = share of resamples in top 10"""
    cfg = table(["Setting (config.py)", "Value", "Meaning"], [
        ["SEED", "42", "fixed randomness"], ["EXCLUDE_EMERGING", "True", "drop the two A-team events"], ["HIGH_PRESSURE_QUANTILE", "0.70", "top 30% of balls by PI = pressure"],
        ["LOW_PRESSURE_QUANTILE", "0.50", "bottom 50% = usual"], ["Knock-out stakes", "1.15", "multiplier on leverage (s02)"], ["Leverage cap", "99.5th percentile", "winsorise extreme leverage (s03)"],
        ["VALUE_LENS / CONSIST_LENS", "val / wpali", "run value for the rating; centred WPA/LI for consistency"], ["MODEL, BLEND_DIRECT", "blend, 0.5", "50/50 direct + hierarchical"],
        ["MIN_UPLIFT_WEIGHT", "0.15", "floor on the uplift weight"], ["MIN_PRESSURE_BALLS_BAT / BOWL", "150 / 150", "eligibility"], ["MIN_PRESSURE_MATCHES", "12", "eligibility"],
        ["MIN_BASELINE_BALLS", "150", "eligibility (usual balls)"], ["OPP_WEIGHT", "Full 1.0 · IPL 1.0 · A 0.8 · Associate 0.5", "opposition down-weighting"],
        ["BOOTSTRAP_ITERS", "300", "resamples"], ["WP model", "300 trees, lr 0.05, 31 leaves, ≥200 per leaf", "LightGBM settings (s02)"], ["Elo", "start 1500, K = 24", "team strength (s02)"]])
    nums = table(["Quantity", "Value"], [["Raw deliveries / matches with balls", "200,999 / 867"], ["Scoped matches / deliveries", "837 / 193,988 (IPL 87,673 · T20I 106,315)"],
                                         ["Batters / bowlers in data", "824 / 596"], ["Eligible batters / bowlers", "120 / 120"], ["High-pressure / usual balls", "58,197 / 96,994"],
                                         ["PI cut-off (top 30%) / median PI", f'{D["pi_cut"]:.3f} / {D["pi_median"]:.3f}'], ["WP AUC first innings / chase", "0.706 / 0.896"],
                                         ["Decisiveness: PI / stress score / rules", "2.06 / 1.31 / 1.22"], ["Pressure balls by phase", "PP 35% · MID 41% · DEATH 23%"],
                                         ["Wicket cost PP / MID / DEATH", "10.0 / 5.5 / 2.6 runs"], ["Shrinkage k, batter runs / wickets", "259 / 1,402 balls"], ["Shrinkage k, bowler runs / wickets", "607 / 2,294 balls"],
                                         ["Tournament candidates per role", "79 + random"], ["Splits", "30 random + 6 past→future"], ["Hybrid batters worst / mean", "−0.004 / 0.321"],
                                         ["Hybrid bowlers worst / mean", "+0.040 / 0.213"], ["Dashboard checks", "10,172, 0 failed"]])
    return f"""<section class="chapter"><div class="chead"><div class="num">A</div><div><div class="kick">Appendix</div><h1>Glossary</h1></div></div>
{table(["Term", "Plain meaning"], [[f"<b>{a}</b>", b] for a, b in gl])}</section>
<section class="chapter"><div class="chead"><div class="num">B</div><div><div class="kick">Appendix</div><h1>Formula sheet</h1></div></div>
<p>The whole method on one page.</p>{table(["Step", "Formula"], [[f"<b>{a}</b>", f"<span style=\"font-family:DejaVu Sans Mono,monospace;font-size:8.2pt\">{esc(b_)}</span>"] for a, b_ in (__import__("re").split(r"\s{2,}", ln, maxsplit=1) for ln in fs.splitlines())])}
<div class="chead" style="margin-top:22px"><div class="num">C</div><div><div class="kick">Appendix</div><h1>Settings</h1></div></div>{cfg}</section>
<section class="chapter"><div class="chead"><div class="num">D</div><div><div class="kick">Appendix</div><h1>Number reference</h1></div></div>{nums}
<h2>Sources</h2><ul class="small"><li>Methodology report: <code>pipeline/outputs/SupeRR_Selector_Round1_HYBRID_Methodology_Report.pdf</code> and all files in <code>pipeline/outputs/</code>.</li>
<li>IPL 2027 retention and auction dates: CricTracker (\"BCCI sets November 15 as IPL 2027 retention deadline\") and Sportsdigest (\"BCCI extends IPL 2027 retention deadline\"), November 2026.</li>
<li>RR's 2025 and 2026 finishes: Cricxtasy and MyKhel.</li></ul></section>"""
