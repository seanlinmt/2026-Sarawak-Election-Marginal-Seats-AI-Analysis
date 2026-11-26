"""Build a multi-page publication-grade PDF briefing for Sarawak 2026 marginal DUN seats."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import html
import json
from pathlib import Path
import subprocess
import sys
import tempfile
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
    SIZE_BANDS,
    TIER_ORDER,
    UNCERTAIN,
    compute_facts,
    join_seats,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
OUT_DIR = ROOT_DIR / "outputs"
CHART_DIR = OUT_DIR / "charts"
CSV_PATH = OUT_DIR / "sarawak_2026_marginal_seats.csv"
MANIFEST_PATH = RAW_DIR / "download_manifest.json"
PDF_PATH = OUT_DIR / "sarawak_2026_marginal_seats_report.pdf"
CHROME_BIN = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def _b64_png(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def _esc(val: object) -> str:
    return html.escape(str(val), quote=True)


def _code(val: str) -> str:
    return f"<code>{_esc(val)}</code>"


def _tier_pill(tier: str) -> str:
    if tier.startswith("Tier 1"):
        cls, label = "pill-t1", "Tier 1"
    elif tier.startswith("Tier 2"):
        cls, label = "pill-t2", "Tier 2"
    elif tier.startswith("Tier 3"):
        cls, label = "pill-t3", "Tier 3"
    else:
        cls, label = "pill-safe", "Safe"
    return f'<span class="pill {cls}">{label}</span>'


def _tier_short(tier: str) -> str:
    if tier.startswith("Tier 1"):
        return "T1"
    if tier.startswith("Tier 2"):
        return "T2"
    if tier.startswith("Tier 3"):
        return "T3"
    return "Safe"


def _outlook_pill(status: str) -> str:
    if status.startswith(LIVE):
        if "Ex-PSB" in status:
            return '<span class="pill pill-ind">Live: Ex-PSB Ind</span>'
        return '<span class="pill pill-live">Live 2026 Contest</span>'
    if status.startswith(UNCERTAIN):
        return '<span class="pill pill-uncertain">Uncertain: Left PDP</span>'
    if status.startswith(CONSOLIDATED):
        return '<span class="pill pill-psb">GPS/PDP Scenario</span>'
    return '<span class="pill pill-safe">Safe</span>'


def build_html(df: pd.DataFrame, manifest: dict) -> str:
    f = compute_facts(df)
    df = f["df"]
    tc = f["tier_counts"]
    non_safe = f["non_safe"]

    def seats_html(sub: pd.DataFrame, col: str | None = None, fmt: str = "", suffix: str = "") -> str:
        return join_seats(sub, _code, col, fmt, suffix)

    def seats_plain(sub: pd.DataFrame) -> str:
        return ", ".join(_esc(s) for s in sub["seat"].tolist())

    # Chart base64 URIs
    img_map = _b64_png(CHART_DIR / "sarawak_marginal_map.png")
    img_ranked = _b64_png(CHART_DIR / "marginal_seats_ranked.png")
    img_scatter = _b64_png(CHART_DIR / "margin_vs_split_vote.png")
    img_vol = _b64_png(CHART_DIR / "undi18_turnout_saluran.png")
    img_ge15 = _b64_png(CHART_DIR / "ge15_crosscheck.png")

    # Tier breakdown rows
    tier_rows_html = []
    for t in TIER_ORDER:
        sub = df[df["marginality_tier"] == t]
        cnt = len(sub)
        live_c = int(sub["live_2026_status"].str.startswith(LIVE).sum())
        unc_c = int(sub["live_2026_status"].str.startswith(UNCERTAIN).sum())
        gps_c = int(sub["live_2026_status"].str.startswith(CONSOLIDATED).sum())
        tier_rows_html.append(
            f"""
            <tr>
              <td>{_tier_pill(t)} {_esc(t)}</td>
              <td class="num">{cnt}</td>
              <td class="num">{100.0 * cnt / len(df):.1f}%</td>
              <td class="num">{live_c}</td>
              <td class="num">{unc_c}</td>
              <td class="num">{gps_c}</td>
              <td class="num">{sub['majority_perc'].median():.1f}%</td>
              <td class="num">{sub['composite_marginality_score'].mean():.1f}</td>
            </tr>
            """
        )

    # Regional breakdown table + dynamic cards
    reg_rows_html = []
    reg_cards_html = []
    dense = f["densest_region"]
    for reg in f["regions"]:
        reg_rows_html.append(
            f"""
            <tr>
              <td><strong>{_esc(reg['name'])}</strong></td>
              <td class="num">{reg['seats']}</td>
              <td class="num">{reg['t1']}</td>
              <td class="num">{reg['t2']}</td>
              <td class="num">{reg['t3']}</td>
              <td class="num">{reg['safe']}</td>
              <td class="num"><strong>{reg['nonsafe_share']:.1f}%</strong></td>
              <td class="num">{len(reg['live'])}</td>
              <td class="num">{len(reg['uncertain'])}</td>
              <td class="num">{len(reg['consolidated'])}</td>
              <td class="num">{reg['median_maj']:.1f}%</td>
              <td class="num">+{reg['median_roll']:.1f}%</td>
              <td class="num">{len(reg['ge15_trailed'])}</td>
            </tr>
            """
        )
        density_note = " (highest regional Tier 1–3 share)" if reg["short"] == dense["short"] else ""
        unc_clause = (
            f" Uncertain (left PDP): {seats_html(reg['uncertain'])}."
            if not reg["uncertain"].empty
            else ""
        )
        reg_cards_html.append(
            f"""
            <div class="reg-card">
              <strong>{_esc(reg['short'])} ({_esc(reg['range'])} · {reg['seats']} Seats)</strong><br>
              {reg['nonsafe']}/{reg['seats']} non-safe ({reg['nonsafe_share']:.1f}%){density_note}; median majority {reg['median_maj']:.1f}%.
              Live 2026 ({len(reg['live'])}): {seats_html(reg['live'])}.{unc_clause}
              GPS-consolidation scenario ({len(reg['consolidated'])}): {seats_html(reg['consolidated'])}.
              GE15 GPS trailed in {len(reg['ge15_trailed'])} seat(s).
            </div>
            """
        )

    # GE15 watch table rows (all seats where GPS trailed or led by <10 pp)
    ge15_rows_html = []
    for _, r in f["ge15_watch"].iterrows():
        lead_cls = "lead-gps" if r["ge15_dun_leading_bloc"] == "GPS" else "lead-opp"
        ge15_rows_html.append(
            f"""
            <tr>
              <td class="nowrap-cell"><strong>{_esc(r['seat'])}</strong></td>
              <td class="nowrap-cell">{_tier_short(str(r['marginality_tier']))}</td>
              <td class="num">{r['prn12_gps_margin_pp']:+.1f}</td>
              <td class="num">{r['ge15_dun_gps_share_perc']:.1f}%</td>
              <td class="num">{r['ge15_dun_ph_share_perc']:.1f}%</td>
              <td class="num">{r['ge15_dun_pn_share_perc']:.1f}%</td>
              <td class="num">{r['ge15_dun_psb_share_perc']:.1f}%</td>
              <td class="num">{r['ge15_dun_other_share_perc']:.1f}%</td>
              <td class="num {lead_cls}"><strong>{r['ge15_dun_gps_margin_pp']:+.1f}</strong></td>
              <td class="nowrap-cell">{_esc(r['ge15_dun_leading_bloc'])}</td>
            </tr>
            """
        )

    # 18 non-safe dossier rows
    dossier_rows_html = []
    for _, r in non_safe.iterrows():
        c3_str = (
            f"{r['third_place_party']} {r['third_place_vote_share_perc']:.1f}%"
            if r["third_place_votes"] > 0
            else "No 3rd"
        )
        swing_str = (
            f"{r['winning_share_swing_pp']:+.1f}"
            if pd.notna(r["winning_share_swing_pp"])
            else "N/A"
        )
        sal_str = (
            f"{r['saluran_youth_gap_pp']:+.1f}"
            if pd.notna(r["saluran_youth_gap_pp"])
            else "N/A"
        )
        size_short = str(r["electorate_size_band"]).split(" ")[0]
        dossier_rows_html.append(
            f"""
            <tr>
              <td class="num"><strong>{int(r['marginality_rank'])}</strong></td>
              <td class="nowrap-cell"><strong>{_esc(r['seat'])}</strong><br><span class="muted">{_esc(size_short)} · {int(r['voters_total']):,}</span></td>
              <td class="nowrap-cell">{_tier_pill(str(r['marginality_tier']))}<br><span class="muted">{r['composite_marginality_score']:.1f} pts</span></td>
              <td class="nowrap-cell"><strong>{_esc(r['winner_party'])}</strong>/{_esc(r['winner_coalition'])}<br><span class="muted">{r['winner_vote_share_perc']:.1f}%</span></td>
              <td class="nowrap-cell">{_esc(r['runner_up_party'])} ({r['runner_up_vote_share_perc']:.1f}%)<br><span class="muted">{_esc(c3_str)}</span></td>
              <td class="num"><strong>{r['majority_perc']:.2f}%</strong><br><span class="muted">{int(r['majority_votes']):,}</span></td>
              <td class="num">{int(r['top2_opposition_combined_gap']):+,d}</td>
              <td class="num">{swing_str}</td>
              <td class="num">{sal_str}</td>
              <td class="num">+{r['undi18_voter_growth_perc']:.1f}%</td>
              <td class="num">{r['ge15_dun_gps_margin_pp']:+.1f}</td>
              <td>{_outlook_pill(str(r['live_2026_status']))}</td>
            </tr>
            """
        )

    # 64 Safe seats split into 2 balanced columns (32 + 32)
    safe_df = df[df["marginality_tier"] == "Safe"].sort_values("marginality_rank").reset_index(drop=True)
    half = (len(safe_df) + 1) // 2
    safe_left = safe_df.iloc[:half]
    safe_right = safe_df.iloc[half:]

    def _safe_rows(sub: pd.DataFrame) -> str:
        out_rows = []
        for _, r in sub.iterrows():
            tags = ""
            if bool(r["is_prk_updated"]):
                tags += " *"
            if bool(r["ge15_flags_safe_seat"]):
                tags += " †"
            out_rows.append(
                f"""
                <tr>
                  <td class="num">{int(r['marginality_rank'])}</td>
                  <td>{_esc(r['seat'])}{tags}</td>
                  <td>{_esc(r['winner_party'])}/{_esc(r['winner_coalition'])}</td>
                  <td class="num">{r['majority_perc']:.1f}%</td>
                  <td class="num">{int(r['majority_votes']):,}</td>
                  <td class="num">{r['ge15_dun_gps_margin_pp']:+.1f}</td>
                  <td class="num">+{r['undi18_voter_growth_perc']:.1f}%</td>
                </tr>
                """
            )
        return "\n".join(out_rows)

    # Manifest provenance rows
    prov_rows = []
    for f_entry in manifest.get("files", []):
        size_kb = f_entry["size_bytes"] / 1024.0
        size_str = f"{size_kb / 1024.0:.2f} MB" if size_kb >= 1024.0 else f"{size_kb:.1f} KB"
        prov_rows.append(
            f"""
            <tr>
              <td><code>{_esc(f_entry['filename'])}</code></td>
              <td class="num">{size_str}</td>
              <td><code>{_esc(str(f_entry['sha256'])[:16])}…</code></td>
              <td class="muted">{_esc(str(f_entry['downloaded_at_utc'])[:19].replace('T', ' '))} UTC</td>
            </tr>
            """
        )

    gen_date = datetime.now().strftime("%d %b %Y")
    jr = f["jepak"]
    bl = f["batu_lintang"]
    kr = f["krian"]
    mt2 = f["max_t2"]
    sm = f["score_means"]
    comp_txt = ", ".join(f"{label} {sm[c]:.1f}/{mx}" for c, label, mx in SCORE_COMPONENTS)
    small_txt = ", ".join(
        f"{_code(r['seat'])} ({int(r['voters_total']):,} voters; 500 votes ≈ {r['vote500_perc']:.1f}% of valid votes)"
        for _, r in f["small_examples"].iterrows()
    )
    overrides_txt = " ".join(
        f"{_code(r['seat'])}: {_esc(r['political_context_note'])}"
        for _, r in f["overrides"].iterrows()
    )
    uncontested_16 = df[df["prn11_2016_uncontested"]]
    no_saluran = df[df["multi_saluran_pm_count"] == 0]
    first_seat = df.sort_values("code_dun").iloc[0]["seat"]
    last_seat = df.sort_values("code_dun").iloc[-1]["seat"]
    n_files = len(manifest.get("files", []))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sarawak 2026 State Election (PRN13) — Marginal DUN Seats Analysis</title>
<style>
  @page {{
    size: A4 portrait;
    margin: 12mm 13mm 14mm 13mm;
    @bottom-left {{
      content: "Sarawak 2026 DUN Marginal Seats Analysis · Source: electiondata.my · Context as of {CONTEXT_DATE}";
      font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
      font-size: 7.3pt;
      color: #64748b;
    }}
    @bottom-right {{
      content: "Page " counter(page) " of " counter(pages);
      font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
      font-size: 7.3pt;
      color: #64748b;
    }}
  }}
  * {{
    box-sizing: border-box;
    print-color-adjust: exact !important;
    -webkit-print-color-adjust: exact !important;
  }}
  body {{
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
    font-size: 8.8pt;
    line-height: 1.4;
    color: #1e293b;
    background: #ffffff;
  }}
  .page-break {{
    break-before: page;
    page-break-before: always;
  }}
  .avoid-break {{
    break-inside: avoid;
    page-break-inside: avoid;
  }}
  /* Masthead */
  .masthead {{
    background: #0f2342;
    color: #ffffff;
    padding: 13px 17px 12px 17px;
    border-radius: 6px;
    border-bottom: 4px solid #c0392b;
    position: relative;
    margin-bottom: 10px;
  }}
  .masthead::after {{
    content: "";
    display: block;
    position: absolute;
    left: 0;
    right: 0;
    bottom: -7px;
    height: 3px;
    background: #f1c40f;
    border-radius: 0 0 4px 4px;
  }}
  .masthead .eyebrow {{
    font-size: 7.4pt;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #cbd5e1;
    margin-bottom: 3px;
  }}
  .masthead h1 {{
    font-size: 16pt;
    line-height: 1.15;
    margin: 0 0 4px 0;
    font-weight: 700;
    color: #ffffff;
  }}
  .masthead .subtitle {{
    font-size: 9.2pt;
    color: #e2e8f0;
    margin: 0 0 5px 0;
  }}
  .masthead .meta {{
    font-size: 7.5pt;
    color: #94a3b8;
  }}
  /* KPI Row */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin: 13px 0 10px 0;
  }}
  .kpi-card {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-top: 3px solid #0f2342;
    border-radius: 5px;
    padding: 7px 9px;
  }}
  .kpi-card.accent-red {{ border-top-color: #c0392b; }}
  .kpi-card.accent-amber {{ border-top-color: #e67e22; }}
  .kpi-card.accent-teal {{ border-top-color: #0d9488; }}
  .kpi-val {{
    font-size: 14.5pt;
    font-weight: 700;
    color: #0f2342;
    line-height: 1.15;
  }}
  .kpi-lbl {{
    font-size: 7.6pt;
    font-weight: 600;
    color: #334155;
    margin-top: 2px;
  }}
  .kpi-sub {{
    font-size: 6.9pt;
    color: #64748b;
    margin-top: 2px;
  }}
  h2 {{
    font-size: 11.6pt;
    font-weight: 700;
    color: #0f2342;
    border-bottom: 1.5px solid #cbd5e1;
    padding-bottom: 3px;
    margin: 0 0 7px 0;
  }}
  h3 {{
    font-size: 9.4pt;
    font-weight: 700;
    color: #0f2342;
    margin: 7px 0 4px 0;
  }}
  p {{ margin: 0 0 5px 0; }}
  ul {{
    margin: 3px 0 8px 0;
    padding-left: 16px;
  }}
  li {{ margin-bottom: 3px; }}
  code {{
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 7.4pt;
    background: #f1f5f9;
    padding: 0.5px 3px;
    border-radius: 3px;
    color: #0f172a;
  }}
  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 8px;
    font-size: 7.9pt;
  }}
  th {{
    background: #0f2342;
    color: #ffffff;
    font-weight: 600;
    text-align: left;
    padding: 4.5px 5.5px;
    font-size: 7.4pt;
    border-bottom: 2px solid #c0392b;
  }}
  th.num, td.num {{
    text-align: right;
    font-variant-numeric: tabular-nums;
  }}
  td {{
    padding: 4px 5.5px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
  }}
  tbody tr:nth-child(even) {{
    background: #f8fafc;
  }}
  .muted {{
    font-size: 6.8pt;
    color: #64748b;
  }}
  .lead-opp {{ color: #991b1b; }}
  .lead-gps {{ color: #0f5132; }}
  /* Pills */
  .pill {{
    display: inline-block;
    padding: 1.2px 5px;
    border-radius: 999px;
    font-size: 6.6pt;
    font-weight: 700;
    letter-spacing: 0.01em;
    white-space: nowrap;
  }}
  .pill-t1 {{ background: #fde8e8; color: #9b1c1c; border: 1px solid #f8b4b4; }}
  .pill-t2 {{ background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; }}
  .pill-t3 {{ background: #fef9c3; color: #854d0e; border: 1px solid #fde047; }}
  .pill-safe {{ background: #e2e8f0; color: #334155; border: 1px solid #cbd5e1; }}
  .pill-live {{ background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }}
  .pill-ind {{ background: #f3e8ff; color: #6b21a8; border: 1px solid #d8b4fe; }}
  .pill-uncertain {{ background: #ffedd5; color: #9a3412; border: 1px solid #fdba74; }}
  .pill-psb {{ background: #e0f2fe; color: #075985; border: 1px solid #7dd3fc; }}
  /* Two-col methodology */
  .two-col {{
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 9px;
    margin-top: 5px;
  }}
  .box {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 7px 9px;
    font-size: 7.8pt;
  }}
  .box h3 {{
    margin-top: 0;
    font-size: 8.8pt;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 3px;
  }}
  /* Figures */
  .figure-card {{
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 8px 5px 8px;
    background: #ffffff;
    margin-bottom: 8px;
  }}
  .figure-card img {{
    display: block;
    width: 100%;
    height: auto;
    object-fit: contain;
    margin: 0 auto;
  }}
  .fig-map img {{ max-height: 112mm; }}
  .fig-stacked img {{ max-height: 104mm; }}
  .fig-vol img {{ max-height: 106mm; }}
  .fig-ge15 img {{ max-height: 82mm; }}
  .fig-caption {{
    font-size: 7.5pt;
    color: #475569;
    margin-top: 4px;
    border-top: 1px solid #f1f5f9;
    padding-top: 3.5px;
  }}
  /* 3-col regional cards */
  .three-col {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-top: 4px;
  }}
  .reg-card {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 3px solid #0f2342;
    border-radius: 4px;
    padding: 6px 7px;
    font-size: 7.35pt;
    line-height: 1.32;
  }}
  .reg-card strong {{ color: #0f2342; }}
  /* 2x2 insight grid */
  .grid-2x2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 7px;
  }}
  .insight-card {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 7px 9px;
    font-size: 7.9pt;
  }}
  .insight-card h3 {{
    margin-top: 0;
    font-size: 8.8pt;
    color: #0f2342;
  }}
  th code {{
    background: rgba(255, 255, 255, 0.16);
    color: #ffffff;
  }}
  /* GE15 compact table */
  .ge15-table {{ font-size: 6.7pt; margin-bottom: 5px; }}
  .ge15-table th {{ padding: 2.8px 4px; font-size: 6.6pt; }}
  .ge15-table td {{ padding: 1.9px 4px; line-height: 1.18; }}
  .ge15-table td.num, .ge15-table td.nowrap-cell {{ white-space: nowrap; }}
  /* Dossier compact table */
  .dossier-table {{ font-size: 6.8pt; margin-bottom: 6px; }}
  .dossier-table th {{ padding: 3.2px 3.5px; font-size: 6.6pt; }}
  .dossier-table td {{ padding: 2.5px 3.5px; line-height: 1.2; }}
  .dossier-table td.num, .dossier-table td.nowrap-cell {{ white-space: nowrap; }}
  /* Safe appendix 2-col */
  .safe-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 9px;
  }}
  .safe-table {{ font-size: 6.7pt; }}
  .safe-table th {{ padding: 3.2px 3.5px; font-size: 6.5pt; }}
  .safe-table td {{ padding: 2.2px 3.5px; }}
  .callout-banner {{
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-left: 4px solid #1d4ed8;
    border-radius: 4px;
    padding: 6px 9px;
    font-size: 7.7pt;
    margin-top: 5px;
  }}
  .prov-table {{ font-size: 7.4pt; margin-bottom: 6px; }}
  .prov-table th {{ padding: 3.5px 5px; font-size: 7.1pt; }}
  .prov-table td {{ padding: 2.6px 5px; }}
</style>
</head>
<body>

<!-- ==================== PAGE 1: EXECUTIVE BRIEF & METHODOLOGY ==================== -->
<div class="masthead">
  <div class="eyebrow">Election Intelligence Briefing · Gazetted {len(df)}-Seat Baseline (N.01–N.82)</div>
  <h1>Sarawak 2026 State Election (PRN13): Marginal DUN Seats Analysis</h1>
  <div class="subtitle">Empirical Margin Rankings, Vote-Split Risk, GE15 Cross-Check &amp; Post-PSB Realignment</div>
  <div class="meta">PRN13 Nomination {NOMINATION_DATE} · Polling {POLLING_DATE} (existing {len(df)} seats) · Context as of {CONTEXT_DATE} · Source: electiondata.my · Compiled {gen_date}</div>
</div>

<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-val">{len(df)}</div>
    <div class="kpi-lbl">Gazetted DUN Seats</div>
    <div class="kpi-sub">{_esc(first_seat)} – {_esc(last_seat)}</div>
  </div>
  <div class="kpi-card accent-amber">
    <div class="kpi-val">{len(non_safe)}</div>
    <div class="kpi-lbl">Tier 1–3 Seats (2021 Math)</div>
    <div class="kpi-sub">{int(tc[TIER_ORDER[0]])} Razor-Thin · {int(tc[TIER_ORDER[1]])} Marginal · {int(tc[TIER_ORDER[2]])} Watchlist</div>
  </div>
  <div class="kpi-card accent-red">
    <div class="kpi-val">{len(f['live'])} / {len(f['uncertain'])}</div>
    <div class="kpi-lbl">Live / Uncertain (2026)</div>
    <div class="kpi-sub">{len(f['consolidated'])} GPS/PDP consolidation scenarios</div>
  </div>
  <div class="kpi-card accent-teal">
    <div class="kpi-val">+{f['med_roll']:.1f}%</div>
    <div class="kpi-lbl">Median Roll Growth (Undi18+AVR)</div>
    <div class="kpi-sub">PRN12 (Dec 2021) → GE15 (Nov 2022)</div>
  </div>
</div>

<h2>Executive Summary</h2>
<ul>
  <li><strong>Baseline Marginality Distribution:</strong> Evaluating all {len(df)} seats from PRN12 (18 Dec 2021) and the {_code(jr['seat'])} by-election ({_esc(jr['baseline_election_date'])}) yields <strong>{int(tc[TIER_ORDER[0]])} Tier 1 (Razor-Thin)</strong>, <strong>{int(tc[TIER_ORDER[1]])} Tier 2 (Marginal)</strong>, <strong>{int(tc[TIER_ORDER[2]])} Tier 3 (Watchlist)</strong>, and <strong>{int(tc['Safe'])} Safe</strong> seats.</li>
  <li><strong>Multi-Cornered Vote-Splitting Exposure:</strong> <strong>{f['plurality_count']} DUN seats</strong> were won with &lt;50% of valid votes, and in <strong>{f['top2_exceed_count']} seats</strong> combined 2nd + 3rd place votes exceeded the winner (widest deficits: {seats_html(f['worst_split'], 'top2_opposition_combined_gap', '+,d')}).</li>
  <li><strong>Post-PSB 2026 Outlook (Scenario, Not Forecast):</strong> PSB placed 1st or 2nd in <strong>{f['psb_flag_all']} seats</strong> statewide ({f['psb_flag_nonsafe']} of {len(non_safe)} Tier 1–3 seats) before dissolving into GPS component PDP in April 2024. As of {CONTEXT_DATE}, <strong>{len(f['live'])}</strong> Tier 1–3 seats remain live contests (led by {seats_html(f['live'].head(3))}), <strong>{len(f['uncertain'])}</strong> are uncertain after late-Nov 2026 PDP exits ({seats_html(f['uncertain'])}), and <strong>{len(f['consolidated'])}</strong> are GPS/PDP consolidation scenarios assuming former PSB voters follow.</li>
  <li><strong>GE15 (2022) Cross-Check:</strong> Aggregating GE15 saluran ballots to DUN level shows GPS trailed the strongest non-GPS bloc in <strong>{len(f['ge15_trailed'])}</strong> of {len(df)} seats ({len(f['ge15_nonsafe_trailed'])} Tier 1–3) and led by &lt;10 pp in <strong>{len(f['ge15_close_led'])}</strong> more, flagging <strong>{len(f['ge15_safe_flagged'])}</strong> Safe seats.</li>
</ul>

<table>
  <thead>
    <tr>
      <th>Marginality Tier</th>
      <th class="num">Seats</th>
      <th class="num">% of {len(df)}</th>
      <th class="num">Live 2026</th>
      <th class="num">Uncertain</th>
      <th class="num">GPS Scenario</th>
      <th class="num">Median Maj %</th>
      <th class="num">Mean Score</th>
    </tr>
  </thead>
  <tbody>
    {"".join(tier_rows_html)}
  </tbody>
</table>

<h2>Composite Marginality Methodology &amp; Tier Rules</h2>
<div class="two-col">
  <div class="box">
    <h3>Composite Score (0–100 Scale)</h3>
    <p>Each seat sums five clipped components (missing 2016/saluran sub-terms add <code>0.0</code> without altering raw values):</p>
    <ul>
      <li><strong>Baseline % Majority (40 pts):</strong> <code>40 × clip((30 − maj%) / 30)</code></li>
      <li><strong>Small-Seat Raw Majority (15 pts):</strong> <code>15 × clip((2500 − maj_votes) / 2500)</code></li>
      <li><strong>Plurality &amp; Split-Vote (20 pts):</strong> <code>10 × clip((60 − win%) / 35) + 10 × clip((10 − top2_gap%) / 25)</code></li>
      <li><strong>2016→Baseline Swing (15 pts):</strong> <code>15 × clip(−swing_pp / 25)</code> (BN→GPS, PH, or incumbent continuity)</li>
      <li><strong>Turnout &amp; Saluran Volatility (10 pts):</strong> <code>5 × clip(−turnout_Δ / 20) + 5 × clip(|youth_gap| / 15)</code></li>
    </ul>
  </div>
  <div class="box">
    <h3>Top-Down Tier Rules &amp; Separate GE15 Signal</h3>
    <ul>
      <li><strong>Tier 1 (Razor-Thin):</strong> <code>majority_perc &lt; 5%</code> OR <code>majority_votes &lt; 500</code></li>
      <li><strong>Tier 2 (Marginal):</strong> Not Tier 1, and (<code>5% ≤ majority_perc &lt; 10%</code> OR plurality win <code>&lt;50%</code> where <code>2nd + 3rd &gt; winner</code>)</li>
      <li><strong>Tier 3 (Watchlist):</strong> Not Tier 1–2, <code>10% ≤ majority_perc &lt; 15%</code>, plus ≥1 volatility trigger (negative swing, <code>|turnout Δ| ≥ 10 pp</code>, <code>|youth gap| ≥ 5 pp</code>, or 2021 turnout <code>&lt;55%</code>)</li>
      <li><strong>GE15 Cross-Check (Separate):</strong> Non-postal GE15 saluran ballots aggregated by DUN code (GPS, PH, PN, PSB, Other); not mixed into the composite score.</li>
    </ul>
  </div>
</div>

<!-- ==================== PAGE 2: SPATIAL ANALYSIS & REGIONAL BREAKDOWN ==================== -->
<div class="page-break"></div>
<h2>Spatial Distribution &amp; Regional Breakdown ({len(df)} Sarawak DUNs)</h2>

<div class="figure-card fig-map avoid-break">
  <img src="{img_map}" alt="Sarawak 82-DUN Marginality Choropleth Map">
  <div class="fig-caption"><strong>Figure 1:</strong> Geographic clustering of Tier 1–3 seats on the gazetted 2015 Sarawak DUN delimitation, with zoomed urban insets for Kuching (A) and Sibu (B). Highest Tier 1–3 concentration is in <strong>{_esc(dense['short'])}</strong> ({dense['nonsafe']}/{dense['seats']} = {dense['nonsafe_share']:.1f}%).</div>
</div>

<table>
  <thead>
    <tr>
      <th>Region</th>
      <th class="num">Seats</th>
      <th class="num">T1</th>
      <th class="num">T2</th>
      <th class="num">T3</th>
      <th class="num">Safe</th>
      <th class="num">Non-Safe</th>
      <th class="num">Live</th>
      <th class="num">Unc.</th>
      <th class="num">Cons.</th>
      <th class="num">Med Maj</th>
      <th class="num">Med Roll Δ</th>
      <th class="num">GE15 Trail</th>
    </tr>
  </thead>
  <tbody>
    {"".join(reg_rows_html)}
  </tbody>
</table>

<div class="three-col">
  {"".join(reg_cards_html)}
</div>

<!-- ==================== PAGE 3: MARGIN RANKINGS & VOTE-SPLITTING ==================== -->
<div class="page-break"></div>
<h2>2021 Margin Rankings &amp; Multi-Cornered Vote-Splitting Exposure</h2>

<div class="figure-card fig-stacked avoid-break">
  <img src="{img_ranked}" alt="Top 20 Tightest Sarawak DUN Seats">
  <div class="fig-caption"><strong>Figure 2:</strong> Top 20 tightest seats ranked by 2021 majority percentage. All {len(f['tier1'])} Tier 1 seats fell below 5% ({seats_html(f['tier1'], 'majority_perc', '.2f', '%')}). Tags separate 2024 PSB→PDP merger seats (<code>[PSB→PDP]</code>), late-Nov 2026 PDP exits (<code>[Left PDP]</code>: {seats_html(f['overrides'])}), and {_code(bl['seat'])} (<code>[Ex-PSB Ind]</code>).</div>
</div>

<div class="figure-card fig-stacked avoid-break">
  <img src="{img_scatter}" alt="Majority Margin vs Winner Vote Share">
  <div class="fig-caption"><strong>Figure 3:</strong> Majority margin versus winner vote share across all {len(df)} DUNs. Of {f['plurality_count']} plurality wins (&lt;50% winner share), {f['top2_exceed_count']} saw combined 2nd + 3rd votes exceed the winner (black rings), led by lowest winning shares in {seats_html(f['low_share_split'], 'winner_vote_share_perc', '.1f', '%')}.</div>
</div>

<!-- ==================== PAGE 4: TURNOUT, ROLL GROWTH & SALURAN VOLATILITY ==================== -->
<div class="page-break"></div>
<h2>Turnout Suppression, Voter-Roll Growth (Undi18 + AVR) &amp; Saluran Youth Proxy</h2>

<div class="figure-card fig-vol avoid-break">
  <img src="{img_vol}" alt="Voter-Roll Growth, Turnout Shift, and Saluran Youth Gap">
  <div class="fig-caption"><strong>Figure 4:</strong> Demographic and turnout volatility across all {len(non_safe)} Tier 1–3 seats ordered by composite rank. Largest post-PRN12 voter-roll expansions among Tier 1–3 seats occurred in {seats_html(f['top_roll_nonsafe'], 'undi18_voter_growth_perc', '+.1f', '%')}.</div>
</div>

<div class="grid-2x2">
  <div class="insight-card">
    <h3>1. 2021 COVID-Era Turnout Suppression</h3>
    <p>Contested DUN turnout fell from <strong>{f['mean_t16']:.1f}%</strong> in 2016 ({f['n_contested_2016']} contested seats) to <strong>{f['mean_t21']:.1f}%</strong> in December 2021 (mean shift <strong>{f['mean_t_chg']:+.1f} pp</strong>). Largest drops among Tier 1–3 seats were in {seats_html(f['worst_turnout_drops'], 'turnout_change_2016_to_2021_pp', '+.1f', ' pp')}, creating rebound sensitivity in 2026.</p>
  </div>
  <div class="insight-card">
    <h3>2. Voter-Roll Growth (Undi18 + Automatic Registration)</h3>
    <p>PRN12 predated both Undi18 and automatic voter registration (AVR). By GE15 (Nov 2022), non-postal DUN rolls expanded by a median <strong>+{f['med_roll']:.1f}%</strong> (range <strong>+{f['min_roll']['undi18_voter_growth_perc']:.1f}%</strong> in {_code(f['min_roll']['seat'])} to <strong>+{f['max_roll']['undi18_voter_growth_perc']:.1f}%</strong> in {_code(f['max_roll']['seat'])}). Growth reflects all newly auto-registered adults, not only 18–20-year-olds; the 2026 roll is larger again.</p>
  </div>
  <div class="insight-card">
    <h3>3. Within-PM Saluran Youth-Stream Proxy</h3>
    <p>Splitting multi-saluran centres at <code>max_saluran / 2</code> (excluding Undi Pos/Awal) is a rough age-stream proxy. Sharpest negative gaps (winner weaker among younger streams) were in {seats_html(f['youth_neg'], 'saluran_youth_gap_pp', '+.1f', ' pp')}, versus strongest positive youth skew in {seats_html(f['youth_pos'], 'saluran_youth_gap_pp', '+.1f', ' pp')}.</p>
  </div>
  <div class="insight-card">
    <h3>4. Electorate Scale &amp; Swing Leverage</h3>
    <p>Across {len(df)} seats: <strong>{f['size_counts'][SIZE_BANDS[0]]}</strong> Small Rural (&lt;10k; {f['size_ns_counts'][SIZE_BANDS[0]]} Tier 1–3), <strong>{f['size_counts'][SIZE_BANDS[1]]}</strong> Medium (10k–20k; {f['size_ns_counts'][SIZE_BANDS[1]]} Tier 1–3), and <strong>{f['size_counts'][SIZE_BANDS[2]]}</strong> Large Urban (≥20k; {f['size_ns_counts'][SIZE_BANDS[2]]} Tier 1–3). Small-roll leverage examples: {small_txt}.</p>
  </div>
</div>

<!-- ==================== PAGE 5: GE15 SEAT-LEVEL CROSS-CHECK ==================== -->
<div class="page-break"></div>
<h2>GE15 (2022) Seat-Level Cross-Check: DUN-Level Federal Benchmarks</h2>

<div class="figure-card fig-ge15 avoid-break">
  <img src="{img_ge15}" alt="2021 State GPS Margin vs GE15 2022 DUN-Level GPS Margin">
  <div class="fig-caption"><strong>Figure 5:</strong> 2021 state GPS margin vs. GE15 (Nov 2022) DUN-level GPS margin across all {len(df)} seats. GPS led {int(f['ge15_lead_counts'].get('GPS', 0))} seats in GE15, trailed in {len(f['ge15_trailed'])} (PH {int(f['ge15_lead_counts'].get('PH', 0))}, PSB {int(f['ge15_lead_counts'].get('PSB', 0))}, PN {int(f['ge15_lead_counts'].get('PN', 0))}, Other {int(f['ge15_lead_counts'].get('OTHER', 0))}), and led by &lt;10 pp in {len(f['ge15_close_led'])} more.</div>
</div>

<table class="ge15-table">
  <thead>
    <tr>
      <th>Seat ({len(f['ge15_watch'])} seats where GPS trailed or led &lt;10 pp)</th>
      <th>Tier</th>
      <th class="num">2021 GPS Δ</th>
      <th class="num">GE15 GPS</th>
      <th class="num">GE15 PH</th>
      <th class="num">GE15 PN</th>
      <th class="num">GE15 PSB</th>
      <th class="num">GE15 Oth</th>
      <th class="num">GE15 GPS Δ</th>
      <th>Leader</th>
    </tr>
  </thead>
  <tbody>
    {"".join(ge15_rows_html)}
  </tbody>
</table>

<div class="callout-banner avoid-break">
  <strong>Cross-Check Takeaway:</strong> GPS trailed at DUN level in GE15 in <strong>{len(f['ge15_nonsafe_trailed'])} of {len(non_safe)}</strong> Tier 1–3 seats and in <strong>{len(f['ge15_safe_trailed'])} Safe seats</strong> ({seats_html(f['ge15_safe_trailed'])}), and led by &lt;10 pp in <strong>{len(f['ge15_safe_close'])} additional Safe seats</strong> ({seats_html(f['ge15_safe_close'])})—<strong>{len(f['ge15_safe_flagged'])} Safe seats</strong> flagged in total. Because GE15 was a federal contest with different candidates and stronger urban PH coattails, treat these as an upper bound on non-GPS potential rather than a state-election forecast.
</div>

<!-- ==================== PAGE 6: 18-SEAT MARGINAL & WATCHLIST DOSSIER ==================== -->
<div class="page-break"></div>
<h2>Complete Tier 1–3 Seat Dossier &amp; Post-PSB 2026 Outlook</h2>

<table class="dossier-table">
  <thead>
    <tr>
      <th class="num">#</th>
      <th>Seat &amp; Scale</th>
      <th>Tier / Score</th>
      <th>2021 Winner</th>
      <th>2nd &amp; (3rd)</th>
      <th class="num">Majority</th>
      <th class="num">Top2 Gap</th>
      <th class="num">16→21 Δ</th>
      <th class="num">Youth Δ</th>
      <th class="num">Roll Δ</th>
      <th class="num">GE15 Δ</th>
      <th>2026 Outlook</th>
    </tr>
  </thead>
  <tbody>
    {"".join(dossier_rows_html)}
  </tbody>
</table>

<div class="callout-banner avoid-break">
  <h3>Post-PSB Political Context (As of {CONTEXT_DATE}): Scenario Assumptions vs. Live Contests</h3>
  <ul>
    <li><strong>{len(f['consolidated'])} GPS/PDP Consolidation Scenarios ({seats_plain(f['consolidated'])}):</strong> Assumes former 2021 PSB voters follow PSB's Apr 2024 merger into GPS component PDP. Treat as a scenario rather than a forecast—many 2021 PSB ballots were anti-GPS protest votes.</li>
    <li><strong>{len(f['uncertain'])} Uncertain Seats After Late-Nov 2026 PDP Exits ({seats_plain(f['uncertain'])}):</strong> {overrides_txt}</li>
    <li><strong>{_code(bl['seat'])} (Rank #{int(bl['marginality_rank'])}, {bl['composite_marginality_score']:.2f} pts, {int(bl['majority_votes']):,}-vote margin):</strong> Incumbent See Chee How quit PSB in Aug 2022 before the PDP merger; with {_esc(bl['runner_up_party'])} at {bl['runner_up_vote_share_perc']:.1f}% and {_esc(bl['third_place_party'])} at {bl['third_place_vote_share_perc']:.1f}%, it stays live.</li>
    <li><strong>3rd-Place PSB Vote &amp; {_code(kr['seat'])}:</strong> PSB placed 3rd with ≥10% in {seats_html(f['psb_third'], 'psb_2021_vote_share_perc', '.1f', '%')}, creating swing sensitivity in urban GPS/PH duels if former PSB voters split unevenly. {_code(kr['seat'])} stays live because 3rd-place {_esc(kr['third_place_party'])} ({kr['third_place_vote_share_perc']:.1f}%) sat outside PSB.</li>
  </ul>
</div>

<!-- ==================== PAGE 7: CAVEATS & PROVENANCE ==================== -->
<div class="page-break"></div>
<h2>Key Analytical Caveats, Method Limits &amp; Data Provenance</h2>

<div class="box avoid-break" style="margin-bottom: 8px;">
  <h3>Analytical Caveats &amp; Methodological Limits (Context as of {CONTEXT_DATE})</h3>
  <ul>
    <li><strong>PRN13 Schedule &amp; Scope:</strong> Nomination is <strong>{NOMINATION_DATE}</strong> and polling is <strong>{POLLING_DATE}</strong> on the existing <strong>{len(df)} gazetted DUN seats</strong> (2015 delimitation). All 2026 political status flags reflect developments as of {CONTEXT_DATE}.</li>
    <li><strong>Roll Growth &amp; GE15 Cross-Check Limits:</strong> GE15 DUN figures aggregate non-postal saluran stations (excluding <code>dm</code> code <code>00</code> Undi Pos, ~2% of votes). Roll growth combines Undi18 and automatic registration of all unregistered adults, not only youth; GE15 was a federal contest with different candidates and PSB contesting federally.</li>
    <li><strong>Score Dominance &amp; Tier Ordering:</strong> For the {len(non_safe)} Tier 1–3 seats, mean composite score is <strong>{f['score_total_mean']:.1f}</strong>, of which <strong>{f['margin_points_mean']:.1f} pts</strong> come from the two 2021-margin terms ({_esc(comp_txt)})—making the ranking largely margin-driven. Tier rules and score rank can diverge: {seats_html(f['t2_below_t3'])} are Tier 2 yet rank below the top Tier 3 seat, while {_code(mt2['seat'])} is Tier 2 at {mt2['majority_perc']:.2f}% majority vs. Safe {seats_html(f['safe_below_t2'], 'majority_perc', '.2f', '%')}. The saluran youth gap is a crude half-split proxy; PSB consolidation is a scenario assumption.</li>
    <li><strong>By-Election &amp; Missing-Value Edge Cases:</strong> {_code(jr['seat'])} uses the <code>{_esc(jr['baseline_election_date'])}</code> PRK ({_esc(jr['winner_party'])}/{_esc(jr['winner_coalition'])} {jr['winner_vote_share_perc']:.2f}%, majority {int(jr['majority_votes']):,} / {jr['majority_perc']:.2f}%, turnout {jr['voter_turnout_perc']:.2f}%) rather than PRN12 ({jr['prn12_2021_majority_perc']:.2f}% majority, {jr['prn12_2021_turnout_perc']:.2f}% turnout). 2016 uncontested {seats_html(uncontested_16)} have N/A swing/turnout Δ; single-saluran {seats_html(no_saluran)} has N/A youth gap.</li>
  </ul>
</div>

<h3>Verified Raw Data Lake Manifest (<code>data/raw/download_manifest.json</code> · {n_files} files)</h3>
<table class="prov-table">
  <thead>
    <tr>
      <th>File Name (from <code>lake.electiondata.my</code>)</th>
      <th class="num">Size</th>
      <th>SHA-256 Prefix</th>
      <th>Downloaded (UTC)</th>
    </tr>
  </thead>
  <tbody>
    {"".join(prov_rows)}
  </tbody>
</table>

<div class="callout-banner avoid-break">
  <strong>Automated Verification &amp; Audit Status:</strong> All {len(df)} PRN12 seats, the {_code(jr['seat'])} PRK, and all {len(df)} non-postal GE15 DUN aggregations passed exact ballot-vs-<code>votes_valid</code> reconciliation, bloc-share sum checks, duplicate/null checks, Top-20 raw Parquet margin checks, political override assertions, and {len(df)}/{len(df)} GeoJSON geometry verification via <code>pytest</code>.
</div>

<!-- ==================== PAGE 8: SAFE SEATS APPENDIX ==================== -->
<div class="page-break"></div>
<h2>Appendix: All Remaining {len(safe_df)} Safe DUN Seats (Ranks #{int(safe_df['marginality_rank'].min())}–#{int(safe_df['marginality_rank'].max())})</h2>
<p class="muted" style="margin-bottom: 6px;">Sorted by composite marginality score descending. <code>*</code> = post-2021 PRK baseline ({_code(jr['seat'])}, {_esc(jr['baseline_election_date'])}); <code>†</code> = Safe seat flagged by GE15 cross-check (GPS trailed or led &lt;10 pp at DUN level in 2022).</p>

<div class="safe-grid">
  <table class="safe-table">
    <thead>
      <tr>
        <th class="num">#</th>
        <th>Seat</th>
        <th>Winner</th>
        <th class="num">Maj %</th>
        <th class="num">Votes</th>
        <th class="num">GE15 Δ</th>
        <th class="num">Roll Δ</th>
      </tr>
    </thead>
    <tbody>
      {_safe_rows(safe_left)}
    </tbody>
  </table>
  <table class="safe-table">
    <thead>
      <tr>
        <th class="num">#</th>
        <th>Seat</th>
        <th>Winner</th>
        <th class="num">Maj %</th>
        <th class="num">Votes</th>
        <th class="num">GE15 Δ</th>
        <th class="num">Roll Δ</th>
      </tr>
    </thead>
    <tbody>
      {_safe_rows(safe_right)}
    </tbody>
  </table>
</div>

</body>
</html>
"""


def render_pdf(save_html: bool = False) -> Path:
    if not CHROME_BIN.exists():
        raise FileNotFoundError(f"Google Chrome binary not found at {CHROME_BIN}")

    df = pd.read_csv(CSV_PATH)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    html_text = build_html(df, manifest)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if save_html:
        html_debug = OUT_DIR / "sarawak_2026_marginal_seats_report.html"
        html_debug.write_text(html_text, encoding="utf-8")
        print(f"Wrote debug HTML: {html_debug}")

    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / "report.html"
        html_path.write_text(html_text, encoding="utf-8")
        cmd = [
            str(CHROME_BIN),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={PDF_PATH}",
            html_path.as_uri(),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise RuntimeError(
                f"Chrome print-to-pdf failed (rc={res.returncode}):\n{res.stderr}"
            )

    if not PDF_PATH.exists() or PDF_PATH.stat().st_size == 0:
        raise RuntimeError(f"PDF output missing or empty: {PDF_PATH}")

    print(f"Wrote {PDF_PATH} ({PDF_PATH.stat().st_size:,} bytes)")
    return PDF_PATH


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--save-html",
        action="store_true",
        help="Also write rendered HTML to outputs/ for debugging.",
    )
    args = parser.parse_args()
    render_pdf(save_html=args.save_html)


if __name__ == "__main__":
    main()
