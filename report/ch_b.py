"""Chapters 8-15: value, shrinkage, composite, journey, solution B, tournament, final recipe, uncertainty."""
from rlib import *


def STAIR(role, rawlab):
    R = ROWSM[role]
    return [(lab, R[k]["mean"], R[k]["worst"], t) for lab, k, t in (("Random 10", "random", "base"), ("Most pressure balls", "volume", "base"), (rawlab, "raw", "base"),
                                                                     ("Solution A", "A", "A"), ("Solution B", "B", "B"), ("FINAL hybrid", "final", "final"))]
import pandas as _pd
_REL = _pd.read_csv(OUT / "val_reliability.csv")
RAWRHO = float(_REL[_REL.definition.str.startswith("PI") & (_REL.role == "bat") & (_REL.value_lens == "raw")].split_half_rho.iloc[0])


# =============================================================================================== 8
def ch8():
    ex = D["value_example"][-1]
    feats = ("innings, over, balls left, wickets left, score, runs needed, required rate, current rate, Elo difference, "
             "Pressure Index (capped), pace or spin, IPL / T20I, opposition is an Associate, own team is an Associate, season")
    vf = Flow(680, 200)
    vf.node("st", 6, 64, 130, 72, "Situation", "16 facts about the ball", "n")
    vf.node("e1", 180, 6, 150, 56, "Expected runs", "Poisson model", "b")
    vf.node("e2", 180, 72, 150, 56, "Chance of getting out", "classifier", "b")
    vf.node("e3", 180, 138, 150, 56, "Wicket cost", "remaining-runs model", "v")
    vf.node("act", 380, 6, 130, 56, "What happened", "runs, out or not", "n")
    vf.node("val", 550, 64, 124, 72, "Value of the ball", "runs above expected, wicket-adjusted", "s")
    for k in ("e1", "e2", "e3"):
        vf.edge("st", k).edge(k, "val", color="#c9bfd6")
    vf.edge("act", "val", "r", "t", tb=0.3)
    return chapter("8", "Measuring performance", "Valuing every ball fairly",
                   "Knowing which balls are pressure balls is half the job. Now we need a fair mark for what the batter or bowler did on each one. The mark is: how much better than an average player in exactly the same situation (program <code>s03_value.py</code>).") + f"""
{vf.svg()}
<h2>Why raw strike rate is unfair</h2>
<p>A finisher in the last two overs is expected to score at 10–12 an over. An opener in the first over of a Test-like chase is expected to score at 6. If both score at 9, the opener did well and the finisher did badly. Raw strike rate says they did the same. The fix is to compare each ball with what an <b>average</b> player would produce in that exact spot.</p>
<h2>Step 1: what would an average player do here?</h2>
<p>We trained four models, all out-of-fold (5 groups of matches, like Chapter 5), on these 16 facts about each ball: {feats}.</p>
{table(["Model", "Predicts", "Type"], [
        ["Expected batter runs", "runs off the bat on this ball", "LightGBM, Poisson objective (runs are counts)"],
        ["P(out)", "chance the striker is dismissed", "LightGBM classifier"],
        ["Expected bowler runs", "runs charged to the bowler", "LightGBM, Poisson objective"],
        ["P(bowler wicket)", "chance the bowler takes a wicket", "LightGBM classifier"]])}
{box("kid", "<p>Imagine a thousand average players, all facing this exact ball in this exact situation. On average they would score, say, 1.9 runs and 13% of them would get out. That is the \"expected\" line. A real player gets credit for beating it and blame for falling short.</p>")}
<h2>Step 2: what does a wicket cost?</h2>
<p>A wicket is not worth a fixed number of runs. Losing a wicket in the 2nd over removes a batter who might have batted for 15 overs; losing the last-but-one wicket in the 20th over costs almost nothing. We trained an <b>expected remaining runs</b> model on first innings: given balls left and wickets left, how many more runs will the team score?</p>
{box("math", eq("wicket cost (state) = ExpectedRemainingRuns(balls left, wickets left) - ExpectedRemainingRuns(balls left, wickets left - 1)"))}
{stats([("10.0", "runs: average cost of a wicket in the powerplay"), ("5.5", "runs in the middle overs"), ("2.6", "runs at the death"), ("0", "minimum: costs are never negative")])}

<h2>Step 3: the value of one ball</h2>
{box("math", eq("Batter value = (runs - expected runs)  -  wicket cost x (out - P(out))\\nBowler value = (expected runs conceded - runs conceded)  +  wicket cost x (wicket - P(wicket))") +
             f"""<p><b>Worked example, real numbers.</b> The six that won the KKR chase: {ex["s"]} facing {ex["b"]}, needing {ex["need"]} off {ex["left"]}.</p>
{table(["Piece", "Value"], [["Runs scored", "6"], ["Expected runs for an average batter here", f'{ex["E"]:.2f}'], ["Run part = 6 − 1.91", "+4.09"],
                            ["Chance an average batter gets out here", f'{ex["Pout"]:.3f}'], ["Wicket cost in this state", f'{ex["Wc"]:.2f} runs'],
                            ["Wicket part = −1.51 × (0 − 0.127)", "+0.19 (he survived a risky ball)"], ["<b>Batter value</b>", f'<b>{ex["val"]:+.2f} runs</b>'],
                            ["<b>Bowler value</b> (mirror image, own models)", f'<b>{ex["bval"]:+.2f} runs</b>']], num=(1,))}""")}
{box("why", "<p><b>Why runs and not win probability?</b> We also built a win-probability version (credit = change in win chance). It sounds perfect for \"clutch\", but it is very noisy, because almost all of the swing happens on a few balls. In tests (Chapter 11) the run-value version repeated better across matches and predicted future seasons better. We kept win probability for two narrower jobs: deciding <i>which</i> balls are pressure, and judging match-by-match consistency.</p>")}
<h2>Step 4: two sanity checks</h2>
<ul><li><b>The average should be zero.</b> If the expected models are fair, the average batter value over all balls should be about 0. It is ({__import__('pandas').read_parquet(OUT / 'deliveries_value.parquet', columns=['bat_val']).bat_val.mean():+.4f} runs per ball for batters, {__import__('pandas').read_parquet(OUT / 'deliveries_value.parquet', columns=['bowl_val']).bowl_val.mean():+.4f} for bowlers).</li>
<li><b>Opposition strength.</b> Runs against an Associate side (a team that is not one of the 12 ICC Full Members) are easier to score. Those balls count with weight 0.5 in every rating; all other balls count 1.0. Elo already reduces their leverage too.</li></ul>
{box("warn", "<p><b>The last wicket.</b> When only one wicket is left, losing it ends the innings at once. The remaining-runs model can under-price that, so we set a floor: with one wicket left, the wicket cost is never below the median wicket cost. Small rules like this matter at the death, where pressure is high.</p>")}
</section>"""


# =============================================================================================== 9
def ch9():
    def kr(lab, k):
        return [lab, f"{k:,.0f}", f"200 / (200 + {k:,.0f}) = {200 / (200 + k):.2f}"]
    rows = [kr("Batter, run part", KSH["bat"]["runs"]), kr("Batter, wicket part", KSH["bat"]["wickets"]),
            kr("Bowler, run part", KSH["bowl"]["runs"]), kr("Bowler, wicket part", KSH["bowl"]["wickets"])]
    return chapter("9", "Small samples", "Small samples: shrinkage",
                   "Most players have only a few hundred pressure balls. On samples that small, luck can look like skill. Shrinkage is the standard cure, and it is the single most important idea in this project.") + f"""
{box("kid", "<p><b>The restaurant problem.</b> Restaurant A has 2 reviews, both 5 stars. Restaurant B has 800 reviews averaging 4.6. Which is safer? Most people pick B. Two reviews could be the owner's friends. So in your head you pull A's 5.0 down toward the typical restaurant, maybe to 4.3, because you do not have much evidence yet. As A gets more reviews, you trust its own average more. That pulling-down is shrinkage.</p>")}
<h2>The formula</h2>
{box("math", eq("shrunk value = player's average x  n / (n + k)\\n\\nn = the player's number of balls (weighted)\\nk = sigma2 / tau2\\nsigma2 = how noisy a single ball is (within-player variance)\\ntau2   = how much players REALLY differ from each other (between-player variance)") +
             "<p>Values are measured relative to the league average (which is 0 by construction), so shrinking toward 0 means shrinking toward an average player. A player with n = k balls keeps exactly half of his raw advantage. A player with many more balls than k keeps almost all of it.</p>")}
<h3>Estimating k from the data (the DerSimonian–Laird method)</h3>
<p>We do not guess k. We measure how spread out the players' averages are, and subtract the spread that pure luck would produce. Whatever spread is left is real skill (tau²).</p>
{box("math", eq("Q    = sum over players of  n_i x (mean_i - overall mean)^2 / sigma2\\ntau2 = max( (Q - (number of players - 1)) x sigma2 / (sum n_i - sum n_i^2 / sum n_i) ,  tiny )") +
             "<p>If players differed only by luck, Q would be about equal to (number of players − 1). Every bit of Q above that is real difference. This is the same method medical researchers use to combine results from many small studies.</p>")}
<h2>Runs and wickets are shrunk separately</h2>
<p>Here is the key discovery from our second version (Chapter 11). A wicket is rare and worth 5–10 runs, so one dismissal more or less changes a player's average a lot. The run part is much steadier. Shrinking them together let the wicket noise swamp the run signal. Shrinking them separately lets each keep the right amount of trust.</p>
{table(["Component (pressure balls)", "k measured from the data (balls)", "How much a 200-ball player keeps of his raw advantage"], rows, num=(1,))}
<p>A batter with 200 pressure balls keeps {200 / (200 + KSH['bat']['runs']):.0%} of his run advantage but only {200 / (200 + KSH['bat']['wickets']):.0%} of his wicket advantage. That matches common sense: 200 balls tells you a fair amount about how fast someone scores, and very little about how often they get out.</p>
{fig(panel("Shrinkage in action (batters)", "grey = raw value per 100 pressure balls; pink = shrunk value we use", ch.shrink(D["shrink"], 900, 420), 900, 420),
         "<b>Figure 9.1</b> Players with few balls (left) are pulled hard toward the pool average; players with many balls (right) barely move. The labelled players moved the most.")}
<h2>Two ways to shrink, and why we average them</h2>
<ul><li><b>Direct:</b> shrink what he did under pressure toward the league average. Most faithful to the pressure sample, but noisy.</li>
<li><b>Hierarchical:</b> start from his shrunk <i>overall</i> level (lots of balls, very stable), then add his pressure <i>difference</i>, shrunk hard because it is noisy. Stable, but it leans toward \"good players are good under pressure\".</li></ul>
{box("math", eq("hierarchical = shrunk overall level + shrunk (pressure average - overall average)\\nrating       = 0.5 x direct + 0.5 x hierarchical") +
             "<p>The pressure balls are part of all balls, so the difference is measured with an effective sample of 1 / (1/n<sub>pressure</sub> − 1/n<sub>all</sub>) balls.</p>")}
{box("why", "<p>Tested on split halves and on 2022–24 predicting 2025–26: the 50/50 blend was the most repeatable and most predictive for batters and close to the best for bowlers (Chapter 11). Neither pure version won on both.</p>")}
<h2>Minimum sample rules (eligibility)</h2>
<p>Shrinkage handles noise, but a ranking of \"most reliable\" should not include someone with 60 balls. To be eligible a player needs <b>at least 150 pressure balls</b>, <b>at least 12 matches</b> with pressure involvement, and <b>at least 150 usual balls</b> (so his usual level can be measured). That leaves <b>120 batters and 120 bowlers</b>. This rule later beat Solution B's rule (top quarter of players by pressure balls) in the tournament.</p>
</section>"""


# =============================================================================================== 10
def ch10():
    w = json.loads((OUT / "weights.json").read_text())
    return chapter("10", "Measuring performance", "Usual level, consistency and the composite",
                   "A rating of pressure performance is the core. The brief also asks how players compare with their usual level, and \"reliable\" suggests doing it match after match. This chapter adds those two pieces and explains how they are weighted.") + f"""
<h2>Usual level and uplift</h2>
<p>Every player gets the same rating on his <b>usual</b> balls (the bottom 50% by Pressure Index). Then:</p>
{eq("uplift = pressure level - usual level        (both measured the same way, per ball)")}
<p>A positive uplift means he gets better when it matters; a negative uplift means he drops off. We report both levels side by side for every player, because that directly answers the brief's comparison.</p>
{box("warn", f"<p>Uplift turned out to be the <b>least</b> repeatable thing we measured (split-half ρ between about {min(t['uplift_rho'] for t in D['threshold']):+.2f} and {max(t['uplift_rho'] for t in D['threshold']):+.2f} depending on the cut-off). In plain words: \"rises to the occasion\" is mostly not a stable trait in this data. Pressure performance behaves mostly like normal skill. So uplift gets a deliberately small weight. It is honest to say so, and it is one of the most interesting findings.</p>")}
<h2>Consistency: does he deliver match after match?</h2>
<p>For each player and match we add up his pressure value, this time in a win-probability currency (credit per ball divided by the ball's leverage, then centred so an average player scores 0 in every innings × phase × pressure-level cell). Then:</p>
{box("math", eq("Batters, impact rate  = (matches with a top-25% contribution + 1) / (matches + 4)\\nBowlers, no-fail rate = 1 - (matches with a bottom-25% contribution + 1) / (matches + 4)") +
             "<p>The \"+1 and +4\" is a small built-in shrinkage: a player with 2 matches and 2 big contributions gets (2+1)/(2+4) = 0.50, not 100%. The top/bottom 25% lines are the league's quartiles of all player-match contributions.</p>")}
{box("why", "<p>We tried three versions of consistency (share of positive matches, impact rate, no-failure rate) and kept the one that repeated best for each role. For batters it was producing big contributions; for bowlers it was rarely being the reason a pressure moment was lost. That matches how the roles work: a batter wins a match with one big innings; a bowler loses one with a bad over.</p>")}
<h2>Putting the three pieces together (Solution A's composite)</h2>
<p>Each piece is turned into a <b>z-score</b> so they are on the same scale:</p>
{eq("z(x) = (x - average of the eligible pool) / standard deviation of the pool")}
<p>A z-score of +2 means \"two standard deviations above the typical eligible player\". Then the pieces are weighted <b>in proportion to how repeatable each one is</b> (its split-half reliability), with uplift given a floor of 0.15 so the brief's comparison always counts:</p>
{table(["Role", "Pressure rating", "Uplift (vs usual)", "Consistency"], [["Batters", f'{w["bat"][0]:.2f}', f'{w["bat"][1]:.2f}', f'{w["bat"][2]:.2f}'], ["Bowlers", f'{w["bowl"][0]:.2f}', f'{w["bowl"][1]:.2f}', f'{w["bowl"][2]:.2f}']], num=(1, 2, 3))}
{box("kid", "<p>If three friends give you directions and one of them is usually right, one is sometimes right and one is often confused, you listen to them in that order. Weighting by reliability does the same: the more repeatable a measure, the louder its voice.</p>")}
<h2>The \"delivered\" gate</h2>
<p>One more rule: a player whose <i>observed</i> pressure value is below the league average cannot be ranked above a player who delivered. Without the gate, a player with average pressure numbers but a great usual level and consistency could sneak into a \"best under pressure\" list. With it, a top ranking must be earned under pressure. In the final method the gate is used for bowlers; {int((__import__('pandas').read_csv(OUT / 'hyb_ratings_bowl.csv').hp_raw > 0).sum())} of the {len(__import__('pandas').read_csv(OUT / 'hyb_ratings_bowl.csv'))} eligible bowlers pass it.</p>
</section>"""


# =============================================================================================== 11
def ch11():
    steps = [("0", "Simplest ideas", "Rank by raw pressure strike rate / economy, or by most pressure balls", "On their worst cell, volume and raw rates are no safer than random; finishers dominate", "drop"),
             ("1", "Define pressure", "Rules vs hand-weighted stress vs model leverage", "Leverage packs 2× its share of decisive swing; rules ~1.2×", "keep"),
             ("2", "A v1", "Runs above expected, one joint shrinkage, top 25%", "Reliability 0.01 / 0.07: one dismissal swamps the signal", "drop"),
             ("3", "A v2", "Shrink run and wicket parts separately", "Small gain (0.04 / 0.05)", "step"),
             ("4", "A v3", "Switch to win-probability lens (WPA ÷ leverage)", "Looked great (0.31 / 0.23) but measured match context, not skill", "drop"),
             ("5", "A v4", "Centre that lens within innings × phase × pressure cells", "Honest but modest (0.11 / 0.13)", "step"),
             ("6", "A v5", "Run value + direct shrinkage", "Most faithful to the pressure sample, least stable", "step"),
             ("7", "A v6", "Blend direct + hierarchical; reliability-weighted composite", "0.22 / 0.17; 2022–24 predicts 2025–26", "keep"),
             ("8", "Solution B", "Independent build: pressure SR, economy + WPA, chosen by prediction", "Strong on strike rate; ignores dismissals and context", "keep"),
             ("9", "A vs B", "Same unseen splits, 8 targets", "No overall winner: each found something", "step"),
             ("10", "Hybrid tournament", "79 candidates mixing A and B, 3 pools, gates, extra terms", "Beats both parents on worst case and/or mean", "keep"),
             ("11", "Brief constraint", "Only methods that score pressure vs usual may win", "Bowler score gains the uplift term", "keep")]
    col = {"keep": GOOD, "drop": BAD, "step": JER}
    lab = {"keep": "KEPT", "drop": "DROPPED", "step": "STEP"}
    tb = table(["#", "Version", "What changed", "What the data said", ""], [[a, f"<b>{b_}</b>", c, d, chip(lab[v], col[v])] for a, b_, c, d, v in steps])
    m = __import__("pandas").read_csv(OUT / "val_models.csv")
    mt = table(["Rating model", "Role", "Split-half ρ (rating)", "2022–24 → 2025–26 ρ"], [[r.model, r.role, f"{r.split_half_rho:.2f}", f"{r.predicts_2025_26_pressure:.2f}"] for r in m.itertuples() if r.score == "pressure rating only"], num=(2, 3))
    sh = Flow(680, 170)
    sh.node("all", 6, 55, 120, 60, "837 matches", "", "d")
    sh.node("h1", 170, 10, 140, 60, "Half 1", "rate every player", "b")
    sh.node("h2", 170, 100, 140, 60, "Half 2", "rate every player again", "p")
    sh.node("cmp", 360, 55, 150, 60, "Compare the two lists", "Spearman rank correlation ρ", "v")
    sh.node("rep", 550, 55, 124, 60, "Repeat 16×", "average ρ", "g")
    sh.edge("all", "h1").edge("all", "h2").edge("h1", "cmp").edge("h2", "cmp").edge("cmp", "rep")
    return chapter("11", "Iterating", "The refinement journey: 12 steps",
                   "The final method was not designed in one go. We started with the simplest possible ranking and changed one thing at a time. Every version had to prove itself on two tests. This chapter is the honest history, including what we threw away.") + f"""
<h2>The two tests every version had to pass</h2>
<h3>Test 1: split-half reliability (does it repeat?)</h3>
{sh.svg()}
<p>Split the matches into two random halves. Rate every player on each half separately. If the rating measures something real about the player, the two lists should agree. We measure agreement with the <b>Spearman rank correlation ρ</b>: +1 means the same order, 0 means no relation. We average over 16 random splits.</p>
{box("kid", "<p>If a bathroom scale says 60 kg, then 72 kg, then 55 kg in one minute, it is broken, however nice it looks. Reliability asks: does our \"scale\" give a player roughly the same reading on two different sets of matches?</p>")}
<h3>Test 2: does the past predict the future?</h3>
<p>Rate players on 2022–24 only, then on 2025–26 only, and correlate the two for players with enough balls in both. A rating that predicts a later period is measuring something that lasts.</p>
{box("warn", f"<p><b>High reliability is not enough on its own.</b> Raw pressure strike rate repeats very well (ρ ≈ {RAWRHO:.2f} for batters) because it mostly measures a player's <i>role</i>: openers and finishers always score faster than anchors. A measure can be very repeatable and still not measure pressure skill. That is why we also need context adjustment and the unseen-match tournament.</p>")}
<h2>The 12 steps</h2>
{tb}
<p class="small m">Reliability pairs are split-half ρ for batters / bowlers.</p>
{box("mist", "<p><b>The version that looked too good (A v3).</b> Switching to the win-probability lens jumped reliability to 0.31 / 0.23, by far our best. Before celebrating we checked <i>why</i>. The average value was different in different contexts (innings, phase, pressure level), because the win-probability model drifts between them. So the rating was partly learning \"which situations a player usually plays in\" rather than \"how well he plays\". A rating that repeats because of context is not measuring skill. We dropped it, centred the lens within innings × phase × pressure cells (v4), and reliability fell to an honest 0.11 / 0.13. Dropping your best-looking number is painful, and it is the most important decision in this project.</p>")}
<h2>Choosing the rating model (A v6)</h2>
{mt}
<p>The hierarchical model repeats best for bowlers but predicts batters' future less well than the blend; the direct model is noisiest. The 50/50 blend was the best balance, so it became the rating inside Solution A.</p>
{fig(f'<div class="grid2">{panel("Batters: every step on unseen matches", "filled = average gain; outline = worst of 16 cells", ch.staircase(STAIR("bat", "Raw pressure SR"), 330, 280, "m", "w", PINK), 330, 280)}'
     f'{panel("Bowlers: every step on unseen matches", "filled = average gain; outline = worst of 16 cells", ch.staircase(STAIR("bowl", "Raw pressure economy"), 330, 280, "m", "w", BLUE), 330, 280)}</div>',
     "<b>Figure 11.1</b> The whole journey on one yardstick (explained in Chapter 13). Each step up is a measured improvement on matches the method never saw.")}
</section>"""


# =============================================================================================== 12
def ch12():
    return chapter("12", "A second opinion", "A second, independent solution",
                   "One team building one method can talk itself into anything. So a second solution (Solution B) was built separately, with different instincts, and the two were made to compete on the same unseen matches.") + f"""
<h2>Solution B's recipe</h2>
{table(["Piece", "Batters", "Bowlers"], [
        ["Pressure", "Within-innings leverage percentile ≥ 75 and ≥ 85", "Within-innings leverage percentile ≥ 70"],
        ["Measure", "Strike rate on those balls (two cut-offs, each z-scored, then added)", "Minus runs per ball, and win probability added per ball"],
        ["Small samples", "No shrinkage", "Each shrunk toward the pool average with strength k = 500 balls"],
        ["Pool", "Top 25% of players by pressure balls", "Top 25% of players by pressure balls"],
        ["How it was chosen", "Purely by held-out prediction, best worst case", "Purely by held-out prediction, best worst case"]])}
{box("math", eq("Batter B score = z(strike rate at pct >= 75) + z(strike rate at pct >= 85)\\nBowler B score = z(shrunk minus runs per ball) + z(shrunk WPA per ball)\\nshrunk v = pool mean + n / (n + 500) x (v - pool mean)"))}
<h2>The fair fight</h2>
<p>Both solutions ranked players on the same training matches and were scored on the same unseen matches against eight targets (four measures × two pressure definitions, so neither solution's own definition was favoured).</p>
{table(["Result on unseen matches", "Batters", "Bowlers"], [
        ["Strike-rate targets", "B better: A − B = −0.19 pool SD", "within one standard error"],
        ["Dismissal / wicket targets", "A better: A − B = +0.20 pool SD", "within one standard error"],
        ["Overall", "no winner", "no winner"]])}
{box("kid", "<p>Two coaches pick a team. One coach picks batters who score fast; the other picks batters who do not get out. Over a season, the first coach's picks win the strike-rate table and the second coach's picks win the \"fewest dismissals\" table. Neither coach is wrong; each has noticed something real. The smart move is to combine them, and to decide <i>how much</i> of each by testing, not by arguing.</p>")}
<h2>What each solution had found</h2>
<ul><li><b>A</b> knew about context (an opener and a finisher are compared fairly), wickets (a dismissal has a price) and small samples (shrinkage). It was safer, especially on dismissal avoidance.</li>
<li><b>B</b> rewarded raw scoring speed on the highest-leverage balls, which is exactly what wins tight T20 finishes. Its bowler recipe (economy + WPA, shrunk with k = 500) predicted unseen matches very well.</li></ul>
{box("why", "<p>Instead of choosing one parent, we turned the disagreement into a search: build many mixtures of A and B and let unseen matches choose. That is Chapter 13, the heart of the final method.</p>")}
</section>"""


# =============================================================================================== 13
def ch13():
    S = __import__("pandas").read_csv(OUT / "hyb_selection.csv", index_col=0)
    def pick(role):
        s_ = S[S.role == role]
        unc = s_[s_.best_unconstrained].index[0]
        near = [i for i in s_[s_.has_usual].sort_values("worst_cell", ascending=False).index if i != CHOSEN[role]][:2]
        return list(dict.fromkeys(["A: solution A (shipped)", "B: solution B recipe", CHOSEN[role], *near, unc, "random"]))
    keep, keepw = pick("bat"), pick("bowl")
    def rows(role, names):
        out = []
        for n_ in names:
            r = S[(S.role == role)].loc[n_]
            star = " ★" if r.chosen else ""
            out.append([f"<b>{n_}{star}</b>" if r.chosen else n_, f"{r.worst_cell:+.3f}", f"{r.mean_cell:.3f}", f"{r.random_mean:.3f}", f"{r.future_mean:.3f}", "yes" if r.has_usual else "no"])
        return out
    hd = ["Candidate", "Worst cell", "Mean", "Random splits", "Future splits", "Has usual-level term"]
    def verdict(role):
        R = ROWSM[role]; f = R["final"]; a, b = R["A"], R["B"]
        w = (f"the hybrid has the best worst cell of the three ({f['worst']:+.3f}, against {a['worst']:+.3f} for A and {b['worst']:+.3f} for B)" if f["worst"] >= max(a["worst"], b["worst"])
             else f"the hybrid's worst cell is {f['worst']:+.3f} (A {a['worst']:+.3f}, B {b['worst']:+.3f})")
        m = (f"and the best mean ({f['mean']:.3f}, against {a['mean']:.3f} and {b['mean']:.3f})" if f["mean"] >= max(a["mean"], b["mean"])
             else f"with a mean of {f['mean']:.3f}, between A ({a['mean']:.3f}) and B ({b['mean']:.3f})")
        return f"{w}, {m}."
    tf = Flow(680, 250)
    tf.node("m", 6, 90, 110, 70, "837 matches", "", "d")
    tf.node("tr", 150, 20, 140, 70, "Training matches", "every candidate ranks players", "b")
    tf.node("te", 150, 160, 140, 70, "Unseen matches", "measure the picked players", "p")
    tf.node("top", 330, 20, 140, 70, "Each candidate's top 10", "79 candidates per role", "v")
    tf.node("g", 330, 160, 140, 70, "Gain", "how far above the pool the 10 performed", "g")
    tf.node("c", 510, 90, 164, 70, "16 cells", "8 targets × 2 split schemes; repeat 36 splits", "s")
    tf.edge("m", "tr").edge("m", "te").edge("tr", "top").edge("top", "g", "b", "t").edge("te", "g").edge("g", "c")
    return chapter("13", "The core", "The held-out tournament",
                   "This is how the final method was chosen. Every candidate method ranks players using some matches. Its top 10 is then judged on matches it never saw. The winner is picked by a rule written before the results were known (program <code>s07_hybrid_select.py</code>).") + f"""
{tf.svg()}
<h2>Step 1: the splits</h2>
<ul><li><b>30 random half-splits.</b> Pick half of the 837 matches at random for training; the other half is unseen.</li>
<li><b>6 past → future splits.</b> Train on the first 50%, 57%, 64%, 71%, 78% or 85% of matches by date; test on the rest. This is the realistic case: an auction uses the past to bet on the future.</li></ul>
<p>When a candidate trains on a fraction of the matches, the minimum sample rules are scaled down by the same fraction, so it is not starved of players.</p>
<h2>Step 2: the eight targets</h2>
<p>On the unseen matches, for every player with at least 30 pressure balls there, we measure:</p>
{table(["Batters", "Bowlers"], [["strike rate", "economy (lower is better)"], ["runs above expected", "runs saved vs expected"], ["win probability added per ball", "win probability added per ball"], ["dismissal avoidance", "wickets per ball"]])}
<p>Each target is measured under <b>both</b> pressure definitions (A's top 30% Pressure Index and B's within-innings percentile ≥ 80). That makes 8 targets, and with two split schemes, <b>16 cells</b>.</p>
<h2>Step 3: the gain</h2>
{box("math", eq("gain = (average target of the candidate's top 10  -  average of the whole pool) / standard deviation of the pool") +
             "<p>A gain of +0.3 means the ten players picked from the training matches went on to perform 0.3 standard deviations better than a typical pool player in matches the method never saw. A random pick of ten scores about 0.</p>")}
<h2>Step 4: the candidates</h2>
<p>79 candidate methods per role, plus a random picker for reference. They mix A and B in every sensible way:</p>
<ul><li><b>Blend weights</b> wB = 0.33, 0.5, 0.67, 0.8, 1.0 between A's rating (or A's full composite) and B's score.</li>
<li><b>Three pools</b>: A's eligibility rule (poolA), B's top-quartile rule (poolB), or either (poolA+B).</li>
<li><b>Optional extras</b>: the uplift term (+U, weight 0.1, 0.15 or 0.2), uplift + consistency (+U+C), the delivered gate (gated).</li>
<li><b>Baselines</b>: volume (most pressure balls), raw pressure strike rate / economy, pure A, pure B.</li></ul>
{box("kid", "<p>Name decoder: <code>H wB=0.5 +U+C | poolA</code> = \"hybrid of A's rating and B's score with 50% on B, plus uplift and consistency terms, players chosen by A's eligibility rule\". <code>H wB=0.8 gated +U0.1 | poolA</code> = \"hybrid of A's rating and B's score with 80% on B, with the delivered gate, plus an uplift term with weight 0.1, A's pool\".</p>")}
<h2>Step 5: the rule (fixed in advance)</h2>
<ol><li>Only candidates whose score includes the pressure-vs-usual comparison may be chosen (the brief asks for it).</li>
<li>Take the candidate with the <b>best worst cell</b> (the highest minimum over the 16 cells).</li>
<li>Among candidates within 0.03 of that, take the <b>best average</b>.</li></ol>
{box("why", "<p><b>Why the worst case first?</b> An auction bet goes wrong in the cases you did not plan for. A method that is excellent on strike rate but picks players who get out all the time is a risky buy. Maximising the worst case (\"maximin\") picks the method that never fails badly on any target, and then the 0.03 tolerance lets the average break near-ties. A tiny difference in the worst cell is noise, so we do not let it decide alone.</p>")}
<h2>The results</h2>
<h3>Batters</h3>{table(hd, rows("bat", keep), num=(1, 2, 3, 4))}
<h3>Bowlers</h3>{table(hd, rows("bowl", keepw), num=(1, 2, 3, 4))}
<p class="small m">★ = chosen by the rule. Gains are in pool standard deviations on unseen matches.</p>
<ul><li><b>Batters</b>: {verdict("bat")}</li>
<li><b>Bowlers</b>: {verdict("bowl")}</li>
<li><b>Cost of the brief's rule</b>: the best method <i>without</i> an uplift term scores {ROWSM["bat"]["unconstrained"]["worst"]:+.3f} / {ROWSM["bat"]["unconstrained"]["mean"]:.3f} for batters and {ROWSM["bowl"]["unconstrained"]["worst"]:+.3f} / {ROWSM["bowl"]["unconstrained"]["mean"]:.3f} for bowlers, against {ROWSM["bat"]["final"]["worst"]:+.3f} / {ROWSM["bat"]["final"]["mean"]:.3f} and {ROWSM["bowl"]["final"]["worst"]:+.3f} / {ROWSM["bowl"]["final"]["mean"]:.3f} for the chosen ones. We show this so nobody thinks the requirement was free, or that it was costly when it was not.</li></ul>
<div class="grid2">{panel("Batters: all candidates", "x = worst cell, y = mean gain", ch.tournament(D["tournament"], 330, 280, "bat", PINK), 330, 280)}{panel("Bowlers: all candidates", "x = worst cell, y = mean gain", ch.tournament(D["tournament"], 330, 280, "bowl", BLUE), 330, 280)}</div>
<p class="small m"><b>Figure 13.1</b> Every candidate as a dot. Up = better on average; right = safer in the worst case. The chosen hybrid sits in the top-right group.</p>
</section>"""


# =============================================================================================== 14
def _parse(name):
    import re
    wb = float(re.search(r"wB=([0-9.]+)", name).group(1))
    mu = re.search(r"\+U([0-9.]+)", name)
    return {"wb": wb, "wa": 1 - wb, "uc": "+U+C" in name, "gate": "gated" in name,
            "wu": 0.1 if "+U+C" in name else (float(mu.group(1)) if mu else 0.0), "composite": name.startswith("HA(composite)")}


def _recipe_flow(role):
    P = _parse(CHOSEN[role]); bat = role == "bat"
    f = Flow(680, 300)
    f.node("f", 6, 115, 130, 70, f"Final {'batter' if bat else 'bowler'} score", "+100 if delivered" if P["gate"] else "z-scored, higher = better", "s" if bat else "j")
    core = 0.8 if P["uc"] else 1 - P["wu"]
    f.node("h", 196, 30, 160, 76, f"Rating blend × {core:.2f}", f"{P['wa']:.2f} × z(A rating) + {P['wb']:.2f} × z(B), re-z-scored", "p")
    leaves = ([("l1", f"A pressure rating × {P['wa']:.2f}", "runs above expected, shrunk"), ("l2", "SR at leverage pct ≥ 75", "z-scored, part of B"), ("l3", "SR at leverage pct ≥ 85", "z-scored, part of B")] if bat else
              [("l1", f"A pressure rating × {P['wa']:.2f}", "runs saved vs expected, shrunk"), ("l2", "B economy", "runs per ball at pct ≥ 70, shrunk k = 500"), ("l3", "B win prob. added", "per ball at pct ≥ 70, shrunk k = 500")])
    for i, (k, t1, t2) in enumerate(leaves):
        f.node(k, 420, 4 + i * 62, 254, 54, t1, t2, "n")
        f.edge(k, "h", "l", "r", tb=0.2 + i * 0.3)
    f.edge("h", "f", "l", "r", tb=0.25, color=PINK)
    y = 130
    if P["wu"]:
        f.node("u", 196, y, 160, 56, f"Uplift × {P['wu']:.2f}", "pressure − usual level", "g"); f.edge("u", "f", "l", "r", tb=0.55, color=GOOD); y += 66
    if P["uc"]:
        f.node("c", 196, y, 160, 56, "Consistency × 0.10", "impact rate", "y"); f.edge("c", "f", "l", "r", tb=0.85, color=WARN)
    if P["gate"]:
        f.node("gate", 420, 206, 254, 70, "Delivered gate", "observed pressure value must be above league average to rank above those who delivered", "y")
        f.edge("gate", "f", "b", "b", color=WARN, dash=True, via=[(547, 292), (71, 292)])
    return f


def _worked(role):
    """Every step of the #1 player's score, recomputed from the rating table (matches the pipeline to 1e-12)."""
    import pandas as pd
    t = pd.read_csv(OUT / f"hyb_ratings_{role}.csv", index_col=0)
    zf = lambda v: (v - v.mean()) / v.std(ddof=0)
    P = _parse(CHOSEN[role]); i = t.index[0]; p = t.loc[i]; rows = []
    zA = zf(t.hp_val)
    if role == "bat":
        z75, z85 = zf(t.sr75), zf(t.sr85); Bs = z75 + z85; zB = zf(Bs)
        rows += [["A pressure rating (runs above expected per ball)", f"{p.hp_val:+.3f}", f"{zA[i]:+.2f}"],
                 ["SR at pct ≥ 75", f"{p.sr75 * 100:.1f}", f"{z75[i]:+.2f}"], ["SR at pct ≥ 85", f"{p.sr85 * 100:.1f}", f"{z85[i]:+.2f}"],
                 [f"B ensemble = {z75[i]:.2f} + {z85[i]:.2f}", f"{Bs[i]:.2f}", f"{zB[i]:+.2f}"]]
        note = (f"<p>The pool average pressure strike rate at pct ≥ 75 is {t.sr75.mean() * 100:.1f} with a standard deviation of {t.sr75.std(ddof=0) * 100:.1f}, "
                f"so {p.player.split()[0]}'s {p.sr75 * 100:.1f} is ({p.sr75 * 100:.1f} − {t.sr75.mean() * 100:.1f}) / {t.sr75.std(ddof=0) * 100:.1f} = {z75[i]:.1f} standard deviations above it.</p>")
    else:
        n = t.n; sh = lambda v: v.mean() + n / (n + 500) * (v - v.mean())
        z1, z2 = zf(sh(t.neg_rpb)), zf(sh(t.wpa)); Bs = z1 + z2; zB = zf(Bs)
        rows += [["A pressure rating (runs saved vs expected per ball)", f"{p.hp_val:+.3f}", f"{zA[i]:+.2f}"],
                 [f"Runs per ball at pct ≥ 70 ({p.n:.0f} balls)", f"{-p.neg_rpb:.2f} ({-p.neg_rpb * 6:.1f} an over)", f"{z1[i]:+.2f} after shrinkage"],
                 ["WPA per ball at pct ≥ 70", f"{p.wpa:+.3f}", f"{z2[i]:+.2f} after shrinkage"], [f"B score = {z1[i]:.2f} + {z2[i]:.2f}", f"{Bs[i]:.2f}", f"{zB[i]:+.2f}"]]
        note = ""
    base = P["wa"] * zA + P["wb"] * zB; zb = zf(base)
    rows.append([f"Blend = {P['wa']:.2f}×{zA[i]:.2f} + {P['wb']:.2f}×{zB[i]:.2f}", f"{base[i]:.2f}", f"{zb[i]:+.2f}"])
    parts = []
    if P["uc"]:
        zU, zC = zf(t.uplift), zf(t.consistency.fillna(t.consistency.median()))
        rows += [["Uplift (pressure − usual)", f"{p.uplift:+.3f}", f"{zU[i]:+.2f}"], ["Consistency (impact rate)", f"{p.consistency:.3f}", f"{zC[i]:+.2f}"]]
        final = 0.8 * zb[i] + 0.1 * zU[i] + 0.1 * zC[i]; expr = f"0.8×{zb[i]:.2f} + 0.1×{zU[i]:.2f} + 0.1×{zC[i]:.2f}"
    elif P["wu"]:
        zU = zf(t.uplift.fillna(0))
        rows.append(["Uplift (pressure − usual)", f"{p.uplift:+.3f}", f"{zU[i]:+.2f}"])
        final = (1 - P["wu"]) * zb[i] + P["wu"] * zU[i]; expr = f"{1 - P['wu']:.2f}×{zb[i]:.2f} + {P['wu']:.2f}×{zU[i]:.2f}"
    else:
        final = base[i]; expr = f"{base[i]:.2f}"
    if P["gate"]:
        rows.append([f"Delivered? (observed value {p.hp_raw:+.3f} > 0)", "yes" if p.hp_raw > 0 else "no", "+100" if p.hp_raw > 0 else "+0"])
        final += 100 * (p.hp_raw > 0); expr += " + 100"
    assert abs(final - p.score) < 1e-6, (role, final, p.score)
    rows.append([f"<b>Final = {expr}</b>", "", f"<b>{p.score:.2f} (rank 1)</b>"])
    return p.player, rows, note, len(t)


def ch14():
    rb, rw = _recipe_flow("bat"), _recipe_flow("bowl")
    nb, rows_b, note_b, n_bat = _worked("bat")
    nw, rows_w, _, n_bowl = _worked("bowl")
    db, dw = __import__("recipes").describe(CHOSEN["bat"], "bat"), __import__("recipes").describe(CHOSEN["bowl"], "bowl")
    return chapter("14", "The core", "The final recipe, step by step",
                   "Here is the winning method written out in full, with every number of the calculation for the #1 batter and the #1 bowler. Anyone can check these against the files in the repository.") + f"""
<h2>Batters</h2>
{fig(rb.svg(), "<b>Figure 14.1</b> The batter score. Every number in the tree was chosen by the tournament or by reliability, not by hand.")}
{box("math", eq(f"B ensemble   = z(SR at pct >= 75) + z(SR at pct >= 85)\nFinal score  = {db}        (z over the {n_bat} eligible batters)") + table([nb, "Raw value", "z-score in pool"], rows_b, num=(1, 2)) + note_b)}
<h2>Bowlers</h2>
{fig(rw.svg(), "<b>Figure 14.2</b> The bowler score. The +100 from the gate simply puts every bowler who delivered above every bowler who did not; within each group the score decides.")}
{box("math", eq(f"B score   = z(shrunk minus runs per ball) + z(shrunk WPA per ball)          at pct >= 70, k = 500\nFinal     = {dw}") + table([nw, "Raw value", "z-score in pool"], rows_w, num=(1, 2)))}
<h2>The whole calculation as a checklist</h2>
<ol><li>Rebuild the state before every ball (Chapter 3).</li><li>Score every ball's win probability and leverage, out-of-fold (Chapters 5–6).</li>
<li>Flag pressure balls: top 30% Pressure Index; usual balls: bottom 50%. Also compute the within-innings percentile (Chapter 6).</li>
<li>Value every ball against an average player, with a wicket cost (Chapter 8).</li>
<li>Shrink run and wicket parts separately; blend direct and hierarchical (Chapter 9).</li>
<li>Compute uplift and consistency (Chapter 10).</li>
<li>Compute B's components (Chapter 12).</li><li>Apply the eligibility rule ({n_bat} batters and {n_bowl} bowlers qualify).</li>
<li>Combine with the tournament-chosen recipe above; sort; the top 10 are the answer.</li>
<li>Check how sure we are (Chapter 15).</li></ol>
</section>"""


# =============================================================================================== 15
def ch15():
    TB, TW = D["top"]["bat"], D["top"]["bowl"]
    def firm(rows):
        k = 0
        while k < len(rows) and rows[k]["p_top10"] >= 50:
            k += 1
        return k
    FIRM = {"bat": firm(TB), "bowl": firm(TW)}
    FULL = [r["player"] for r in TB + TW if r["specs"] == r["n_specs"]]
    KEEP = {"bat": sum(r["p_top10"] for r in TB) / 100, "bowl": sum(r["p_top10"] for r in TW) / 100}
    return chapter("15", "Uncertainty", "How sure are we?",
                   "A rank on its own hides how close the race was. We re-ran the whole final method hundreds of times on reshuffled data and under different reasonable settings, and counted how often each player stayed in the top 10 (program <code>s08_hybrid_final.py</code>).") + f"""
<h2>The bootstrap: replaying history with different luck</h2>
{box("kid", "<p>Imagine the five seasons were played again, with the same players but slightly different luck: some matches happen twice, some do not happen at all. Would the same ten players come out on top? We cannot replay cricket, but we can replay the data: draw the matches again at random, rebuild the ranking, and repeat 300 times.</p>")}
{box("math", eq("For each of 300 resamples:\\n   every match gets a random weight from a Poisson(1) distribution (0, 1, 2, 3 ... ; average 1)\\n   re-run the final scoring with those weights and record every player's rank\\nP(top 10) = share of the 300 resamples in which the player is in the top 10") +
             "<p>We resample whole <b>matches</b>, not single balls, because balls inside a match are linked (same pitch, same opponents, same game situation). Resampling balls would make us look more certain than we are.</p>")}
<div class="grid2">{panel("Batters", "P(top 10) across 300 resamples · right: specs agreeing", ch.ptop_bars(TB, 330, 330, PINK), 330, 330)}{panel("Bowlers", "P(top 10) across 300 resamples · right: specs agreeing", ch.ptop_bars(TW, 330, 330, BLUE), 330, 330)}</div>
<p class="small m"><b>Figure 15.1</b> {TB[0]["player"]} stays in the top 10 in {TB[0]["p_top10"]}% of resamples; {TW[0]["player"]} in {TW[0]["p_top10"]}%. Ranks 7–10 sit in a crowded band.</p>
<h2>Specification checks: would a reasonable alternative agree?</h2>
<p>We also re-ranked under alternative but reasonable choices and counted how many put the player in the top 10:</p>
{table(["Check", "Batters", "Bowlers"], [
        ["Other near-best methods from the tournament (worst cell within 0.05 of the best)", f"{NEAR['bat']} methods", f"{NEAR['bowl']} methods"],
        ["IPL balls only / T20I balls only", "2", "2"], ["Excluding Associate opposition", "1", "1"], ["Chases only / first innings only", "2", "2"],
        ["Pressure = top 35% / top 25% instead of 30%", "2", "2"], ["No opposition down-weighting", "1", "1"], ["<b>Total specifications</b>", f"<b>{TB[0]['n_specs']}</b>", f"<b>{TW[0]['n_specs']}</b>"]], num=(1, 2))}
<p>The totals differ only because a different number of methods finished close to the best in each role\'s tournament. The two counts are not comparable across roles; read them as \"out of {TB[0]["n_specs"]}\" and \"out of {TW[0]["n_specs"]}\".</p>
<h2>How to read the uncertainty</h2>
<ul><li><b>Batters 1–{FIRM["bat"]} and bowlers 1–{FIRM["bowl"]}</b> stay in the top 10 in more than half of all resamples. Top 10 in every specification: {", ".join(FULL)}.</li>
<li><b>Ranks 7–10</b> are close calls. The next 5–10 players are near them, and small changes move them in or out.</li>
<li><b>On average a resample keeps about {KEEP["bat"]:.0f} of the 10 batters and {KEEP["bowl"]:.0f} of the 10 bowlers.</b> That is a limit of five seasons of data, not of one method. We say it plainly instead of pretending the list is exact.</li></ul>
{box("why", f"<p>Showing P(top 10) changes how the list should be used. An auction team should treat a {TB[0]['p_top10']}% player as a near-certain pick and a {TB[-1]['p_top10']}% player as \"one of several similar options\". A bare rank 1–10 would hide that difference.</p>")}
</section>"""
