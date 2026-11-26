"""Analyze Sarawak DUN historical election data and rank 2026 marginal seats."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from report_facts import (
    CONSOLIDATED,
    CONTEXT_DATE,
    LIVE,
    NOMINATION_DATE,
    POLLING_DATE,
    SCORE_COMPONENTS,
    TIER_ORDER,
    UNCERTAIN,
    compute_facts,
    join_seats,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
OUT_DIR = ROOT_DIR / "outputs"
CSV_PATH = OUT_DIR / "sarawak_2026_marginal_seats.csv"
REPORT_PATH = OUT_DIR / "marginal_seats_report.md"

PRN11_DATE = "2016-05-07"
PRN12_DATE = "2021-12-18"
GE15_DATE = "2022-11-19"

# Post-merger political changes reported after PSB's Apr 2024 merger into PDP
# (context as of 26 Nov 2026). Maps seat -> (2026 outlook status, analyst note).
POLITICAL_OVERRIDES: dict[str, tuple[str, str]] = {
    "N.53 Bawang Assan": (
        "Uncertain 2026 (Open Seat: Ex-PSB Incumbent Left PDP, Not Defending)",
        "Ex-PSB incumbent Wong Soon Koh joined PDP in Apr 2024 but quit PDP in late Nov 2026 and "
        "said he will not defend the seat (while stating continued support for GPS), leaving an open seat.",
    ),
    "N.33 Engkilili": (
        "Uncertain 2026 (Ex-PSB Incumbent Left PDP Nov 2026)",
        "Ex-PSB incumbent Johnichal Rayong joined PDP in Apr 2024 but quit PDP in late Nov 2026 "
        "(while stating continued support for GPS); his 2026 candidacy and alignment are unsettled.",
    ),
}


def _norm_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.strftime("%Y-%m-%d")


def _clip01(val: float) -> float:
    return float(np.clip(val, 0.0, 1.0))


def _harmonize_bloc(coalition: str, party: str) -> str:
    if coalition in ("BN", "GPS"):
        return "GPS/BN"
    if coalition == "PH":
        return "PH"
    if party == "PSB":
        return "PSB"
    return f"{party}/{coalition}"


def _classify_region(code_parlimen: str) -> str:
    p_num = int(code_parlimen.split(".")[1])
    if 192 <= p_num <= 205:
        return "Southern (Kuching-Samarahan-Serian-Sri Aman-Betong)"
    if 206 <= p_num <= 216:
        return "Central (Sarikei-Sibu-Mukah-Kapit)"
    if 217 <= p_num <= 222:
        return "Northern (Bintulu-Miri-Limbang-Lawas)"
    raise ValueError(f"Unexpected code_parlimen: {code_parlimen}")


def _classify_size_band(voters_total: int) -> str:
    if voters_total < 10_000:
        return "Small Rural (<10k)"
    if voters_total < 20_000:
        return "Medium (10k-20k)"
    return "Large Urban (>=20k)"


def _classify_tier(row: dict) -> str:
    maj_pct = row["majority_perc"]
    maj_votes = row["majority_votes"]
    win_pct = row["winner_vote_share_perc"]
    gap = row["top2_opposition_combined_gap"]
    swing = row["winning_share_swing_pp"]
    t_chg = row["turnout_change_2016_to_2021_pp"]
    sal_gap = row["saluran_youth_gap_pp"]
    t21 = row["prn12_2021_turnout_perc"]

    if (maj_pct < 5.0) or (maj_votes < 500):
        return "Tier 1 (Razor-Thin)"
    if (5.0 <= maj_pct < 10.0) or (win_pct < 50.0 and gap < 0):
        return "Tier 2 (Marginal)"
    if 10.0 <= maj_pct < 15.0:
        neg_swing = pd.notna(swing) and (swing < 0.0)
        large_turnout_shift = pd.notna(t_chg) and (abs(t_chg) >= 10.0)
        large_sal_gap = pd.notna(sal_gap) and (abs(sal_gap) >= 5.0)
        low_t21 = pd.notna(t21) and (t21 < 55.0)
        if neg_swing or large_turnout_shift or large_sal_gap or low_t21:
            return "Tier 3 (Watchlist)"
    return "Safe"


def _compute_saluran_metrics(
    sal_ballots: pd.DataFrame,
    sal_stats: pd.DataFrame,
    prn12_winner_uid_by_seat: dict[str, str],
    prn12_valid_by_seat: dict[str, int],
) -> dict[str, dict]:
    """Compute within-PM older vs younger saluran vote-share gap per seat."""
    # Exclude postal (/UP ) and early (/00 ) streams which share saluran=1
    stats_ord = sal_stats[
        ~sal_stats["dm"].str.contains("/UP ", regex=False)
        & ~sal_stats["dm"].str.contains("/00 ", regex=False)
    ].copy()
    ballots_ord = sal_ballots[
        ~sal_ballots["dm"].str.contains("/UP ", regex=False)
        & ~sal_ballots["dm"].str.contains("/00 ", regex=False)
    ].copy()

    pm_max = (
        stats_ord.groupby(["seat", "dm", "pm"], as_index=False)["saluran"]
        .max()
        .rename(columns={"saluran": "max_saluran"})
    )
    multi_pms = pm_max[pm_max["max_saluran"] >= 2]
    pm_counts = multi_pms.groupby("seat").size().to_dict()

    stats_m = stats_ord.merge(multi_pms, on=["seat", "dm", "pm"], how="inner")
    stats_m["stream_group"] = np.where(
        stats_m["saluran"] <= stats_m["max_saluran"] / 2.0, "older", "younger"
    )
    valid_by_group = (
        stats_m.groupby(["seat", "stream_group"])["votes_valid"].sum().to_dict()
    )

    ballots_m = ballots_ord.merge(multi_pms, on=["seat", "dm", "pm"], how="inner")
    ballots_m["stream_group"] = np.where(
        ballots_m["saluran"] <= ballots_m["max_saluran"] / 2.0, "older", "younger"
    )
    ballots_m["is_2021_winner"] = (
        ballots_m["seat"].map(prn12_winner_uid_by_seat) == ballots_m["candidate_uid"]
    )
    win_votes_by_group = (
        ballots_m[ballots_m["is_2021_winner"]]
        .groupby(["seat", "stream_group"])["votes"]
        .sum()
        .to_dict()
    )

    results: dict[str, dict] = {}
    for seat, prn12_valid in prn12_valid_by_seat.items():
        n_multi = int(pm_counts.get(seat, 0))
        older_valid = int(valid_by_group.get((seat, "older"), 0))
        younger_valid = int(valid_by_group.get((seat, "younger"), 0))
        coverage = 100.0 * (older_valid + younger_valid) / prn12_valid if prn12_valid else 0.0

        if n_multi == 0 or older_valid == 0 or younger_valid == 0:
            results[seat] = {
                "winner_share_older_saluran_perc": np.nan,
                "winner_share_younger_saluran_perc": np.nan,
                "saluran_youth_gap_pp": np.nan,
                "multi_saluran_pm_count": n_multi,
                "multi_saluran_vote_coverage_perc": round(coverage, 2),
            }
        else:
            older_w = int(win_votes_by_group.get((seat, "older"), 0))
            younger_w = int(win_votes_by_group.get((seat, "younger"), 0))
            older_pct = 100.0 * older_w / older_valid
            younger_pct = 100.0 * younger_w / younger_valid
            results[seat] = {
                "winner_share_older_saluran_perc": round(older_pct, 2),
                "winner_share_younger_saluran_perc": round(younger_pct, 2),
                "saluran_youth_gap_pp": round(younger_pct - older_pct, 2),
                "multi_saluran_pm_count": n_multi,
                "multi_saluran_vote_coverage_perc": round(coverage, 2),
            }
    return results


def _compute_ge15_dun_shares(ge15_ballots: pd.DataFrame) -> pd.DataFrame:
    """Aggregate GE15 (2022) saluran ballots to DUN level bloc vote shares (postal excluded)."""
    b = ge15_ballots[ge15_ballots["state"] == "Sarawak"].copy()
    b["dun_token"] = b["dm"].str.split("/").str[1]
    b = b[b["dun_token"] != "00"].copy()
    b["code_dun"] = "N." + b["dun_token"]
    b["bloc"] = np.select(
        [
            b["coalition"] == "GPS",
            b["coalition"] == "PH",
            b["coalition"] == "PN",
            b["party"] == "PSB",
        ],
        ["GPS", "PH", "PN", "PSB"],
        default="OTHER",
    )
    votes = b.pivot_table(index="code_dun", columns="bloc", values="votes", aggfunc="sum", fill_value=0)
    for bloc in ("GPS", "PH", "PN", "PSB", "OTHER"):
        if bloc not in votes.columns:
            votes[bloc] = 0
    total = votes[["GPS", "PH", "PN", "PSB", "OTHER"]].sum(axis=1)
    shares = votes[["GPS", "PH", "PN", "PSB", "OTHER"]].div(total, axis=0) * 100.0
    non_gps = shares[["PH", "PN", "PSB", "OTHER"]]
    out = pd.DataFrame(
        {
            "ge15_dun_valid_votes": total.astype(int),
            "ge15_dun_gps_share_perc": shares["GPS"],
            "ge15_dun_ph_share_perc": shares["PH"],
            "ge15_dun_pn_share_perc": shares["PN"],
            "ge15_dun_psb_share_perc": shares["PSB"],
            "ge15_dun_other_share_perc": shares["OTHER"],
            "ge15_dun_leading_bloc": shares.idxmax(axis=1),
            "ge15_dun_gps_margin_pp": shares["GPS"] - non_gps.max(axis=1),
        }
    )
    return out


def _build_political_note(row: dict) -> str:
    parts: list[str] = []
    seat = row["seat"]
    if row["is_prk_updated"]:
        parts.append(
            f"Updated with {row['baseline_election_date']} PRK (GPS/PBB won {row['winner_vote_share_perc']:.1f}%, "
            f"majority {row['majority_votes']:,}, turnout {row['voter_turnout_perc']:.1f}%)."
        )
    if seat == "N.11 Batu Lintang":
        parts.append(
            "Incumbent See Chee How won under PSB in 2021 (+93 votes over SUPP/GPS; PKR 3rd at 14.8%) "
            "but left PSB in Aug 2022 to sit as an Independent before PSB's Apr 2024 PDP merger."
        )
    elif row["seat"] in POLITICAL_OVERRIDES:
        parts.append(POLITICAL_OVERRIDES[row["seat"]][1])
    elif row["psb_2021_role"] == "Winner":
        parts.append(
            f"PSB incumbent ({row['winner_name']}) merged into GPS component PDP in Apr 2024, "
            "consolidating the ruling coalition's hold ahead of 2026."
        )
    elif row["psb_2021_role"] == "Runner-up":
        if row["live_2026_status"].startswith("GPS Consolidation"):
            parts.append(
                f"2021 runner-up PSB ({row['runner_up_vote_share_perc']:.1f}%) merged into GPS/PDP in 2024, "
                "leaving <15% residual opposition share in 2021 terms."
            )
        else:
            parts.append(
                f"2021 runner-up PSB ({row['runner_up_vote_share_perc']:.1f}%) merged into GPS/PDP in 2024, "
                f"though {row['third_place_party']} ({row['third_place_vote_share_perc']:.1f}%) or minor parties remain active."
            )
    elif row["psb_2021_role"] == "Third-place" and row["psb_2021_vote_share_perc"] >= 10.0:
        parts.append(
            f"3rd-place PSB ({row['psb_2021_vote_share_perc']:.1f}%) subsequently merged into GPS/PDP in 2024, "
            f"directly shifting the three-cornered arithmetic against {row['runner_up_party']}."
        )
    elif row["marginality_tier"] != "Safe":
        parts.append(
            f"Live multi-cornered contest: {row['winner_party']} ({row['winner_vote_share_perc']:.1f}%) vs "
            f"{row['runner_up_party']} ({row['runner_up_vote_share_perc']:.1f}%)"
            + (
                f" and {row['third_place_party']} ({row['third_place_vote_share_perc']:.1f}%)."
                if row["third_place_votes"] > 0
                else "."
            )
        )
    else:
        parts.append(
            f"Comfortable {row['winner_party']}/{row['winner_coalition']} stronghold ({row['majority_perc']:.1f}% majority)."
        )

    if row["electorate_size_band"] == "Small Rural (<10k)" and row["marginality_tier"] != "Safe":
        parts.append(
            f"Small rural roll ({row['voters_total']:,} voters in baseline; "
            f"{row['ge15_dun_voters_total']:,} after Undi18/automatic registration) amplifies small raw-vote swings."
        )
    elif row["electorate_size_band"] == "Large Urban (>=20k)" and row["marginality_tier"] != "Safe":
        parts.append(
            f"Large urban electorate ({row['voters_total']:,} in baseline → {row['ge15_dun_voters_total']:,} in GE15)."
        )
    return " ".join(parts)


def build_dataset() -> pd.DataFrame:
    swk_ballots = pd.read_parquet(RAW_DIR / "headline_ballots_state_swk.parquet")
    swk_stats = pd.read_parquet(RAW_DIR / "headline_stats_state_swk.parquet")
    prk_ballots = pd.read_parquet(RAW_DIR / "headline_ballots_byelections.parquet")
    prk_stats = pd.read_parquet(RAW_DIR / "headline_stats_byelections.parquet")
    sal_ballots = pd.read_parquet(RAW_DIR / "swk_se12_ballots.parquet")
    sal_stats = pd.read_parquet(RAW_DIR / "swk_se12_stats.parquet")
    fed_ballots = pd.read_parquet(RAW_DIR / "headline_ballots_federal.parquet")
    fed_stats = pd.read_parquet(RAW_DIR / "headline_stats_federal.parquet")
    ge15_sal = pd.read_parquet(RAW_DIR / "ge15_stats.parquet")
    ge15_ballots = pd.read_parquet(RAW_DIR / "ge15_ballots.parquet")
    ge15_shares = _compute_ge15_dun_shares(ge15_ballots)

    for df in (
        swk_ballots,
        swk_stats,
        prk_ballots,
        prk_stats,
        sal_ballots,
        sal_stats,
        fed_ballots,
        fed_stats,
        ge15_sal,
    ):
        df["date"] = _norm_date(df["date"])

    geo = json.loads((RAW_DIR / "sarawak_2015_dun.geojson").read_text(encoding="utf-8"))
    geo_meta = {
        feat["properties"]["dun"]: feat["properties"] for feat in geo["features"]
    }

    # Filter PRN11 (2016) & PRN12 (2021)
    st16 = swk_stats[swk_stats["date"] == PRN11_DATE].set_index("seat")
    bl16 = swk_ballots[swk_ballots["date"] == PRN11_DATE]
    st21 = swk_stats[swk_stats["date"] == PRN12_DATE].set_index("seat")
    bl21 = swk_ballots[swk_ballots["date"] == PRN12_DATE]

    # Post-2021 Sarawak PRK overlay
    prk_s_swk = prk_stats[(prk_stats["state"] == "Sarawak") & (prk_stats["date"] > PRN12_DATE)]
    prk_b_swk = prk_ballots[(prk_ballots["state"] == "Sarawak") & (prk_ballots["date"] > PRN12_DATE)]
    latest_prk_by_seat: dict[str, str] = {}
    if not prk_s_swk.empty:
        for seat, grp in prk_s_swk.groupby("seat"):
            latest_prk_by_seat[seat] = grp["date"].max()

    # GE15 Parliament stats/winners (Sarawak)
    fed22_s = fed_stats[(fed_stats["state"] == "Sarawak") & (fed_stats["date"] == GE15_DATE)].set_index("seat")
    fed22_b = fed_ballots[(fed_ballots["state"] == "Sarawak") & (fed_ballots["date"] == GE15_DATE)]
    fed22_win = (
        fed22_b.sort_values("votes", ascending=False)
        .groupby("seat", as_index=False)
        .first()
        .set_index("seat")
    )

    # GE15 DUN-level post-Undi18 voter roll & non-postal turnout
    ge15_swk = ge15_sal[ge15_sal["state"] == "Sarawak"].copy()
    ge15_swk["dun_token"] = ge15_swk["dm"].str.split("/").str[1]
    ge15_swk = ge15_swk[ge15_swk["dun_token"] != "00"].copy()
    ge15_swk["code_dun"] = "N." + ge15_swk["dun_token"]
    ge15_dun = (
        ge15_swk.groupby("code_dun", as_index=False)[["voters_total", "ballots_issued"]]
        .sum()
        .set_index("code_dun")
    )

    # 2021 PRN12 winners for saluran lookup
    prn12_winners = (
        bl21.sort_values("votes", ascending=False)
        .groupby("seat", as_index=False)
        .first()
        .set_index("seat")
    )
    saluran_metrics = _compute_saluran_metrics(
        sal_ballots=sal_ballots,
        sal_stats=sal_stats,
        prn12_winner_uid_by_seat=prn12_winners["candidate_uid"].to_dict(),
        prn12_valid_by_seat=st21["votes_valid"].astype(int).to_dict(),
    )

    rows: list[dict] = []
    for seat in sorted(st21.index):
        meta = geo_meta[seat]
        code_dun = meta["code_dun"]
        parlimen = meta["parlimen"]
        code_parlimen = meta["code_parlimen"]

        s21 = st21.loc[seat]
        c21 = bl21[bl21["seat"] == seat].sort_values("votes", ascending=False).reset_index(drop=True)

        # Apply PRK overlay if present
        if seat in latest_prk_by_seat:
            prk_date = latest_prk_by_seat[seat]
            s_base = prk_s_swk[(prk_s_swk["seat"] == seat) & (prk_s_swk["date"] == prk_date)].iloc[0]
            c_base = (
                prk_b_swk[(prk_b_swk["seat"] == seat) & (prk_b_swk["date"] == prk_date)]
                .sort_values("votes", ascending=False)
                .reset_index(drop=True)
            )
            baseline_date = prk_date
            is_prk = True
        else:
            s_base = s21
            c_base = c21
            baseline_date = PRN12_DATE
            is_prk = False

        w = c_base.iloc[0]
        ru = c_base.iloc[1]
        c3 = c_base.iloc[2] if len(c_base) > 2 else None

        votes_valid = int(s_base["votes_valid"])
        winner_votes = int(w["votes"])
        ru_votes = int(ru["votes"])
        c3_votes = int(c3["votes"]) if c3 is not None else 0
        c3_pct = float(c3["votes_perc"]) if c3 is not None else 0.0
        maj_votes = int(s_base["majority"])
        maj_pct = float(s_base["majority_perc"])

        shares = c_base["votes"].astype(float) / votes_valid
        enc = float(1.0 / (shares**2).sum())
        gap_votes = winner_votes - (ru_votes + c3_votes)
        gap_pct = 100.0 * gap_votes / votes_valid

        # Historical 2016 PRN11 comparison
        s16 = st16.loc[seat]
        c16 = bl16[bl16["seat"] == seat].sort_values("votes", ascending=False).reset_index(drop=True)
        w16 = c16.iloc[0]
        uncontested_16 = bool(pd.isna(s16["voter_turnout"]) or int(s16["majority"]) == 0)

        w_bloc_base = _harmonize_bloc(str(w["coalition"]), str(w["party"]))
        w_bloc_16 = _harmonize_bloc(str(w16["coalition"]), str(w16["party"]))

        if uncontested_16:
            t16_pct = np.nan
            maj16_pct = np.nan
            w_bloc_16_share = np.nan
            swing_basis = "uncontested_2016"
            swing_pp = np.nan
            margin_chg_pp = np.nan
            turnout_chg_pp = np.nan
        else:
            t16_pct = float(s16["voter_turnout"])
            maj16_pct = float(s16["majority_perc"])
            if str(w["coalition"]) == "GPS":
                w_bloc_16_share = float(c16[c16["coalition"] == "BN"]["votes_perc"].sum())
                swing_basis = "coalition_continuity_bn_to_gps"
            elif str(w["coalition"]) == "PH":
                w_bloc_16_share = float(c16[c16["coalition"] == "PH"]["votes_perc"].sum())
                swing_basis = "coalition_continuity_ph"
            else:
                matched = c16[c16["candidate_uid"] == w["candidate_uid"]]
                if matched.empty:
                    raise ValueError(f"Expected 2016 candidate match for {seat} ({w['candidate_uid']})")
                w_bloc_16_share = float(matched["votes_perc"].sum())
                swing_basis = "incumbent_candidate_continuity"
            swing_pp = float(w["votes_perc"]) - w_bloc_16_share
            margin_chg_pp = maj_pct - maj16_pct
            turnout_chg_pp = float(s21["voter_turnout"]) - t16_pct

        flipped_bloc = (w_bloc_16 != w_bloc_base) and not uncontested_16

        # Turnout & Undi18 GE15
        prn12_voters = int(s21["voters_total"])
        prn12_turnout = float(s21["voter_turnout"])
        low_turnout_flag = bool(
            (prn12_turnout < 55.0)
            or (pd.notna(turnout_chg_pp) and turnout_chg_pp <= -10.0)
        )

        ge15_p_s = fed22_s.loc[parlimen]
        ge15_p_w = fed22_win.loc[parlimen]
        ge15_d = ge15_dun.loc[code_dun]
        ge15_dun_voters = int(ge15_d["voters_total"])
        ge15_dun_turnout = 100.0 * float(ge15_d["ballots_issued"]) / ge15_dun_voters
        undi18_growth = 100.0 * (ge15_dun_voters - prn12_voters) / prn12_voters

        sal = saluran_metrics[seat]

        # Composite marginality score (0-100)
        score_margin_pct = 40.0 * _clip01((30.0 - maj_pct) / 30.0)
        score_margin_votes = 15.0 * _clip01((2500.0 - maj_votes) / 2500.0)
        score_plurality_split = (
            10.0 * _clip01((60.0 - float(w["votes_perc"])) / 35.0)
            + 10.0 * _clip01((10.0 - gap_pct) / 25.0)
        )
        score_hist_swing = (
            15.0 * _clip01(-swing_pp / 25.0) if pd.notna(swing_pp) else 0.0
        )
        t_vol = (
            5.0 * _clip01(-turnout_chg_pp / 20.0) if pd.notna(turnout_chg_pp) else 0.0
        )
        s_vol = (
            5.0 * _clip01(abs(sal["saluran_youth_gap_pp"]) / 15.0)
            if pd.notna(sal["saluran_youth_gap_pp"])
            else 0.0
        )
        score_volatility = t_vol + s_vol
        composite_score = round(
            score_margin_pct
            + score_margin_votes
            + score_plurality_split
            + score_hist_swing
            + score_volatility,
            2,
        )

        # PSB 2021 role & realignment context
        psb_cands = c21[c21["party"] == "PSB"]
        if psb_cands.empty:
            psb_votes = 0
            psb_pct = 0.0
            psb_role = "Did Not Contest"
        else:
            psb_row = psb_cands.iloc[0]
            psb_votes = int(psb_row["votes"])
            psb_pct = float(psb_row["votes_perc"])
            psb_rank = int(c21.index[c21["party"] == "PSB"][0]) + 1
            if psb_rank == 1:
                psb_role = "Winner"
            elif psb_rank == 2:
                psb_role = "Runner-up"
            elif psb_rank == 3:
                psb_role = "Third-place"
            else:
                psb_role = "Other"

        psb_realignment_flag = psb_role in {"Winner", "Runner-up"}

        # GPS margin in PRN12 2021 (all seats, incl. Jepak) vs GE15 2022 DUN-level margin
        gps21_share = float(c21[c21["coalition"] == "GPS"]["votes_perc"].sum())
        non_gps21 = c21[c21["coalition"] != "GPS"]["votes_perc"]
        prn12_gps_margin = gps21_share - (float(non_gps21.max()) if not non_gps21.empty else 0.0)
        g15 = ge15_shares.loc[code_dun]
        ge15_gps_margin = float(g15["ge15_dun_gps_margin_pp"])

        row_dict = {
            "code_dun": code_dun,
            "seat": seat,
            "code_parlimen": code_parlimen,
            "parlimen": parlimen,
            "region": _classify_region(code_parlimen),
            "baseline_election_date": baseline_date,
            "is_prk_updated": is_prk,
            "voters_total": int(s_base["voters_total"]),
            "electorate_size_band": _classify_size_band(int(s_base["voters_total"])),
            "votes_valid": votes_valid,
            "votes_rejected": int(s_base["votes_rejected"]),
            "voter_turnout_perc": round(float(s_base["voter_turnout"]), 2),
            "n_candidates": int(s_base["n_candidates"]),
            "winner_name": str(w["name"]),
            "winner_party": str(w["party"]),
            "winner_coalition": str(w["coalition"]),
            "winner_votes": winner_votes,
            "winner_vote_share_perc": round(float(w["votes_perc"]), 4),
            "runner_up_name": str(ru["name"]),
            "runner_up_party": str(ru["party"]),
            "runner_up_coalition": str(ru["coalition"]),
            "runner_up_votes": ru_votes,
            "runner_up_vote_share_perc": round(float(ru["votes_perc"]), 4),
            "third_place_party": str(c3["party"]) if c3 is not None else "NONE",
            "third_place_coalition": str(c3["coalition"]) if c3 is not None else "NONE",
            "third_place_votes": c3_votes,
            "third_place_vote_share_perc": round(c3_pct, 4),
            "majority_votes": maj_votes,
            "majority_perc": round(maj_pct, 4),
            "is_plurality_win": bool(float(w["votes_perc"]) < 50.0),
            "effective_num_candidates": round(enc, 4),
            "combined_non_winner_share": round(100.0 - float(w["votes_perc"]), 4),
            "top2_opposition_combined_gap": gap_votes,
            "top2_opposition_combined_gap_perc": round(gap_pct, 4),
            "top2_exceed_winner": bool(gap_votes < 0),
            "prn11_2016_uncontested": uncontested_16,
            "prn11_2016_winner_party": str(w16["party"]),
            "prn11_2016_winner_coalition": str(w16["coalition"]),
            "prn11_2016_turnout_perc": round(t16_pct, 2) if pd.notna(t16_pct) else np.nan,
            "prn11_2016_majority_perc": round(maj16_pct, 2) if pd.notna(maj16_pct) else np.nan,
            "winning_bloc_2016_share_perc": round(w_bloc_16_share, 2) if pd.notna(w_bloc_16_share) else np.nan,
            "swing_basis": swing_basis,
            "winning_share_swing_pp": round(swing_pp, 2) if pd.notna(swing_pp) else np.nan,
            "margin_change_pp": round(margin_chg_pp, 2) if pd.notna(margin_chg_pp) else np.nan,
            "flipped_bloc_2016_to_2021": flipped_bloc,
            "prn12_2021_voters_total": prn12_voters,
            "prn12_2021_turnout_perc": round(prn12_turnout, 2),
            "prn12_2021_majority_votes": int(s21["majority"]),
            "prn12_2021_majority_perc": round(float(s21["majority_perc"]), 4),
            "turnout_change_2016_to_2021_pp": round(turnout_chg_pp, 2) if pd.notna(turnout_chg_pp) else np.nan,
            "low_turnout_distortion_flag": low_turnout_flag,
            "ge15_parl_turnout_perc": round(float(ge15_p_s["voter_turnout"]), 2),
            "ge15_parl_winner_coalition": str(ge15_p_w["coalition"]),
            "ge15_parl_majority_perc": round(float(ge15_p_s["majority_perc"]), 2),
            "ge15_dun_voters_total": ge15_dun_voters,
            "ge15_dun_nonpostal_turnout_perc": round(ge15_dun_turnout, 2),
            "undi18_voter_growth_perc": round(undi18_growth, 2),
            "prn12_gps_margin_pp": round(prn12_gps_margin, 2),
            "ge15_dun_valid_votes": int(g15["ge15_dun_valid_votes"]),
            "ge15_dun_gps_share_perc": round(float(g15["ge15_dun_gps_share_perc"]), 2),
            "ge15_dun_ph_share_perc": round(float(g15["ge15_dun_ph_share_perc"]), 2),
            "ge15_dun_pn_share_perc": round(float(g15["ge15_dun_pn_share_perc"]), 2),
            "ge15_dun_psb_share_perc": round(float(g15["ge15_dun_psb_share_perc"]), 2),
            "ge15_dun_other_share_perc": round(float(g15["ge15_dun_other_share_perc"]), 2),
            "ge15_dun_leading_bloc": str(g15["ge15_dun_leading_bloc"]),
            "ge15_dun_gps_margin_pp": round(ge15_gps_margin, 2),
            "ge15_gps_trailed": bool(ge15_gps_margin < 0.0),
            "ge15_competitive": bool(abs(ge15_gps_margin) < 10.0),
            **sal,
            "score_margin_pct": round(score_margin_pct, 2),
            "score_margin_votes": round(score_margin_votes, 2),
            "score_plurality_split": round(score_plurality_split, 2),
            "score_hist_swing": round(score_hist_swing, 2),
            "score_volatility": round(score_volatility, 2),
            "composite_marginality_score": composite_score,
            "psb_2021_votes": psb_votes,
            "psb_2021_vote_share_perc": round(psb_pct, 2),
            "psb_2021_role": psb_role,
            "psb_realignment_flag": psb_realignment_flag,
        }
        # Tier classification uses unrounded exact checks
        tier_eval = dict(row_dict)
        tier_eval.update(
            {
                "majority_perc": maj_pct,
                "winner_vote_share_perc": float(w["votes_perc"]),
                "winning_share_swing_pp": swing_pp,
                "turnout_change_2016_to_2021_pp": turnout_chg_pp,
                "prn12_2021_turnout_perc": prn12_turnout,
            }
        )
        tier = _classify_tier(tier_eval)
        row_dict["marginality_tier"] = tier

        # Live 2026 status
        if str(w["party"]) == "PSB":
            if seat == "N.11 Batu Lintang":
                live_status = "Live 2026 Competitive (Ex-PSB Independent Incumbent)"
            else:
                live_status = "GPS Consolidation (PSB Incumbent Merged into PDP)"
        elif tier in {"Tier 1 (Razor-Thin)", "Tier 2 (Marginal)", "Tier 3 (Watchlist)"}:
            residual_non_gps_psb = 100.0 - float(w["votes_perc"]) - psb_pct
            if (
                str(w["coalition"]) == "GPS"
                and str(ru["party"]) == "PSB"
                and residual_non_gps_psb < 15.0
            ):
                live_status = "GPS Consolidation (PSB Runner-up Merged into PDP)"
            else:
                live_status = "Live 2026 Competitive (PH/Local Challenger)"
        else:
            live_status = "Safe Incumbent"

        if seat in POLITICAL_OVERRIDES:
            live_status = POLITICAL_OVERRIDES[seat][0]
        row_dict["live_2026_status"] = live_status
        row_dict["ge15_flags_safe_seat"] = bool(
            tier == "Safe" and (ge15_gps_margin < 0.0 or abs(ge15_gps_margin) < 10.0)
        )
        row_dict["political_context_note"] = _build_political_note(row_dict)
        rows.append(row_dict)

    out = pd.DataFrame(rows)
    out = out.sort_values(
        by=["composite_marginality_score", "majority_perc", "majority_votes"],
        ascending=[False, True, True],
    ).reset_index(drop=True)
    out.insert(0, "marginality_rank", range(1, len(out) + 1))

    # Reorder columns cleanly with rank, ids, tier, score, key metrics first
    front_cols = [
        "marginality_rank",
        "code_dun",
        "seat",
        "region",
        "marginality_tier",
        "composite_marginality_score",
        "live_2026_status",
        "psb_realignment_flag",
        "psb_2021_role",
    ]
    remaining = [c for c in out.columns if c not in front_cols]
    out = out[front_cols + remaining]
    return out


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def write_report(df: pd.DataFrame) -> None:
    f = compute_facts(df)
    df = f["df"]
    tc = f["tier_counts"]
    non_safe = f["non_safe"]

    def code(s: str) -> str:
        return f"`{s}`"

    def seats(sub: pd.DataFrame, col: str | None = None, fmt: str = "", suffix: str = "") -> str:
        return join_seats(sub, code, col, fmt, suffix)

    def n_status(tier: str, prefix: str) -> int:
        return int((df["marginality_tier"].eq(tier) & df["live_2026_status"].str.startswith(prefix)).sum())

    summary_rows = [
        [
            t,
            str(int(tc[t])),
            f"{100.0 * tc[t] / len(df):.1f}%",
            str(n_status(t, LIVE)),
            str(n_status(t, UNCERTAIN)),
            str(n_status(t, CONSOLIDATED)),
        ]
        for t in TIER_ORDER
    ]

    t12_rows = []
    for _, r in df[df["marginality_tier"].isin(TIER_ORDER[:2])].iterrows():
        c3_str = f"{r['third_place_party']} ({r['third_place_vote_share_perc']:.1f}%)" if r["third_place_votes"] > 0 else "—"
        swing_str = f"{r['winning_share_swing_pp']:+.1f} pp" if pd.notna(r["winning_share_swing_pp"]) else "N/A"
        sal_str = f"{r['saluran_youth_gap_pp']:+.1f} pp" if pd.notna(r["saluran_youth_gap_pp"]) else "N/A"
        t12_rows.append(
            [
                str(r["marginality_rank"]),
                code(r["seat"]),
                " ".join(r["marginality_tier"].split(" ")[:2]),
                f"{r['composite_marginality_score']:.1f}",
                f"{r['winner_party']}/{r['winner_coalition']} ({r['winner_vote_share_perc']:.1f}%)",
                f"{r['runner_up_party']}/{r['runner_up_coalition']} ({r['runner_up_vote_share_perc']:.1f}%)",
                c3_str,
                f"{r['majority_perc']:.2f}% ({r['majority_votes']:,})",
                f"{r['top2_opposition_combined_gap']:+,d}",
                swing_str,
                sal_str,
                r["electorate_size_band"].split(" ")[0],
                f"{r['undi18_voter_growth_perc']:+.1f}%",
                f"{r['ge15_dun_gps_margin_pp']:+.1f} pp",
                r["live_2026_status"],
            ]
        )

    t3_rows = []
    for _, r in df[df["marginality_tier"] == TIER_ORDER[2]].iterrows():
        swing_str = f"{r['winning_share_swing_pp']:+.1f} pp" if pd.notna(r["winning_share_swing_pp"]) else "N/A"
        sal_str = f"{r['saluran_youth_gap_pp']:+.1f} pp" if pd.notna(r["saluran_youth_gap_pp"]) else "N/A"
        t3_rows.append(
            [
                str(r["marginality_rank"]),
                code(r["seat"]),
                f"{r['composite_marginality_score']:.1f}",
                f"{r['winner_party']}/{r['winner_coalition']} ({r['winner_vote_share_perc']:.1f}%)",
                f"{r['runner_up_party']}/{r['runner_up_coalition']} ({r['runner_up_vote_share_perc']:.1f}%)",
                f"{r['majority_perc']:.2f}% ({r['majority_votes']:,})",
                swing_str,
                f"{r['turnout_change_2016_to_2021_pp']:+.1f} pp",
                sal_str,
                f"{r['ge15_dun_gps_margin_pp']:+.1f} pp",
                r["live_2026_status"],
            ]
        )

    ge15_rows = [
        [
            code(r["seat"]),
            " ".join(r["marginality_tier"].split(" ")[:2]),
            f"{r['prn12_gps_margin_pp']:+.1f}",
            f"{r['ge15_dun_gps_share_perc']:.1f}%",
            f"{r['ge15_dun_ph_share_perc']:.1f}%",
            f"{r['ge15_dun_pn_share_perc']:.1f}%",
            f"{r['ge15_dun_psb_share_perc']:.1f}%",
            f"{r['ge15_dun_other_share_perc']:.1f}%",
            f"{r['ge15_dun_gps_margin_pp']:+.1f}",
            r["ge15_dun_leading_bloc"],
        ]
        for _, r in f["ge15_watch"].iterrows()
    ]

    reg_rows = []
    reg_bullets = []
    for r in f["regions"]:
        reg_rows.append(
            [
                r["name"],
                str(r["seats"]),
                str(r["t1"]),
                str(r["t2"]),
                str(r["t3"]),
                str(r["safe"]),
                f"{r['nonsafe_share']:.1f}%",
                str(len(r["live"])),
                str(len(r["uncertain"])),
                str(len(r["consolidated"])),
                f"{r['median_maj']:.1f}%",
                f"{r['median_roll']:+.1f}%",
                str(len(r["ge15_trailed"])),
            ]
        )
        reg_bullets.append(
            f"- **{r['short']} ({r['range']}, {r['seats']} DUNs):** {r['nonsafe']} of {r['seats']} seats are Tier 1–3 "
            f"({r['nonsafe_share']:.1f}%). Live 2026: {seats(r['live'])}. Uncertain: {seats(r['uncertain'])}. "
            f"GPS-consolidation scenario: {seats(r['consolidated'])}. GPS trailed at DUN level in GE15 in "
            f"{len(r['ge15_trailed'])} seat(s): {seats(r['ge15_trailed'])}."
        )
    dense = f["densest_region"]

    sm = f["score_means"]
    comp_txt = ", ".join(f"{label} {sm[c]:.1f}/{mx}" for c, label, mx in SCORE_COMPONENTS)
    jr = f["jepak"]
    bl = f["batu_lintang"]
    mt2 = f["max_t2"]

    report = f"""# Sarawak 2026 State Election (PRN13): Marginal DUN Seats Analysis

_PRN13 nomination: {NOMINATION_DATE}; polling: {POLLING_DATE} (existing 82 seats). Political context as of {CONTEXT_DATE}._

## Executive Summary

Across all **{len(df)} Sarawak State Legislative Assembly (DUN) seats (`N.01`–`N.82`)** evaluated from official 2016 PRN11, 2021 PRN12, the 2023 `{jr['seat']}` by-election, 2021 SE-12 saluran results, and GE15 (2022) saluran results:

- **Unadjusted 2021/PRK baseline:** **{int(tc[TIER_ORDER[0]])}** Tier 1 (Razor-Thin), **{int(tc[TIER_ORDER[1]])}** Tier 2 (Marginal), **{int(tc[TIER_ORDER[2]])}** Tier 3 (Watchlist) and **{int(tc['Safe'])}** Safe seats (**{len(non_safe)}** non-safe).
- **Vote-splitting exposure:** **{f['plurality_count']}** seats were won with <50% of valid votes; in **{f['top2_exceed_count']}** the combined 2nd + 3rd place vote exceeded the winner (largest gaps: {seats(f['worst_split'], 'top2_opposition_combined_gap', '+,d')}).
- **Post-PSB 2026 outlook (scenario, not forecast):** PSB was 2021 winner or runner-up in **{f['psb_flag_all']}** seats ({f['psb_flag_nonsafe']} of the {len(non_safe)} Tier 1–3 seats). Of the {len(non_safe)} Tier 1–3 seats: **{len(f['live'])} live 2026 contests**, **{len(f['uncertain'])} uncertain** ({seats(f['uncertain'])} — ex-PSB incumbents who quit PDP in late Nov 2026), and **{len(f['consolidated'])} GPS/PDP consolidation scenarios** that assume former PSB voters follow PSB into GPS.
- **GE15 (2022) cross-check:** GPS trailed the strongest non-GPS bloc at DUN level in **{len(f['ge15_trailed'])}** of {len(df)} seats ({len(f['ge15_nonsafe_trailed'])} of them Tier 1–3) and led by <10 pp in another **{len(f['ge15_close_led'])}**. **{len(f['ge15_safe_flagged'])}** seats rated Safe on 2021 numbers were trailing or within 10 pp in GE15: {seats(f['ge15_safe_flagged'])}.

{_md_table(["Marginality Tier", "Seats", "% of 82", "Live 2026", "Uncertain 2026", "GPS Consolidation"], summary_rows)}

---

## Methodology & Composite Marginality Formula

Each seat receives a **Composite Marginality Score (0–100)** from five components (`clip(x) = min(max(x, 0), 1)`; missing 2016/saluran sub-terms count as 0 points without altering raw columns):

1. **Baseline % Majority (40 pts):** `40 * clip((30 - majority_perc) / 30)`
2. **Small-Seat Raw Majority Risk (15 pts):** `15 * clip((2500 - majority_votes) / 2500)`
3. **Plurality & Split-Vote Exposure (20 pts):** `10 * clip((60 - winner_vote_share_perc) / 35) + 10 * clip((10 - top2_opposition_combined_gap_perc) / 25)`
4. **Negative Historical Swing, 2016 → Baseline (15 pts):** `15 * clip(-winning_share_swing_pp / 25)` (BN→GPS, PH, or same-candidate continuity)
5. **Turnout & Saluran Youth Volatility (10 pts):** `5 * clip(-turnout_change_2016_to_2021_pp / 20) + 5 * clip(|saluran_youth_gap_pp| / 15)`

**Tier rules (top-down):** Tier 1: `majority_perc < 5%` or `majority_votes < 500`. Tier 2: `5% <= majority_perc < 10%` or plurality win where 2nd + 3rd > winner. Tier 3: `10% <= majority_perc < 15%` plus a volatility trigger (negative swing, |turnout Δ| ≥ 10 pp, |youth gap| ≥ 5 pp, or 2021 turnout < 55%). Safe: the rest.

**GE15 cross-check (separate signal, not in the score):** GE15 saluran ballots aggregated to DUN level via the polling-district code (postal votes excluded). Blocs: GPS, PH, PN, PSB, Other. `ge15_dun_gps_margin_pp` = GPS share − largest non-GPS bloc share.

---

## Tier 1 (Razor-Thin) & Tier 2 (Marginal) Seats

{_md_table(["Rank", "Seat", "Tier", "Score", "2021 Winner", "2nd Place", "3rd Place", "Majority", "Top2 Opp Gap", "16→21 Swing", "Youth Gap", "Size", "Roll Growth (Undi18+AVR)", "GE15 GPS Margin", "2026 Outlook"], t12_rows)}

### Tier 3 (Watchlist) Seats

{_md_table(["Rank", "Seat", "Score", "2021 Winner", "2nd Place", "Majority", "16→21 Swing", "Turnout Δ", "Youth Gap", "GE15 GPS Margin", "2026 Outlook"], t3_rows)}

---

## GE15 Seat-Level Cross-Check (GPS trailed or within 10 pp)

{_md_table(["Seat", "Tier", "2021 GPS Margin (pp)", "GE15 GPS", "GE15 PH", "GE15 PN", "GE15 PSB", "GE15 Other", "GE15 GPS Margin (pp)", "GE15 Leader"], ge15_rows)}

GE15 was a federal contest with different candidates; PH (DAP/PKR) typically polls better in federal than state contests in urban Sarawak, so treat these as an upper bound on opposition strength rather than a state-election forecast.

---

## Regional Breakdown

{_md_table(["Region", "Seats", "T1", "T2", "T3", "Safe", "Non-Safe %", "Live", "Uncertain", "Consolidated", "Median Maj %", "Median Roll Growth", "GE15 GPS Trailed"], reg_rows)}

{chr(10).join(reg_bullets)}

The highest share of Tier 1–3 seats is in **{dense['short']}** ({dense['nonsafe']}/{dense['seats']} = {dense['nonsafe_share']:.1f}%).

---

## Key Data Caveats & 2026 Context

1. **2021 COVID-era turnout:** Mean turnout fell from **{f['mean_t16']:.1f}%** in 2016 ({f['n_contested_2016']} contested seats) to **{f['mean_t21']:.1f}%** in 2021 (mean change {f['mean_t_chg']:+.1f} pp). Largest drops among Tier 1–3 seats: {seats(f['worst_turnout_drops'], 'turnout_change_2016_to_2021_pp', '+.1f', ' pp')}.
2. **Voter-roll growth (Undi18 + automatic registration):** PRN12 preceded both reforms. GE15 non-postal DUN rolls were a median **{f['med_roll']:+.1f}%** larger (from {f['min_roll']['undi18_voter_growth_perc']:+.1f}% in `{f['min_roll']['seat']}` to {f['max_roll']['undi18_voter_growth_perc']:+.1f}% in `{f['max_roll']['seat']}`). Growth reflects all newly auto-registered adults, not only 18–20-year-olds; the 2026 roll will be larger again.
3. **PSB realignment is a scenario assumption:** PSB dissolved into GPS component PDP in Apr 2024. The consolidation label assumes former PSB voters follow; many 2021 PSB votes were anti-GPS protest votes. Seats treated as consolidation: {seats(f['consolidated'])}. `{bl['seat']}` stays live: incumbent See Chee How left PSB in Aug 2022 and sits as an Independent.
4. **Late-Nov 2026 changes:** {' '.join(f"`{r['seat']}`: {r['political_context_note']}" for _, r in f['overrides'].iterrows())}
5. **Edge cases:**
   - **`{jr['seat']}` by-election ({jr['baseline_election_date']}):** {jr['winner_party']}/{jr['winner_coalition']} won {jr['winner_vote_share_perc']:.2f}% (majority {jr['majority_votes']:,} / {jr['majority_perc']:.2f}%, turnout {jr['voter_turnout_perc']:.2f}%), replacing its 2021 baseline ({jr['prn12_2021_majority_perc']:.2f}% majority, {jr['prn12_2021_turnout_perc']:.2f}% turnout).
   - **2016 uncontested seats:** {seats(df[df['prn11_2016_uncontested']])} — 2016–2021 swing and turnout change are N/A and excluded from averages.
   - **Single-saluran seats:** {seats(df[df['multi_saluran_pm_count'] == 0])} had no multi-saluran ordinary polling centres in 2021, so the youth-stream gap is N/A.
6. **Method limits:** For Tier 1–3 seats the average score is {f['score_total_mean']:.1f}, of which {f['margin_points_mean']:.1f} points come from the two 2021-margin terms ({comp_txt}) — the score is largely a margin ranking. Tier rules and score order can disagree: {seats(f['t2_below_t3'])} are Tier 2 but rank below the top Tier 3 seat; `{mt2['seat']}` is Tier 2 at {mt2['majority_perc']:.2f}% majority while {seats(f['safe_below_t2'], 'majority_perc', '.2f', '%')} are Safe with smaller majorities. The saluran youth gap is a crude half-split proxy.
7. **GE15 caveat:** federal contest, different candidates, PSB contested federally, postal votes excluded (~2% of votes).
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = build_dataset()
    df.to_csv(CSV_PATH, index=False)
    write_report(df)
    print(f"Wrote {CSV_PATH} ({len(df)} rows, {len(df.columns)} cols)")
    print(f"Wrote {REPORT_PATH}")
    print("\nTier summary:")
    print(df["marginality_tier"].value_counts().to_string())


if __name__ == "__main__":
    main()
