"""Step 1 - Build a clean, state-annotated delivery table.

Output: outputs/deliveries.parquet (one row per delivery, innings 1-2 only)
with the full pre-delivery match state needed by the pressure model.
"""
import numpy as np
import pandas as pd
from config import path, OUT, FULL_MEMBERS, IPL_TEAMS, EXCLUDE_EMERGING


def team_tier(tid, comp_kind):
    if comp_kind == "IPL":
        return "IPL"
    if comp_kind == "EMERGING":
        return "A"
    return "FULL" if tid in FULL_MEMBERS else "ASSOC"


def main():
    b = pd.read_csv(path("balls"), low_memory=False)
    m = pd.read_csv(path("matches"))
    c = pd.read_csv(path("comps"))

    # ---- competition context ----
    c["comp_kind"] = np.where(c.comp_name.str.startswith("IPL"), "IPL",
                     np.where(c.match_format.eq("T20"), "EMERGING", "T20I"))
    m = m.merge(c[["comp_id", "comp_name", "comp_kind"]], on="comp_id", how="left")
    m["no_result"] = m.result.str.contains("Abandon|No Result", case=False, na=True) | m.win_team_id.isna() | (m.win_team_id == 0)
    m["tie"] = m.result.str.contains("Tie|Super Over", case=False, na=False)
    m["year"] = pd.to_datetime(m.match_date).dt.year

    # super overs (innings 3/4) are excluded from state modelling
    b = b[b.innings.isin([1, 2])].copy()
    if EXCLUDE_EMERGING:
        b = b[~b.match_id.isin(m.loc[m.comp_kind == "EMERGING", "match_id"])]
    b = b.merge(m[["match_id", "comp_id", "comp_kind", "match_date", "year", "stage", "knock_out",
                   "first_inn_revised_overs", "second_inn_revised_overs", "revised_target",
                   "win_team_id", "no_result", "tie"]], on="match_id", how="left")
    b = b.sort_values(["match_id", "innings", "innings_ball_num"]).reset_index(drop=True)

    et = b.extras_type.fillna("none")
    b["is_wide"] = et.eq("wide")
    b["is_noball"] = et.isin(["Overstep", "other"])
    b["is_legal"] = ~(b.is_wide | b.is_noball)
    b["faced"] = ~b.is_wide  # a no-ball counts as a ball faced by the batter
    b["bat_runs"] = b.runs
    # Runs on the delivery for the team. The feed stores the extras *type* in
    # extras1_runs (a code) and extra runs from no-ball byes in extras_2_runs;
    # one-run penalty for wide/no-ball and an (approximate) 1 for byes/leg-byes.
    b["team_runs"] = (b.runs + b.extras_2_runs + (b.is_wide | b.is_noball).astype(int)
                      + et.isin(["byes", "legbyes"]).astype(int) + 5 * et.eq("Penalty").astype(int))
    # runs charged to the bowler (byes/leg-byes are not)
    b["bowl_runs"] = b.runs + (b.is_wide | b.is_noball).astype(int)
    b["is_wicket"] = b.is_wicket.astype(bool)
    dt = b.dismissal_type.fillna("")
    b["bowler_wkt"] = b.is_wicket & ~dt.isin(["RunOut", "Retire Out", "Obstracting the field", "Obstructing the field"])
    b["striker_out"] = b.is_wicket & (b.dismissed_player_id.fillna(-1) == b.striker_id) & ~dt.eq("Retire Out")
    b.loc[b.is_wicket & b.dismissed_player_id.isna() & ~dt.isin(["RunOut", "Retire Out"]), "striker_out"] = True
    b["team_wkt"] = b.is_wicket & ~dt.eq("Retire Out")

    g = b.groupby(["match_id", "innings"], sort=False)
    b["score_before"] = g.team_runs.cumsum() - b.team_runs
    b["wkts_before"] = g.team_wkt.cumsum() - b.team_wkt.astype(int)
    b["legal_before"] = g.is_legal.cumsum() - b.is_legal.astype(int)

    # scheduled balls for the innings (rain-reduced matches use revised overs, stored in balls)
    rev1 = b.first_inn_revised_overs.where(b.first_inn_revised_overs > 0)
    rev2 = b.second_inn_revised_overs.where(b.second_inn_revised_overs > 0)
    b["max_balls"] = np.where(b.innings == 1, rev1.fillna(120), rev2.fillna(rev1).fillna(120)).astype(float)
    b["balls_left"] = (b.max_balls - b.legal_before).clip(lower=1)
    b["wkts_left"] = (10 - b.wkts_before).clip(lower=1)

    totals = b[b.innings == 1].groupby("match_id").team_runs.sum().rename("first_total")
    b = b.merge(totals, on="match_id", how="left")
    b["target"] = np.where(b.revised_target.fillna(0) > 0, b.revised_target, b.first_total + 1)
    b["runs_needed"] = np.where(b.innings == 2, b.target - b.score_before, np.nan)
    b["rrr"] = np.where(b.innings == 2, 6 * b.runs_needed / b.balls_left, np.nan)
    b["crr"] = np.where(b.legal_before > 0, 6 * b.score_before / b.legal_before.clip(lower=1), np.nan)
    b["over_no"] = (b.legal_before // 6 + 1).clip(upper=20)
    b["phase"] = pd.cut(b.over_no, [0, 6, 15, 20], labels=["PP", "MID", "DEATH"]).astype(str)

    # labels: did the batting side win?
    b["bat_won"] = np.where(b.tie | b.no_result, np.nan, (b.batting_team_id == b.win_team_id).astype(float))

    # opposition strength context
    b["bat_tier"] = [team_tier(t, k) for t, k in zip(b.batting_team_id, b.comp_kind)]
    b["bowl_tier"] = [team_tier(t, k) for t, k in zip(b.bowling_team_id, b.comp_kind)]

    # ---- data-quality check: reconstructed chase totals vs. results ----
    fin = b.groupby(["match_id", "innings"]).agg(tot=("team_runs", "sum"), tgt=("target", "first"),
                                                  bw=("bat_won", "first"), wk=("team_wkt", "sum")).reset_index()
    ch = fin[(fin.innings == 2) & (fin.bw == 1)]
    reached = (ch.tot >= ch.tgt).mean()
    gap = (ch.tgt - ch.tot).clip(lower=0)
    print(f"[QA] deliveries={len(b):,} matches={b.match_id.nunique()} | "
          f"winning chases whose reconstructed total reaches target: {reached:.1%} "
          f"(median shortfall {gap.median():.0f}, mean {gap.mean():.2f} runs - byes/leg-bye/wide run counts are not in the feed)")

    keep = ["match_id", "comp_id", "comp_kind", "year", "match_date", "stage", "knock_out", "innings",
            "innings_ball_num", "over_no", "phase", "batting_team_id", "bowling_team_id", "bat_tier", "bowl_tier",
            "striker_id", "striker_name", "non_striker_id", "bowler_id", "bowler_name", "pace_or_spin", "bowling_type",
            "batting_type", "batting_order", "is_legal", "is_wide", "is_noball", "faced", "bat_runs", "team_runs", "bowl_runs",
            "is_four", "is_six", "is_wicket", "bowler_wkt", "striker_out", "team_wkt", "dismissal_type",
            "dismissed_player_id", "score_before", "wkts_before", "legal_before", "max_balls", "balls_left",
            "wkts_left", "first_total", "target", "runs_needed", "rrr", "crr", "bat_won", "no_result", "tie"]
    b[keep].to_parquet(OUT / "deliveries.parquet", index=False)
    print("[OK] wrote", OUT / "deliveries.parquet")


if __name__ == "__main__":
    main()
