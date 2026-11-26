# 2026 Sarawak State Election (PRN13) — Marginal DUN Seats AI Analysis

> [!WARNING]
> **Disclaimer:** This analysis was generated with AI assistance and relies on analytical assumptions (including composite score weights, scenario-based party realignment flags, and historical/federal cross-checks). **Assumptions and AI-generated outputs may be inaccurate, incomplete, or superseded by political developments.** Always verify figures and context independently against primary sources before relying on them.

Data-driven marginality analysis of all **82 Sarawak State Legislative Assembly (DUN) seats (`N.01`–`N.82`)** ahead of the 13th Sarawak State Election (nomination `28 Nov 2026`, polling `12 Dec 2026`), built from official historical datasets published by [electiondata.my](https://electiondata.my/data-catalogue/) (CC0 Public Domain).

---

## Key Findings (Context as of 26 Nov 2026)

- **Baseline Marginality Tiers (2021 PRN12 + 2023 `N.67 Jepak` PRK):** **6** Tier 1 (Razor-Thin), **9** Tier 2 (Marginal), **3** Tier 3 (Watchlist), and **64** Safe seats (**18** non-safe seats in total).
- **Multi-Cornered Vote-Splitting:** **16** seats were won with `<50%` of valid votes, and in **14** seats combined 2nd + 3rd place votes exceeded the winner (`N.54 Pelawan` `-3,657`, `N.68 Tanjong Batu` `-2,181`).
- **Post-PSB 2026 Outlook (Scenario, Not Forecast):** Of the 18 Tier 1–3 seats, **11** remain live 2026 contests, **2** are uncertain after late-November 2026 PDP exits (`N.53 Bawang Assan` open seat, `N.33 Engkilili`), and **5** reflect GPS/PDP consolidation scenarios (`N.32 Simanggang`, `N.49 Ngemah`, `N.80 Batu Danau`, `N.48 Meluan`, `N.81 Ba'kelalan`).
- **GE15 (2022) DUN-Level Cross-Check:** Aggregating non-postal GE15 saluran ballots by DUN code shows GPS led **58** seats, trailed in **24** (**16** of 18 Tier 1–3 seats plus **8** Safe seats), and led by `<10 pp` in **7** more (**6** Safe seats — **14** Safe seats flagged in total).
- **Regional Concentration:** Highest share of Tier 1–3 seats is in **Northern** (`4/16 = 25.0%`), followed by **Central** (`6/26 = 23.1%`) and **Southern** (`8/40 = 20.0%`).

---

## Outputs & Visuals

| Artifact | Description |
| --- | --- |
| [`outputs/sarawak_2026_marginal_seats_report_v3.pdf`](outputs/sarawak_2026_marginal_seats_report_v3.pdf) | **Latest 8-page PDF briefing** (includes GE15 DUN-level cross-check, late-Nov 2026 PDP exit updates, PRN13 dates, data-driven tables, all 5 charts, and 64-seat Safe appendix) |
| [`outputs/sarawak_2026_marginal_seats_report_v2.pdf`](outputs/sarawak_2026_marginal_seats_report_v2.pdf) | Prior 7-page PDF briefing (pre-GE15 ballot cross-check) |
| [`outputs/marginal_seats_report.md`](outputs/marginal_seats_report.md) | Markdown analytical brief generated directly from the CSV |
| [`outputs/sarawak_2026_marginal_seats.csv`](outputs/sarawak_2026_marginal_seats.csv) | Complete 82-seat dataset (`82` rows × `88` columns) with margins, split-vote indices, 2016→2021 swings, GE15 DUN shares, saluran youth gaps, composite scores, tiers, and political context flags |

### Charts (`outputs/charts/`)
- [`sarawak_marginal_map.png`](outputs/charts/sarawak_marginal_map.png) — 82-DUN choropleth map (2015 gazetted boundaries) with zoomed Kuching and Sibu urban insets
- [`marginal_seats_ranked.png`](outputs/charts/marginal_seats_ranked.png) — 20 tightest seats by 2021 majority percentage colored by winner/runner-up bloc
- [`margin_vs_split_vote.png`](outputs/charts/margin_vs_split_vote.png) — Majority margin vs. winner vote share across all 82 seats highlighting the 14 plurality wins where 2nd + 3rd exceeded the winner
- [`undi18_turnout_saluran.png`](outputs/charts/undi18_turnout_saluran.png) — Voter-roll growth (Undi18 + AVR), 2016→2021 turnout shift, and saluran youth-stream gap for all 18 Tier 1–3 seats
- [`ge15_crosscheck.png`](outputs/charts/ge15_crosscheck.png) — 2021 state GPS margin vs. GE15 (2022) DUN-level GPS margin across all 82 seats

---

## Repository Structure

```text
.
├── data/raw/                   # 11 official Parquet/GeoJSON datasets + download_manifest.json (SHA-256)
├── scripts/
│   ├── download_data.py        # Idempotent downloader from https://lake.electiondata.my/
│   ├── analyze_marginals.py    # Seat-level metrics, composite score, tiers, CSV & Markdown report
│   ├── report_facts.py         # Shared data-derived facts module for Markdown & PDF reports
│   ├── generate_charts.py      # Generates all five 300-DPI PNG figures
│   └── build_pdf_report.py     # Renders HTML -> A4 PDF via headless Google Chrome
├── tests/
│   └── test_data_integrity.py  # Pytest suite (ballot sums, GE15 reconciliation, overrides, geometries)
├── outputs/                    # CSV, Markdown brief, PDFs (v2 & v3), and PNG charts
├── pyproject.toml              # Python 3.12 dependencies (managed by uv)
└── uv.lock                     # Locked dependency graph
```

---

## Reproducing the Pipeline

Requires [uv](https://docs.astral.sh/uv/) (Python 3.12) and Google Chrome (for PDF rendering):

```bash
uv sync --python 3.12
uv run python scripts/download_data.py
uv run python scripts/analyze_marginals.py
uv run python scripts/generate_charts.py
uv run python scripts/build_pdf_report.py   # writes outputs/sarawak_2026_marginal_seats_report.pdf
uv run pytest -v
```

---

## How This Analysis Was Created

This repository was generated end-to-end using an AI-orchestrated multi-phase workflow:

1. **Initial Discovery, Pipeline & Verification:** Planned and audited under an Orchestrator workflow (browser inspection of `https://electiondata.my/data-catalogue/`, schema verification, composite scoring methodology, automated `pytest` integrity checks, and raw Parquet spot-checks) with script implementation, data ingestion, and chart generation delegated to the execution tier.
2. **PDF Generation & Polish:** Added a headless Chrome HTML-to-PDF report builder (`scripts/build_pdf_report.py`) and visually inspected every rendered page via `pdftoppm`.
3. **Critical Review & v3 Revision:** Audited the completed analysis against raw data and late-November 2026 Sarawak political developments, then added GE15 DUN-level ballot aggregation (`ge15_ballots.parquet` + `ge15_crosscheck.png`), updated `N.53 Bawang Assan` and `N.33 Engkilili` for late-Nov 2026 PDP resignations, fixed regional density/classification errors (`N.39 Krian`, Northern vs. Central share), added PRN13 dates (`28 Nov` / `12 Dec 2026`), and refactored all report narratives to pull dynamically from the CSV via `scripts/report_facts.py`.

### Original Prompt Used

```markdown
You are running under Orchestrator (Neon). Use Gemini 4 Neon for architecture, schema inspection, methodology design, and final verification, and delegate data downloading, script implementation, testing, and chart generation to Gemini 4 Hydrogen.

## Objective
Extract official historical election datasets from https://electiondata.my and identify marginal State Legislative Assembly (DUN) seats ahead of the 2026 Sarawak State Election (82 DUN seats, N.01–N.82).

## Phase 1: Discovery & Planning (Planner — Neon)
1. **Do not scrape HTML result tables.** Use the browser tool to inspect `https://electiondata.my/data-catalogue/` and retrieve the exact direct download URLs (Parquet or CSV) from the open data lake for:
   - `Sarawak DUN Elections (PRN): Ballots` (constituency-level candidate votes)
   - `Sarawak DUN Elections (PRN): Statistics` (turnout, rejected votes, majority, registered voters)
   - `By-Elections (PRK): Ballots` and `Statistics` (to capture post-2021 Sarawak by-elections such as N.67 Jepak)
   - `Saluran-Level (Sarawak State)` (latest available Sarawak PRN ballots and statistics)
   - `Parliamentary Elections (PRU): Ballots` and `Statistics` (GE15 2022, for post-Undi18 turnout and baseline comparison)
   - `Electoral Maps: Delimitation: DUNs` (GeoJSON or GeoParquet, if directly downloadable)
2. **Fallback:** Only if direct Data Catalogue file URLs cannot be accessed programmatically, inspect `https://electiondata.my/openapi/` and pause to ask me for an `ELECTIONDATA_API_KEY` Bearer token before querying `https://api.electiondata.my/v1/`.
3. Download a sample or inspect headers first so the exact column names, seat code formatting (`N.01`–`N.82`), party/coalition identifiers, and election dates are verified before writing pipeline code.
4. Present a concise implementation plan specifying the exact files to create, the composite marginality formula, and validation checks.

## Phase 2: Data Extraction & Analysis Pipeline (Executor — Hydrogen)
Create a clean, reproducible project layout (`data/raw/`, `scripts/`, `tests/`, `outputs/`). Use Python (`pandas` or `duckdb` + `pyarrow`, `matplotlib`/`seaborn`, and `geopandas` if map data is available).

1. **Ingest & Validate:**
   - Download the verified datasets into `data/raw/` and log source URLs and timestamps.
   - Write automated checks in `tests/test_data_integrity.py` verifying:
     - All 82 Sarawak DUN seats exist for the 2021 Sarawak state election (PRN12, `2021-12-18`).
     - Sum of candidate votes matches valid votes per seat within tolerance.
     - No duplicate `(election_date, seat, candidate)` records or unexpected nulls in `votes`, `majority`, or `voters_total`.
2. **Compute Seat-Level Marginality Metrics (for all 82 DUN seats):**
   - **Baseline Margin (PRN12 2021, updated with any post-2021 PRK):** `winner_name`, `winner_party`, `winner_coalition`, `runner_up_party`, `runner_up_coalition`, `majority_votes`, `majority_perc` (% of valid votes), and `winner_vote_share_perc`.
   - **Multi-Cornered Vote-Split Vulnerability:**
     - Flag plurality wins (`winner_vote_share_perc < 50%`).
     - Compute Effective Number of Candidates (Laakso–Taagepera index) and `combined_non_winner_share`.
     - Compute `top2_opposition_combined_gap`: winner votes minus the sum of 2nd + 3rd place candidates to expose seats vulnerable to opposition consolidation.
   - **Historical Trajectory (2016 PRN11 → 2021 PRN12):**
     - Compute seat-level swing in winning coalition vote share and margin change (handling renamed or re-delimited seats carefully via seat code/name matching).
   - **Turnout & Undi18 / Youth-Stream Signals:**
     - Compare 2021 COVID-era turnout (`voter_turnout_perc`) against 2016 PRN11 turnout to flag low-turnout distortion.
     - Using Sarawak Saluran-level data (if available), compute the vote-share gap between lower-numbered saluran (older voters) and higher-numbered saluran (younger voters) per seat.
   - **Composite Marginality Score (0–100) & Tiers:**
     - Assign transparent, documented weights combining: 2021 `majority_perc` (primary), raw `majority_votes` (small-seat risk), plurality/split-vote exposure, negative historical swing, and turnout/saluran volatility.
     - Classify every seat into:
       - **Tier 1 (Razor-Thin):** `majority_perc < 5%` OR `majority_votes < 500`
       - **Tier 2 (Marginal):** `5% <= majority_perc < 10%` OR plurality win (`< 50%`) where 2nd + 3rd exceed the winner
       - **Tier 3 (Watchlist):** `10% <= majority_perc < 15%` with declining incumbent share or high turnout/saluran divergence
       - **Safe:** All remaining seats

## Phase 3: Domain Audit & Verification (Reviewer — Neon)
Before finalizing outputs, Neon must audit the computed results and run verification checks:
1. **Spot-Check Raw Numbers:** Re-verify raw ballot totals and `majority_perc` for the Top 15 ranked seats directly against the downloaded files.
2. **Sarawak Political Context Flagging (Do not distort raw math—add separate analytical columns/notes):**
   - **PSB Realignment Flag:** Flag seats where the 2021 runner-up (or winner) was **PSB** (Parti Sarawak Bersatu), noting that PSB dissolved and merged into GPS component party **PDP** in 2024. Separate *purely mathematical 2021 marginals* from *live 2026 competitive seats* (e.g., seats contested by PH/DAP/PKR, PBK, or local challengers).
   - **Electorate Size Context:** Distinguish small rural electorates (where a 500-vote swing shifts the seat by 5–10%) from large urban seats (Kuching, Sibu, Miri, Bintulu).
3. Ensure all pytest integrity checks pass cleanly.

## Required Deliverables
1. `outputs/sarawak_2026_marginal_seats.csv` — All 82 DUN seats ranked from most to least marginal, containing all computed metrics, tier labels, and the PSB realignment flag.
2. `outputs/marginal_seats_report.md` — Concise analytical brief containing:
   - Methodology and formula weights
   - Summary table of Tier 1 and Tier 2 seats (both unadjusted 2021 math and PSB-adjusted 2026 outlook)
   - Regional breakdown (Southern/Kuching, Central/Sibu-Kapit, Northern/Bintulu-Miri-Limbang)
   - Key data caveats (2021 low turnout, Undi18 voter roll expansion, party realignments)
3. `outputs/charts/` — High-resolution PNG charts:
   - `marginal_seats_ranked.png`: Horizontal bar chart of the 20 tightest seats colored by incumbent/challenger bloc
   - `margin_vs_split_vote.png`: Scatter plot of 2021 `majority_perc` vs. `winner_vote_share_perc` highlighting plurality-win seats
   - `sarawak_marginal_map.png`: Choropleth map of marginality tiers across the 82 DUNs (if DUN boundary GeoJSON/GeoParquet is available)
```

---

## Data Attribution

All historical election results, saluran datasets, and electoral boundary geometries are sourced from [electiondata.my](https://electiondata.my) under CC0 Public Domain. Exact URLs, timestamps, and SHA-256 digests are recorded in [`data/raw/download_manifest.json`](data/raw/download_manifest.json).
