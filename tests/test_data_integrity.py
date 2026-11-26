"""Automated integrity and domain consistency tests for Sarawak marginal seats analysis."""

from __future__ import annotations

import json
from pathlib import Path
import geopandas as gpd
import pandas as pd
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
OUT_DIR = ROOT_DIR / "outputs"
CHART_DIR = OUT_DIR / "charts"

EXPECTED_CODES = {f"N.{i:02d}" for i in range(1, 83)}


def _norm_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.strftime("%Y-%m-%d")


@pytest.fixture(scope="module")
def raw_tables() -> dict[str, pd.DataFrame]:
    swk_b = pd.read_parquet(RAW_DIR / "headline_ballots_state_swk.parquet")
    swk_s = pd.read_parquet(RAW_DIR / "headline_stats_state_swk.parquet")
    prk_b = pd.read_parquet(RAW_DIR / "headline_ballots_byelections.parquet")
    prk_s = pd.read_parquet(RAW_DIR / "headline_stats_byelections.parquet")
    for df in (swk_b, swk_s, prk_b, prk_s):
        df["date"] = _norm_date(df["date"])
    return {
        "swk_b": swk_b,
        "swk_s": swk_s,
        "prk_b": prk_b,
        "prk_s": prk_s,
    }


@pytest.fixture(scope="module")
def output_df() -> pd.DataFrame:
    return pd.read_csv(OUT_DIR / "sarawak_2026_marginal_seats.csv")


def test_prn12_82_seats_present_in_raw_files(raw_tables: dict[str, pd.DataFrame]) -> None:
    st21 = raw_tables["swk_s"][raw_tables["swk_s"]["date"] == "2021-12-18"]
    bl21 = raw_tables["swk_b"][raw_tables["swk_b"]["date"] == "2021-12-18"]
    assert len(st21) == 82
    assert set(st21["seat"].str.slice(0, 4)) == EXPECTED_CODES
    assert set(bl21["seat"].str.slice(0, 4)) == EXPECTED_CODES


def test_candidate_votes_sum_equals_valid_votes(raw_tables: dict[str, pd.DataFrame]) -> None:
    st21 = raw_tables["swk_s"][raw_tables["swk_s"]["date"] == "2021-12-18"].set_index("seat")
    bl21_sum = (
        raw_tables["swk_b"][raw_tables["swk_b"]["date"] == "2021-12-18"]
        .groupby("seat")["votes"]
        .sum()
    )
    assert (bl21_sum.loc[st21.index] == st21["votes_valid"]).all()

    prk_s = raw_tables["prk_s"][
        (raw_tables["prk_s"]["state"] == "Sarawak")
        & (raw_tables["prk_s"]["date"] == "2023-11-04")
        & (raw_tables["prk_s"]["seat"] == "N.67 Jepak")
    ]
    prk_b = raw_tables["prk_b"][
        (raw_tables["prk_b"]["state"] == "Sarawak")
        & (raw_tables["prk_b"]["date"] == "2023-11-04")
        & (raw_tables["prk_b"]["seat"] == "N.67 Jepak")
    ]
    assert len(prk_s) == 1
    assert int(prk_b["votes"].sum()) == int(prk_s.iloc[0]["votes_valid"])


def test_no_duplicates_or_unexpected_nulls(raw_tables: dict[str, pd.DataFrame]) -> None:
    swk_b21 = raw_tables["swk_b"][raw_tables["swk_b"]["date"] == "2021-12-18"]
    swk_s21 = raw_tables["swk_s"][raw_tables["swk_s"]["date"] == "2021-12-18"]
    prk_b23 = raw_tables["prk_b"][
        (raw_tables["prk_b"]["state"] == "Sarawak") & (raw_tables["prk_b"]["date"] > "2021-12-18")
    ]
    prk_s23 = raw_tables["prk_s"][
        (raw_tables["prk_s"]["state"] == "Sarawak") & (raw_tables["prk_s"]["date"] > "2021-12-18")
    ]

    for b_df in (swk_b21, prk_b23):
        assert not b_df.duplicated(subset=["date", "seat", "candidate_uid"]).any()
        assert not b_df.duplicated(subset=["date", "seat", "name"]).any()
        assert b_df["votes"].notna().all()

    for s_df in (swk_s21, prk_s23):
        assert not s_df.duplicated(subset=["date", "seat"]).any()
        assert s_df[["votes_valid", "majority", "voters_total"]].notna().all().all()

    swk_s16 = raw_tables["swk_s"][raw_tables["swk_s"]["date"] == "2016-05-07"]
    null_turnout_seats = set(swk_s16[swk_s16["voter_turnout"].isna()]["seat"])
    null_maj_pct_seats = set(swk_s16[swk_s16["majority_perc"].isna()]["seat"])
    expected_uncontested = {"N.79 Bukit Kota", "N.82 Bukit Sari"}
    assert null_turnout_seats == expected_uncontested
    assert null_maj_pct_seats == expected_uncontested


def test_output_csv_invariants(output_df: pd.DataFrame, raw_tables: dict[str, pd.DataFrame]) -> None:
    assert len(output_df) == 82
    assert set(output_df["code_dun"]) == EXPECTED_CODES
    assert list(output_df["marginality_rank"]) == list(range(1, 83))

    jepak = output_df[output_df["code_dun"] == "N.67"].iloc[0]
    assert jepak["baseline_election_date"] == "2023-11-04"
    assert bool(jepak["is_prk_updated"]) is True

    scores = output_df["composite_marginality_score"]
    assert ((scores >= 0.0) & (scores <= 100.0)).all()
    assert scores.is_monotonic_decreasing

    assert (output_df["majority_votes"] == (output_df["winner_votes"] - output_df["runner_up_votes"])).all()
    expected_maj_pct = (output_df["majority_votes"] / output_df["votes_valid"]) * 100.0
    assert (output_df["majority_perc"] - expected_maj_pct).abs().max() < 1e-3
    assert (output_df["effective_num_candidates"] >= 1.0).all()

    # Tier classification invariants
    for _, r in output_df.iterrows():
        tier = r["marginality_tier"]
        is_t1 = (r["majority_perc"] < 5.0) or (r["majority_votes"] < 500)
        is_t2 = (not is_t1) and (
            (5.0 <= r["majority_perc"] < 10.0)
            or (r["winner_vote_share_perc"] < 50.0 and r["top2_opposition_combined_gap"] < 0)
        )
        trig = (
            (pd.notna(r["winning_share_swing_pp"]) and r["winning_share_swing_pp"] < 0)
            or (pd.notna(r["turnout_change_2016_to_2021_pp"]) and abs(r["turnout_change_2016_to_2021_pp"]) >= 10.0)
            or (pd.notna(r["saluran_youth_gap_pp"]) and abs(r["saluran_youth_gap_pp"]) >= 5.0)
            or (r["prn12_2021_turnout_perc"] < 55.0)
        )
        is_t3 = (not is_t1) and (not is_t2) and (10.0 <= r["majority_perc"] < 15.0) and trig
        if is_t1:
            assert tier == "Tier 1 (Razor-Thin)"
        elif is_t2:
            assert tier == "Tier 2 (Marginal)"
        elif is_t3:
            assert tier == "Tier 3 (Watchlist)"
        else:
            assert tier == "Safe"

    # PSB realignment flag matches 2021 PRN12 winner or runner-up
    bl21 = raw_tables["swk_b"][raw_tables["swk_b"]["date"] == "2021-12-18"]
    psb_top2_seats = set()
    for seat, grp in bl21.groupby("seat"):
        top2 = grp.sort_values("votes", ascending=False).head(2)
        if "PSB" in set(top2["party"]):
            psb_top2_seats.add(seat)
    flagged_seats = set(output_df[output_df["psb_realignment_flag"]]["seat"])
    assert flagged_seats == psb_top2_seats


def test_geojson_geometries_match_output(output_df: pd.DataFrame) -> None:
    gdf = gpd.read_file(RAW_DIR / "sarawak_2015_dun.geojson")
    assert len(gdf) == 82
    assert gdf.geometry.notna().all()
    assert not gdf.geometry.is_empty.any()
    assert set(gdf["code_dun"]) == set(output_df["code_dun"])


def test_ge15_dun_aggregation_and_shares(output_df: pd.DataFrame) -> None:
    ge15_b = pd.read_parquet(RAW_DIR / "ge15_ballots.parquet")
    ge15_s = pd.read_parquet(RAW_DIR / "ge15_stats.parquet")

    b_swk = ge15_b[ge15_b["state"] == "Sarawak"].copy()
    s_swk = ge15_s[ge15_s["state"] == "Sarawak"].copy()
    b_swk["tok"] = b_swk["dm"].str.split("/").str[1]
    s_swk["tok"] = s_swk["dm"].str.split("/").str[1]
    b_swk = b_swk[b_swk["tok"] != "00"].copy()
    s_swk = s_swk[s_swk["tok"] != "00"].copy()
    b_swk["code_dun"] = "N." + b_swk["tok"]
    s_swk["code_dun"] = "N." + s_swk["tok"]

    b_votes = b_swk.groupby("code_dun")["votes"].sum()
    s_valid = s_swk.groupby("code_dun")["votes_valid"].sum()

    assert set(b_votes.index) == EXPECTED_CODES
    assert set(s_valid.index) == EXPECTED_CODES
    assert (b_votes.loc[sorted(EXPECTED_CODES)] == s_valid.loc[sorted(EXPECTED_CODES)]).all()

    out_indexed = output_df.set_index("code_dun")
    assert (out_indexed.loc[sorted(EXPECTED_CODES), "ge15_dun_valid_votes"] == b_votes.loc[sorted(EXPECTED_CODES)]).all()

    share_sum = (
        output_df["ge15_dun_gps_share_perc"]
        + output_df["ge15_dun_ph_share_perc"]
        + output_df["ge15_dun_pn_share_perc"]
        + output_df["ge15_dun_psb_share_perc"]
        + output_df["ge15_dun_other_share_perc"]
    )
    assert (share_sum - 100.0).abs().max() <= 0.05


def test_political_context_overrides(output_df: pd.DataFrame) -> None:
    by_code = output_df.set_index("code_dun")["live_2026_status"]
    assert str(by_code.loc["N.53"]).startswith("Uncertain 2026")
    assert str(by_code.loc["N.33"]).startswith("Uncertain 2026")
    assert str(by_code.loc["N.81"]).startswith("GPS Consolidation")
    assert str(by_code.loc["N.11"]).startswith("Live 2026")


def test_deliverables_exist_and_nonempty() -> None:
    manifest_path = RAW_DIR / "download_manifest.json"
    report_path = OUT_DIR / "marginal_seats_report.md"
    pdf_path = OUT_DIR / "sarawak_2026_marginal_seats_report.pdf"
    charts = [
        CHART_DIR / "marginal_seats_ranked.png",
        CHART_DIR / "margin_vs_split_vote.png",
        CHART_DIR / "sarawak_marginal_map.png",
        CHART_DIR / "undi18_turnout_saluran.png",
        CHART_DIR / "ge15_crosscheck.png",
    ]
    assert manifest_path.exists() and manifest_path.stat().st_size > 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["file_count"] == 11
    assert report_path.exists() and report_path.stat().st_size > 0
    assert pdf_path.exists() and pdf_path.stat().st_size > 100_000
    assert pdf_path.read_bytes().startswith(b"%PDF-")
    for c in charts:
        assert c.exists() and c.stat().st_size > 0
