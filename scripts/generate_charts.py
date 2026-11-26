"""Generate publication-quality PNG charts for Sarawak 2026 marginal DUN seats."""

from __future__ import annotations

from pathlib import Path
import geopandas as gpd
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
OUT_DIR = ROOT_DIR / "outputs"
CHART_DIR = OUT_DIR / "charts"
CSV_PATH = OUT_DIR / "sarawak_2026_marginal_seats.csv"
GEO_PATH = RAW_DIR / "sarawak_2015_dun.geojson"

TIER_COLORS = {
    "Tier 1 (Razor-Thin)": "#c0392b",
    "Tier 2 (Marginal)": "#e67e22",
    "Tier 3 (Watchlist)": "#f1c40f",
    "Safe": "#d5dce4",
}

TIER_SHORT = {
    "Tier 1 (Razor-Thin)": "T1",
    "Tier 2 (Marginal)": "T2",
    "Tier 3 (Watchlist)": "T3",
    "Safe": "Safe",
}


def _bloc_matchup(row: pd.Series) -> str:
    wc = row["winner_coalition"]
    rc = row["runner_up_coalition"]
    wp = row["winner_party"]
    rp = row["runner_up_party"]
    if wc == "GPS" and rc == "PH":
        return "GPS vs PH"
    if wc == "GPS" and rp == "PSB":
        return "GPS vs PSB"
    if wc == "GPS":
        return "GPS vs Ind/Other"
    if wc == "PH" and rc == "GPS":
        return "PH vs GPS"
    if wp == "PSB" and rc == "GPS":
        return "PSB vs GPS"
    return "Other"


def plot_marginal_seats_ranked(df: pd.DataFrame) -> None:
    top20 = df.sort_values(["majority_perc", "majority_votes"]).head(20).copy()
    top20["matchup"] = top20.apply(_bloc_matchup, axis=1)

    matchup_colors = {
        "GPS vs PH": "#1f77b4",
        "GPS vs PSB": "#e67e22",
        "GPS vs Ind/Other": "#16a085",
        "PH vs GPS": "#c0392b",
        "PSB vs GPS": "#8e44ad",
        "Other": "#7f8c8d",
    }

    plt.rcParams.update({"font.sans-serif": "DejaVu Sans", "axes.edgecolor": "#cccccc"})
    fig, ax = plt.subplots(figsize=(13.5, 9.2), dpi=300)

    y_pos = list(range(len(top20)))
    colors = [matchup_colors[m] for m in top20["matchup"]]
    ax.barh(y_pos, top20["majority_perc"], color=colors, height=0.72, edgecolor="none", zorder=3)

    ax.axvline(5.0, color="#c0392b", linestyle="--", linewidth=1.1, alpha=0.75, zorder=2)
    ax.axvline(10.0, color="#e67e22", linestyle="--", linewidth=1.1, alpha=0.75, zorder=2)
    ax.axvline(15.0, color="#b7950b", linestyle=":", linewidth=1.1, alpha=0.75, zorder=2)

    ax.text(5.15, -0.75, "5% (Tier 1)", color="#c0392b", fontsize=8.5, fontweight="bold")
    ax.text(10.15, -0.75, "10% (Tier 2)", color="#d35400", fontsize=8.5, fontweight="bold")
    ax.text(15.15, -0.75, "15% (Tier 3)", color="#9a7d0a", fontsize=8.5, fontweight="bold")

    for i, (_, row) in enumerate(top20.iterrows()):
        t_badge = TIER_SHORT[row["marginality_tier"]]
        if row["seat"] == "N.11 Batu Lintang":
            psb_tag = " [Ex-PSB Ind]"
        elif str(row["live_2026_status"]).startswith("Uncertain 2026"):
            psb_tag = " [Left PDP]"
        elif row["psb_realignment_flag"]:
            psb_tag = " [PSB→PDP]"
        else:
            psb_tag = ""
        label = (
            f"{row['majority_perc']:.2f}% ({int(row['majority_votes']):,})  |  "
            f"{row['winner_party']} vs {row['runner_up_party']}  [{t_badge}]{psb_tag}"
        )
        ax.text(
            row["majority_perc"] + 0.35,
            i,
            label,
            va="center",
            ha="left",
            fontsize=8.6,
            color="#222222",
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(top20["seat"], fontsize=9.5, fontweight="normal")
    ax.invert_yaxis()
    ax.set_xlim(0, 32.5)
    ax.set_ylim(len(top20) - 0.35, -1.15)
    ax.set_xlabel("2021 Majority (% of Valid Votes)", fontsize=10.5, fontweight="bold")
    ax.set_title(
        "Sarawak DUN 2026 Watchlist: 20 Tightest Seats by 2021 Majority Margin",
        fontsize=13.5,
        fontweight="bold",
        pad=14,
        loc="left",
    )
    ax.grid(axis="x", linestyle="-", alpha=0.2, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    present_matchups = [m for m in matchup_colors if m in set(top20["matchup"])]
    handles = [
        mpatches.Patch(color=matchup_colors[m], label=m) for m in present_matchups
    ]
    ax.legend(
        handles=handles,
        title="2021 Winner vs Runner-Up",
        loc="lower right",
        frameon=True,
        facecolor="white",
        edgecolor="#dddddd",
        fontsize=9,
        title_fontsize=9.5,
    )

    fig.text(
        0.01,
        0.01,
        "Source: electiondata.my (2021 Sarawak SE-12; N.67 Jepak updated with 2023 PRK). "
        "[PSB→PDP]: 2021 PSB winner/runner-up seat affected by PSB's 2024 merger into PDP. "
        "[Left PDP]: ex-PSB incumbent quit PDP in Nov 2026.",
        fontsize=8,
        color="#555555",
    )
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(CHART_DIR / "marginal_seats_ranked.png", dpi=300)
    plt.close(fig)


def plot_margin_vs_split_vote(df: pd.DataFrame) -> None:
    plt.rcParams.update({"font.sans-serif": "DejaVu Sans", "axes.edgecolor": "#cccccc"})
    fig, ax = plt.subplots(figsize=(12.8, 8.2), dpi=300)

    ax.axhline(50.0, color="#444444", linestyle="--", linewidth=1.1, alpha=0.75, zorder=1)
    ax.axvline(5.0, color="#c0392b", linestyle="--", linewidth=1.0, alpha=0.55, zorder=1)
    ax.axvline(10.0, color="#e67e22", linestyle="--", linewidth=1.0, alpha=0.55, zorder=1)
    ax.axvline(15.0, color="#b7950b", linestyle=":", linewidth=1.0, alpha=0.55, zorder=1)

    ax.axhspan(20, 50, xmin=0, xmax=1, color="#fdf2e9", alpha=0.35, zorder=0)
    ax.text(85.5, 50.8, "50% Majority Line (Plurality Wins Below)", ha="right", fontsize=8.5, color="#444444", style="italic")
    ax.text(4.8, 94.5, "5%", ha="right", fontsize=8.5, color="#c0392b", fontweight="bold")
    ax.text(9.8, 94.5, "10%", ha="right", fontsize=8.5, color="#d35400", fontweight="bold")
    ax.text(14.8, 94.5, "15%", ha="right", fontsize=8.5, color="#9a7d0a", fontweight="bold")

    tier_order = [
        "Safe",
        "Tier 3 (Watchlist)",
        "Tier 2 (Marginal)",
        "Tier 1 (Razor-Thin)",
    ]
    scatter_colors = {
        "Tier 1 (Razor-Thin)": "#c0392b",
        "Tier 2 (Marginal)": "#e67e22",
        "Tier 3 (Watchlist)": "#d4ac0d",
        "Safe": "#85929e",
    }

    sizes = 45 + (df["voters_total"] / df["voters_total"].max()) * 155
    for tier in tier_order:
        sub = df[df["marginality_tier"] == tier]
        sub_sizes = sizes.loc[sub.index]
        alpha = 0.55 if tier == "Safe" else 0.90
        ax.scatter(
            sub["majority_perc"],
            sub["winner_vote_share_perc"],
            s=sub_sizes,
            c=scatter_colors[tier],
            alpha=alpha,
            edgecolors="#ffffff",
            linewidths=0.7,
            label=f"{tier} ({len(sub)})",
            zorder=3 if tier == "Safe" else 4,
        )

    # Dark ring for plurality wins where 2nd + 3rd exceed winner
    vuln = df[df["is_plurality_win"] & df["top2_exceed_winner"]]
    ax.scatter(
        vuln["majority_perc"],
        vuln["winner_vote_share_perc"],
        s=sizes.loc[vuln.index] + 35,
        facecolors="none",
        edgecolors="#111111",
        linewidths=1.7,
        label=f"Plurality win & 2nd+3rd > winner ({len(vuln)})",
        zorder=5,
    )

    # Curated non-overlapping data-space coordinates for all 18 Tier 1-3 labels
    label_coords = {
        "N.32": (-0.3, 57.5),
        "N.49": (0.2, 62.2),
        "N.53": (2.8, 66.8),
        "N.48": (5.5, 71.4),
        "N.80": (9.5, 76.0),
        "N.81": (13.8, 80.8),
        "N.09": (18.2, 65.5),
        "N.74": (19.6, 59.8),
        "N.34": (17.8, 54.5),
        "N.54": (4.0, 26.0),
        "N.68": (4.4, 29.8),
        "N.11": (11.5, 31.8),
        "N.51": (14.8, 27.6),
        "N.10": (17.2, 35.4),
        "N.47": (20.8, 38.6),
        "N.39": (24.0, 41.8),
        "N.12": (24.5, 33.4),
        "N.33": (31.5, 41.5),
    }

    non_safe = df[df["marginality_tier"] != "Safe"]
    for _, r in non_safe.iterrows():
        code = r["code_dun"]
        lx, ly = label_coords[code]
        ax.annotate(
            f"{code} {r['seat'].split(' ', 1)[1]}",
            xy=(r["majority_perc"], r["winner_vote_share_perc"]),
            xytext=(lx, ly),
            textcoords="data",
            fontsize=7.8,
            fontweight="bold",
            color="#1c1c1c",
            ha="left",
            va="center",
            arrowprops={
                "arrowstyle": "-",
                "color": "#666666",
                "lw": 0.75,
                "shrinkA": 0,
                "shrinkB": 3,
            },
            zorder=6,
        )

    # Label two Safe plurality outliers for context (Opar & Dudong)
    for code, lx, ly in [("N.01", 23.2, 46.8), ("N.52", 30.8, 47.0)]:
        r = df[df["code_dun"] == code].iloc[0]
        ax.annotate(
            f"{code} {r['seat'].split(' ', 1)[1]}",
            xy=(r["majority_perc"], r["winner_vote_share_perc"]),
            xytext=(lx, ly),
            textcoords="data",
            fontsize=7.4,
            color="#555555",
            ha="left",
            va="center",
        )

    ax.set_xlim(-1.5, 88.0)
    ax.set_ylim(24.0, 97.0)
    ax.set_xlabel("Baseline Majority Margin (% of Valid Votes)", fontsize=10.5, fontweight="bold")
    ax.set_ylabel("Winner Vote Share (% of Valid Votes)", fontsize=10.5, fontweight="bold")
    ax.set_title(
        "Vote-Splitting Vulnerability: Majority Margin vs. Winner Vote Share (82 Sarawak DUNs)",
        fontsize=13.2,
        fontweight="bold",
        pad=12,
        loc="left",
    )
    ax.grid(True, linestyle="-", alpha=0.2, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(
        loc="lower right",
        frameon=True,
        facecolor="white",
        edgecolor="#dddddd",
        fontsize=9,
    )
    fig.text(
        0.01,
        0.01,
        "Marker size scales with registered voters (baseline election). Highlighted seats below 50% had combined 2nd + 3rd votes exceeding the winner.",
        fontsize=8,
        color="#555555",
    )
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(CHART_DIR / "margin_vs_split_vote.png", dpi=300)
    plt.close(fig)


def plot_sarawak_map(df: pd.DataFrame) -> None:
    gdf = gpd.read_file(GEO_PATH).merge(df, on="code_dun", how="left")

    plt.rcParams.update({"font.sans-serif": "DejaVu Sans"})
    fig = plt.figure(figsize=(15.5, 10.2), dpi=300)
    ax = fig.add_axes([0.03, 0.06, 0.94, 0.87])

    tier_order = [
        "Safe",
        "Tier 3 (Watchlist)",
        "Tier 2 (Marginal)",
        "Tier 1 (Razor-Thin)",
    ]
    for tier in tier_order:
        sub = gdf[gdf["marginality_tier"] == tier]
        sub.plot(
            ax=ax,
            color=TIER_COLORS[tier],
            edgecolor="#4a4a4a",
            linewidth=0.45,
            zorder=2 if tier == "Safe" else 3,
        )

    ax.set_xlim(109.25, 115.95)
    ax.set_ylim(0.65, 5.20)
    ax.set_axis_off()
    ax.set_title(
        "Sarawak 2026 DUN Marginality Map (82 Seats by Historical Margin & Vulnerability Tier)",
        fontsize=14.5,
        fontweight="bold",
        loc="left",
        pad=10,
    )

    # Bounding boxes on main map for Kuching & Sibu insets
    k_box = (110.17, 1.36, 110.43, 1.65)
    s_box = (111.60, 2.02, 112.18, 2.73)
    for box, tag in [(k_box, "A"), (s_box, "B")]:
        rect = mpatches.Rectangle(
            (box[0], box[1]),
            box[2] - box[0],
            box[3] - box[1],
            fill=False,
            edgecolor="#111111",
            linewidth=1.3,
            linestyle="-",
            zorder=5,
        )
        ax.add_patch(rect)
        ax.text(
            box[0],
            box[3] + 0.05,
            tag,
            fontsize=8.5,
            fontweight="bold",
            color="#111111",
            path_effects=[pe.withStroke(linewidth=2.5, foreground="white")],
            zorder=6,
        )

    # Main map labels for non-Kuching/non-Sibu Tier 1-3 seats
    main_label_offsets = {
        "N.32": (-0.25, -0.22),
        "N.33": (0.18, -0.20),
        "N.34": (0.35, -0.05),
        "N.39": (-0.30, 0.16),
        "N.47": (-0.05, -0.25),
        "N.48": (0.28, -0.22),
        "N.49": (0.30, 0.12),
        "N.68": (-0.05, 0.34),
        "N.74": (-0.35, 0.20),
        "N.80": (-0.35, 0.15),
        "N.81": (0.22, 0.16),
    }
    for code, (dx, dy) in main_label_offsets.items():
        row = gdf[gdf["code_dun"] == code].iloc[0]
        pt = row.geometry.representative_point()
        ax.annotate(
            f"{code}\n({row['majority_perc']:.1f}%)",
            xy=(pt.x, pt.y),
            xytext=(pt.x + dx, pt.y + dy),
            fontsize=7.6,
            fontweight="bold",
            color="#111111",
            ha="center",
            va="center",
            bbox={
                "boxstyle": "round,pad=0.18",
                "facecolor": "white",
                "edgecolor": TIER_COLORS[row["marginality_tier"]],
                "alpha": 0.92,
                "lw": 1.0,
            },
            arrowprops={"arrowstyle": "-", "color": "#222222", "lw": 0.85},
            zorder=7,
        )

    # Inset A: Kuching Urban Cluster (N.06-N.14) in open northwest space
    ax_k = fig.add_axes([0.04, 0.49, 0.25, 0.36])
    for tier in tier_order:
        sub = gdf[gdf["marginality_tier"] == tier]
        sub.plot(ax=ax_k, color=TIER_COLORS[tier], edgecolor="#333333", linewidth=0.65)
    ax_k.set_xlim(110.22, 110.425)
    ax_k.set_ylim(1.42, 1.62)
    ax_k.set_xticks([])
    ax_k.set_yticks([])
    ax_k.set_xlabel("")
    ax_k.set_ylabel("")
    ax_k.set_title("A. Kuching Urban Cluster", fontsize=9.8, fontweight="bold", loc="left", pad=4)
    for spine in ax_k.spines.values():
        spine.set_edgecolor("#222222")
        spine.set_linewidth(1.1)

    kuching_label_pos = {
        "N.09": (110.352, 1.576),
        "N.10": (110.398, 1.552),
        "N.11": (110.348, 1.522),
        "N.12": (110.364, 1.474),
        "N.06": (110.265, 1.575),
        "N.07": (110.350, 1.602),
        "N.08": (110.305, 1.542),
        "N.13": (110.295, 1.448),
        "N.14": (110.258, 1.498),
    }
    for code, (lx, ly) in kuching_label_pos.items():
        r = gdf[gdf["code_dun"] == code].iloc[0]
        is_target = r["marginality_tier"] != "Safe"
        pt = r.geometry.representative_point()
        if is_target:
            ax_k.annotate(
                f"{code}\n{r['majority_perc']:.1f}%",
                xy=(pt.x, pt.y),
                xytext=(lx, ly),
                fontsize=7.1,
                fontweight="bold",
                ha="center",
                va="center",
                color="#111111",
                bbox={"boxstyle": "round,pad=0.13", "facecolor": "white", "edgecolor": "#333333", "alpha": 0.92, "lw": 0.7},
                arrowprops={"arrowstyle": "-", "color": "#222222", "lw": 0.65} if code in ("N.09", "N.10") else None,
            )
        else:
            ax_k.text(
                lx,
                ly,
                code,
                fontsize=6.6,
                ha="center",
                va="center",
                color="#444444",
                path_effects=[pe.withStroke(linewidth=2.0, foreground="white")],
            )

    # Inset B: Sibu Urban Cluster (N.51-N.55)
    ax_s = fig.add_axes([0.31, 0.56, 0.23, 0.30])
    for tier in tier_order:
        sub = gdf[gdf["marginality_tier"] == tier]
        sub.plot(ax=ax_s, color=TIER_COLORS[tier], edgecolor="#333333", linewidth=0.65)
    ax_s.set_xlim(111.61, 112.17)
    ax_s.set_ylim(2.03, 2.72)
    ax_s.set_xticks([])
    ax_s.set_yticks([])
    ax_s.set_xlabel("")
    ax_s.set_ylabel("")
    ax_s.set_title("B. Sibu Cluster (N.51–N.55)", fontsize=9.8, fontweight="bold", loc="left", pad=4)
    for spine in ax_s.spines.values():
        spine.set_edgecolor("#222222")
        spine.set_linewidth(1.1)

    sibu_label_pos = {
        "N.54": (111.71, 2.34),
        "N.51": (111.73, 2.18),
        "N.53": (111.83, 2.59),
        "N.52": (111.98, 2.13),
        "N.55": (112.03, 2.34),
    }
    for code, (lx, ly) in sibu_label_pos.items():
        r = gdf[gdf["code_dun"] == code].iloc[0]
        pt = r.geometry.representative_point()
        is_target = r["marginality_tier"] != "Safe"
        if is_target:
            ax_s.annotate(
                f"{code} ({r['majority_perc']:.1f}%)",
                xy=(pt.x, pt.y),
                xytext=(lx, ly),
                fontsize=7.3,
                fontweight="bold",
                ha="center",
                va="center",
                color="#111111",
                bbox={"boxstyle": "round,pad=0.14", "facecolor": "white", "edgecolor": "#333333", "alpha": 0.9, "lw": 0.7},
                arrowprops={"arrowstyle": "-", "color": "#222222", "lw": 0.7},
            )
        else:
            ax_s.text(
                lx,
                ly,
                code,
                fontsize=6.8,
                ha="center",
                va="center",
                color="#444444",
                path_effects=[pe.withStroke(linewidth=2.0, foreground="white")],
            )

    # Legend in southeast corner
    tier_counts = df["marginality_tier"].value_counts()
    legend_handles = [
        mpatches.Patch(
            facecolor=TIER_COLORS[t],
            edgecolor="#4a4a4a",
            label=f"{t}: {int(tier_counts.get(t, 0))} seats",
        )
        for t in [
            "Tier 1 (Razor-Thin)",
            "Tier 2 (Marginal)",
            "Tier 3 (Watchlist)",
            "Safe",
        ]
    ]
    ax.legend(
        handles=legend_handles,
        title="Marginality Tier (2021/PRK Baseline)",
        loc="lower right",
        bbox_to_anchor=(0.98, 0.04),
        frameon=True,
        facecolor="white",
        edgecolor="#cccccc",
        fontsize=9.5,
        title_fontsize=10,
    )

    fig.text(
        0.03,
        0.02,
        "Geometry: electiondata.my 2015 Sarawak DUN delimitation (82 gazetted seats, N.01–N.82). "
        "GPS-consolidation scenario (PSB→PDP): "
        + ", ".join(df[df["live_2026_status"].str.startswith("GPS Consolidation")]["code_dun"].sort_values())
        + ". Uncertain (ex-PSB incumbent left PDP, Nov 2026): "
        + ", ".join(df[df["live_2026_status"].str.startswith("Uncertain 2026")]["code_dun"].sort_values())
        + ".",
        fontsize=8.2,
        color="#555555",
    )
    fig.savefig(CHART_DIR / "sarawak_marginal_map.png", dpi=300)
    plt.close(fig)


def plot_undi18_turnout_saluran(df: pd.DataFrame) -> None:
    sub = df[df["marginality_tier"] != "Safe"].sort_values("marginality_rank").copy()
    y_pos = list(range(len(sub)))
    y_labels = [f"#{int(r['marginality_rank'])} {r['seat']}" for _, r in sub.iterrows()]
    state_med_growth = float(df["undi18_voter_growth_perc"].median())

    plt.rcParams.update({"font.sans-serif": "DejaVu Sans", "axes.edgecolor": "#cccccc"})
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 7.6), sharey=True, dpi=300)
    fig.subplots_adjust(left=0.16, right=0.98, top=0.81, bottom=0.11, wspace=0.12)

    # Panel 1: Undi18 voter-roll growth (%)
    ax1 = axes[0]
    p1_colors = [
        "#c0392b" if str(s).startswith("Live 2026")
        else "#8e44ad" if str(s).startswith("Uncertain 2026")
        else "#5d6d7e"
        for s in sub["live_2026_status"]
    ]
    g_vals = sub["undi18_voter_growth_perc"].tolist()
    ax1.barh(y_pos, g_vals, color=p1_colors, height=0.68, zorder=3)
    ax1.axvline(state_med_growth, color="#1f2d3d", linestyle="--", linewidth=1.1, zorder=2)
    ax1.text(
        state_med_growth + 1.0,
        -0.72,
        f"Median +{state_med_growth:.1f}%",
        fontsize=7.6,
        color="#1f2d3d",
        fontweight="bold",
        va="bottom",
        ha="left",
    )
    for i, val in enumerate(g_vals):
        ax1.text(
            val + 1.2,
            i,
            f"+{val:.1f}%",
            va="center",
            ha="left",
            fontsize=7.8,
            color="#222222",
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4, "alpha": 0.85},
            zorder=5,
        )
    ax1.set_xlim(0, max(g_vals) + 17)
    ax1.set_title("Voter-Roll Growth (%)\n(Undi18 + AVR, Dec 2021 → Nov 2022)", fontsize=10, fontweight="bold", pad=8)
    ax1.set_xlabel("Voter Roll Expansion (%)", fontsize=9, fontweight="bold")

    # Panel 2: 2016 -> 2021 turnout shift (pp)
    ax2 = axes[1]
    t_vals = sub["turnout_change_2016_to_2021_pp"].tolist()
    p2_colors = ["#2980b9" if v < 0 else "#27ae60" for v in t_vals]
    ax2.barh(y_pos, t_vals, color=p2_colors, height=0.68, zorder=3)
    ax2.axvline(0.0, color="#333333", linewidth=0.9, zorder=4)
    ax2.axvline(-10.0, color="#1f618d", linestyle="--", linewidth=1.0, alpha=0.85, zorder=2)
    ax2.text(
        -10.4,
        -0.72,
        "-10 pp flag",
        fontsize=7.6,
        color="#1f618d",
        fontweight="bold",
        ha="right",
        va="bottom",
    )
    for i, val in enumerate(t_vals):
        if val < 0:
            ax2.text(
                val - 0.6,
                i,
                f"{val:+.1f}",
                va="center",
                ha="right",
                fontsize=7.8,
                color="#222222",
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4, "alpha": 0.85},
                zorder=5,
            )
        else:
            ax2.text(val + 0.6, i, f"{val:+.1f}", va="center", ha="left", fontsize=7.8, color="#222222")
    t_min, t_max = min(t_vals), max(t_vals)
    ax2.set_xlim(min(t_min - 5.5, -15.0), max(t_max + 4.5, 4.0))
    ax2.set_title("2016 → 2021 Turnout Shift (pp)\n(COVID-Era Suppression)", fontsize=10, fontweight="bold", pad=8)
    ax2.set_xlabel("Turnout Change (percentage points)", fontsize=9, fontweight="bold")

    # Panel 3: Saluran youth-stream gap (pp)
    ax3 = axes[2]
    s_vals = sub["saluran_youth_gap_pp"].tolist()
    p3_colors = ["#d35400" if v < 0 else "#16a085" for v in s_vals]
    ax3.barh(y_pos, s_vals, color=p3_colors, height=0.68, zorder=3)
    ax3.axvline(0.0, color="#333333", linewidth=0.9, zorder=4)
    for i, val in enumerate(s_vals):
        if val < 0:
            ax3.text(val - 0.3, i, f"{val:+.1f}", va="center", ha="right", fontsize=7.8, color="#222222")
        else:
            ax3.text(val + 0.3, i, f"{val:+.1f}", va="center", ha="left", fontsize=7.8, color="#222222")
    s_min, s_max = min(s_vals), max(s_vals)
    ax3.set_xlim(s_min - 2.6, s_max + 2.6)
    ax3.set_title("Saluran Youth Gap (pp)\n(Younger − Older Winner Share)", fontsize=10, fontweight="bold", pad=8)
    ax3.set_xlabel("Winner Share Gap (pp)", fontsize=9, fontweight="bold")

    for ax in axes:
        ax.grid(axis="x", linestyle="-", alpha=0.2, zorder=0)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(axis="x", labelsize=8.5)

    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(y_labels, fontsize=8.8, fontweight="normal")
    ax1.invert_yaxis()
    ax1.set_ylim(len(sub) - 0.3, -1.05)

    legend_handles = [
        mpatches.Patch(color="#c0392b", label="Live 2026 Competitive"),
        mpatches.Patch(color="#5d6d7e", label="GPS Consolidation (PSB→PDP)"),
        mpatches.Patch(color="#8e44ad", label="Uncertain (Left PDP)"),
        mpatches.Patch(color="#2980b9", label="Turnout Drop"),
        mpatches.Patch(color="#27ae60", label="Turnout Gain"),
        mpatches.Patch(color="#d35400", label="Weaker Youth Share"),
        mpatches.Patch(color="#16a085", label="Stronger Youth Share"),
    ]
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.56, 0.905),
        ncol=7,
        frameon=False,
        fontsize=7.3,
    )

    fig.suptitle(
        "Demographic & Turnout Volatility Across the 18 Tier 1–3 Seats",
        fontsize=13.5,
        fontweight="bold",
        x=0.03,
        y=0.97,
        ha="left",
    )
    fig.text(
        0.03,
        0.925,
        "Ordered by marginality rank (#1 top). Roll growth: GE15 non-postal DUN roll vs 2021 (Undi18 + automatic registration). "
        "Youth gap: winner share in younger minus older saluran streams.",
        fontsize=8.4,
        color="#444444",
    )
    fig.text(
        0.03,
        0.02,
        "Source: electiondata.my (2016 SE-11, 2021 SE-12 Headline & Saluran, 2022 GE15 Saluran). Excludes Undi Pos and Undi Awal.",
        fontsize=8,
        color="#555555",
    )

    fig.savefig(CHART_DIR / "undi18_turnout_saluran.png", dpi=300)
    plt.close(fig)


def plot_ge15_crosscheck(df: pd.DataFrame) -> None:
    from adjustText import adjust_text

    plt.rcParams.update({"font.sans-serif": "DejaVu Sans", "axes.edgecolor": "#cccccc"})
    fig, ax = plt.subplots(figsize=(12.8, 8.4), dpi=300)
    colors = {
        "Tier 1 (Razor-Thin)": "#c0392b",
        "Tier 2 (Marginal)": "#e67e22",
        "Tier 3 (Watchlist)": "#d4ac0d",
        "Safe": "#85929e",
    }
    x_min = min(df["prn12_gps_margin_pp"].min(), -20) - 6
    x_max = df["prn12_gps_margin_pp"].max() + 6
    y_min = df["ge15_dun_gps_margin_pp"].min() - 6
    y_max = df["ge15_dun_gps_margin_pp"].max() + 6
    ax.axhspan(-10, 10, color="#fdebd0", alpha=0.55, zorder=0)
    ax.axhline(0, color="#333333", linewidth=1.0, zorder=1)
    ax.axvline(0, color="#333333", linewidth=1.0, zorder=1)

    for tier in ["Safe", "Tier 3 (Watchlist)", "Tier 2 (Marginal)", "Tier 1 (Razor-Thin)"]:
        sub = df[df["marginality_tier"] == tier]
        ax.scatter(
            sub["prn12_gps_margin_pp"],
            sub["ge15_dun_gps_margin_pp"],
            s=70 if tier != "Safe" else 50,
            c=colors[tier],
            alpha=0.92 if tier != "Safe" else 0.6,
            edgecolors="white",
            linewidths=0.7,
            label=f"{tier} ({len(sub)})",
            zorder=3,
        )

    to_label = df[(df["marginality_tier"] != "Safe") | df["ge15_gps_trailed"]]
    texts = [
        ax.text(
            r["prn12_gps_margin_pp"],
            r["ge15_dun_gps_margin_pp"],
            f"{r['code_dun']} {r['seat'].split(' ', 1)[1]}",
            fontsize=7.2,
            fontweight="bold" if r["marginality_tier"] != "Safe" else "normal",
            color="#1c1c1c" if r["marginality_tier"] != "Safe" else "#555555",
            zorder=5,
        )
        for _, r in to_label.iterrows()
    ]
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    adjust_text(
        texts,
        x=df["prn12_gps_margin_pp"].tolist(),
        y=df["ge15_dun_gps_margin_pp"].tolist(),
        ax=ax,
        expand=(1.15, 1.3),
        arrowprops={"arrowstyle": "-", "color": "#777777", "lw": 0.6},
    )

    quad = {"fontsize": 8.5, "color": "#566573", "style": "italic", "zorder": 2}
    ax.text(x_max - 1, y_max - 2, "GPS led in 2021 and GE15", ha="right", va="top", **quad)
    ax.text(x_max - 1, y_min + 2, "GPS led 2021, trailed in GE15", ha="right", va="bottom", **quad)
    ax.text(x_min + 1, y_min + 2, "GPS trailed in both", ha="left", va="bottom", **quad)
    ax.text(x_min + 1, y_max - 2, "GPS trailed 2021, led GE15", ha="left", va="top", **quad)
    ax.text(x_max - 1, 9.2, "±10 pp competitive band", ha="right", va="top", fontsize=7.8, color="#b9770e")

    n_trailed = int(df["ge15_gps_trailed"].sum())
    ax.set_xlabel("2021 state election: GPS share − best non-GPS share (pp)", fontsize=10.5, fontweight="bold")
    ax.set_ylabel("GE15 2022 (DUN level): GPS share − best non-GPS bloc (pp)", fontsize=10.5, fontweight="bold")
    ax.set_title(
        f"GE15 Cross-Check: GPS Trailed at DUN Level in {n_trailed} of {len(df)} Seats in the 2022 Federal Election",
        fontsize=13,
        fontweight="bold",
        loc="left",
        pad=12,
    )
    ax.grid(True, alpha=0.2, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 0.93), frameon=True, facecolor="white", edgecolor="#dddddd", fontsize=8.8)
    fig.text(
        0.01,
        0.01,
        "Labels: all Tier 1–3 seats plus Safe seats where GPS trailed in GE15. GE15 = federal contest (different candidates); "
        "saluran ballots aggregated by DUN code, postal excluded. Blocs: GPS, PH, PN, PSB, Other.",
        fontsize=7.8,
        color="#555555",
    )
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(CHART_DIR / "ge15_crosscheck.png", dpi=300)
    plt.close(fig)


def main() -> None:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CSV_PATH)
    plot_marginal_seats_ranked(df)
    plot_margin_vs_split_vote(df)
    plot_sarawak_map(df)
    plot_undi18_turnout_saluran(df)
    plot_ge15_crosscheck(df)
    for name in (
        "marginal_seats_ranked.png",
        "margin_vs_split_vote.png",
        "sarawak_marginal_map.png",
        "undi18_turnout_saluran.png",
        "ge15_crosscheck.png",
    ):
        p = CHART_DIR / name
        print(f"Wrote {p} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
