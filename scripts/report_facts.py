"""Data-derived facts shared by the Markdown and PDF reports (no hand-typed numbers)."""

from __future__ import annotations

import pandas as pd

CONTEXT_DATE = "26 Nov 2026"
NOMINATION_DATE = "28 Nov 2026"
POLLING_DATE = "12 Dec 2026"

TIER_ORDER = [
    "Tier 1 (Razor-Thin)",
    "Tier 2 (Marginal)",
    "Tier 3 (Watchlist)",
    "Safe",
]

REGION_ORDER = [
    ("Southern (Kuching-Samarahan-Serian-Sri Aman-Betong)", "Southern", "N.01–N.40"),
    ("Central (Sarikei-Sibu-Mukah-Kapit)", "Central", "N.41–N.66"),
    ("Northern (Bintulu-Miri-Limbang-Lawas)", "Northern", "N.67–N.82"),
]

SCORE_COMPONENTS = [
    ("score_margin_pct", "Baseline % majority", 40),
    ("score_margin_votes", "Raw-vote majority", 15),
    ("score_plurality_split", "Plurality & split-vote", 20),
    ("score_hist_swing", "2016→2021 swing", 15),
    ("score_volatility", "Turnout & saluran volatility", 10),
]

SIZE_BANDS = ["Small Rural (<10k)", "Medium (10k-20k)", "Large Urban (>=20k)"]

LIVE = "Live 2026"
UNCERTAIN = "Uncertain 2026"
CONSOLIDATED = "GPS Consolidation"


def by_status(sub: pd.DataFrame, prefix: str) -> pd.DataFrame:
    return sub[sub["live_2026_status"].str.startswith(prefix)]


def join_seats(
    sub: pd.DataFrame,
    wrap=lambda s: s,
    col: str | None = None,
    fmt: str = "",
    suffix: str = "",
) -> str:
    """Join seat names (optionally with a formatted value) into a readable list."""
    if sub.empty:
        return "none"
    items = []
    for _, r in sub.iterrows():
        label = wrap(r["seat"])
        if col is not None:
            label += f" ({format(r[col], fmt)}{suffix})"
        items.append(label)
    return ", ".join(items)


def compute_facts(df: pd.DataFrame) -> dict:
    df = df.sort_values("marginality_rank").reset_index(drop=True)
    non_safe = df[df["marginality_tier"] != "Safe"]
    f: dict = {"df": df, "non_safe": non_safe}

    f["tier_counts"] = df["marginality_tier"].value_counts().reindex(TIER_ORDER, fill_value=0)
    f["live"] = by_status(non_safe, LIVE)
    f["uncertain"] = by_status(non_safe, UNCERTAIN)
    f["consolidated"] = by_status(non_safe, CONSOLIDATED)
    f["plurality_count"] = int(df["is_plurality_win"].sum())
    f["top2_exceed_count"] = int(df["top2_exceed_winner"].sum())
    f["psb_flag_all"] = int(df["psb_realignment_flag"].sum())
    f["psb_flag_nonsafe"] = int(non_safe["psb_realignment_flag"].sum())

    f["worst_split"] = df[df["top2_exceed_winner"]].sort_values("top2_opposition_combined_gap").head(2)
    f["low_share_split"] = (
        df[df["is_plurality_win"] & df["top2_exceed_winner"]].sort_values("winner_vote_share_perc").head(4)
    )
    f["tier1"] = df[df["marginality_tier"] == "Tier 1 (Razor-Thin)"].sort_values("majority_perc")
    f["closest"] = df.loc[df["majority_perc"].idxmin()]

    regions = []
    for name, short, rng in REGION_ORDER:
        g = df[df["region"] == name]
        ns = g[g["marginality_tier"] != "Safe"]
        regions.append(
            {
                "name": name,
                "short": short,
                "range": rng,
                "seats": len(g),
                "t1": int((g["marginality_tier"] == TIER_ORDER[0]).sum()),
                "t2": int((g["marginality_tier"] == TIER_ORDER[1]).sum()),
                "t3": int((g["marginality_tier"] == TIER_ORDER[2]).sum()),
                "safe": int((g["marginality_tier"] == "Safe").sum()),
                "nonsafe": len(ns),
                "nonsafe_share": 100.0 * len(ns) / len(g),
                "live": by_status(ns, LIVE),
                "uncertain": by_status(ns, UNCERTAIN),
                "consolidated": by_status(ns, CONSOLIDATED),
                "median_maj": float(g["majority_perc"].median()),
                "median_roll": float(g["undi18_voter_growth_perc"].median()),
                "ge15_trailed": g[g["ge15_gps_trailed"]],
            }
        )
    f["regions"] = regions
    f["densest_region"] = max(regions, key=lambda r: r["nonsafe_share"])

    f["mean_t16"] = float(df["prn11_2016_turnout_perc"].mean())
    f["n_contested_2016"] = int(df["prn11_2016_turnout_perc"].notna().sum())
    f["mean_t21"] = float(df["prn12_2021_turnout_perc"].mean())
    f["mean_t_chg"] = float(df["turnout_change_2016_to_2021_pp"].mean())
    f["worst_turnout_drops"] = non_safe.sort_values("turnout_change_2016_to_2021_pp").head(4)

    f["med_roll"] = float(df["undi18_voter_growth_perc"].median())
    f["min_roll"] = df.loc[df["undi18_voter_growth_perc"].idxmin()]
    f["max_roll"] = df.loc[df["undi18_voter_growth_perc"].idxmax()]
    f["top_roll_nonsafe"] = non_safe.sort_values("undi18_voter_growth_perc", ascending=False).head(4)

    ys = non_safe.dropna(subset=["saluran_youth_gap_pp"])
    f["youth_neg"] = ys.sort_values("saluran_youth_gap_pp").head(3)
    f["youth_pos"] = ys.sort_values("saluran_youth_gap_pp", ascending=False).head(1)

    f["size_counts"] = {b: int((df["electorate_size_band"] == b).sum()) for b in SIZE_BANDS}
    f["size_ns_counts"] = {b: int((non_safe["electorate_size_band"] == b).sum()) for b in SIZE_BANDS}
    small = non_safe[non_safe["electorate_size_band"] == SIZE_BANDS[0]].sort_values("voters_total").head(2).copy()
    small["vote500_perc"] = 500.0 / small["votes_valid"] * 100.0
    f["small_examples"] = small

    f["batu_lintang"] = df[df["code_dun"] == "N.11"].iloc[0]
    f["psb_third"] = non_safe[
        (non_safe["psb_2021_role"] == "Third-place") & (non_safe["psb_2021_vote_share_perc"] >= 10.0)
    ].sort_values("psb_2021_vote_share_perc", ascending=False)
    f["krian"] = df[df["code_dun"] == "N.39"].iloc[0]
    f["overrides"] = by_status(df, UNCERTAIN)

    f["score_means"] = {c: float(non_safe[c].mean()) for c, _, _ in SCORE_COMPONENTS}
    f["score_total_mean"] = float(non_safe["composite_marginality_score"].mean())
    f["margin_points_mean"] = f["score_means"]["score_margin_pct"] + f["score_means"]["score_margin_votes"]
    t3_best_rank = non_safe[non_safe["marginality_tier"] == TIER_ORDER[2]]["marginality_rank"].min()
    f["t2_below_t3"] = non_safe[
        (non_safe["marginality_tier"] == TIER_ORDER[1]) & (non_safe["marginality_rank"] > t3_best_rank)
    ]
    t2 = df[df["marginality_tier"] == TIER_ORDER[1]]
    f["max_t2"] = t2.loc[t2["majority_perc"].idxmax()]
    f["safe_below_t2"] = df[
        (df["marginality_tier"] == "Safe") & (df["majority_perc"] < f["max_t2"]["majority_perc"])
    ].sort_values("majority_perc")

    f["ge15_trailed"] = df[df["ge15_gps_trailed"]].sort_values("ge15_dun_gps_margin_pp")
    f["ge15_close_led"] = df[df["ge15_competitive"] & ~df["ge15_gps_trailed"]].sort_values("ge15_dun_gps_margin_pp")
    f["ge15_watch"] = df[df["ge15_gps_trailed"] | df["ge15_competitive"]].sort_values("ge15_dun_gps_margin_pp")
    f["ge15_safe_flagged"] = df[df["ge15_flags_safe_seat"]].sort_values("ge15_dun_gps_margin_pp")
    f["ge15_safe_trailed"] = df[df["ge15_flags_safe_seat"] & df["ge15_gps_trailed"]].sort_values("ge15_dun_gps_margin_pp")
    f["ge15_safe_close"] = df[df["ge15_flags_safe_seat"] & ~df["ge15_gps_trailed"]].sort_values("ge15_dun_gps_margin_pp")
    f["ge15_nonsafe_trailed"] = non_safe[non_safe["ge15_gps_trailed"]]
    f["ge15_lead_counts"] = df["ge15_dun_leading_bloc"].value_counts().to_dict()

    f["jepak"] = df[df["is_prk_updated"]].iloc[0]
    return f
