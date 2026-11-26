# Sarawak 2026 State Election (PRN13): Marginal DUN Seats Analysis

_PRN13 nomination: 28 Nov 2026; polling: 12 Dec 2026 (existing 82 seats). Political context as of 26 Nov 2026._

## Executive Summary

Across all **82 Sarawak State Legislative Assembly (DUN) seats (`N.01`–`N.82`)** evaluated from official 2016 PRN11, 2021 PRN12, the 2023 `N.67 Jepak` by-election, 2021 SE-12 saluran results, and GE15 (2022) saluran results:

- **Unadjusted 2021/PRK baseline:** **6** Tier 1 (Razor-Thin), **9** Tier 2 (Marginal), **3** Tier 3 (Watchlist) and **64** Safe seats (**18** non-safe).
- **Vote-splitting exposure:** **16** seats were won with <50% of valid votes; in **14** the combined 2nd + 3rd place vote exceeded the winner (largest gaps: `N.54 Pelawan` (-3,657), `N.68 Tanjong Batu` (-2,181)).
- **Post-PSB 2026 outlook (scenario, not forecast):** PSB was 2021 winner or runner-up in **53** seats (9 of the 18 Tier 1–3 seats). Of the 18 Tier 1–3 seats: **11 live 2026 contests**, **2 uncertain** (`N.53 Bawang Assan`, `N.33 Engkilili` — ex-PSB incumbents who quit PDP in late Nov 2026), and **5 GPS/PDP consolidation scenarios** that assume former PSB voters follow PSB into GPS.
- **GE15 (2022) cross-check:** GPS trailed the strongest non-GPS bloc at DUN level in **24** of 82 seats (16 of them Tier 1–3) and led by <10 pp in another **7**. **14** seats rated Safe on 2021 numbers were trailing or within 10 pp in GE15: `N.02 Tasik Biru`, `N.38 Kalaka`, `N.52 Dudong`, `N.01 Opar`, `N.73 Piasau`, `N.40 Kabong`, `N.14 Batu Kawah`, `N.75 Senadin`, `N.50 Machan`, `N.13 Batu Kitang`, `N.45 Repok`, `N.31 Bukit Begunan`, `N.77 Telang Usan`, `N.59 Tamin`.

| Marginality Tier | Seats | % of 82 | Live 2026 | Uncertain 2026 | GPS Consolidation |
| --- | --- | --- | --- | --- | --- |
| Tier 1 (Razor-Thin) | 6 | 7.3% | 4 | 0 | 2 |
| Tier 2 (Marginal) | 9 | 11.0% | 6 | 2 | 1 |
| Tier 3 (Watchlist) | 3 | 3.7% | 1 | 0 | 2 |
| Safe | 64 | 78.0% | 0 | 0 | 0 |

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

| Rank | Seat | Tier | Score | 2021 Winner | 2nd Place | 3rd Place | Majority | Top2 Opp Gap | 16→21 Swing | Youth Gap | Size | Roll Growth (Undi18+AVR) | GE15 GPS Margin | 2026 Outlook |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `N.11 Batu Lintang` | Tier 1 | 91.1 | PSB/ALONE (35.9%) | SUPP/GPS (35.1%) | PKR (14.8%) | 0.75% (93) | -1,730 | -25.8 pp | +3.3 pp | Large | +55.9% | -49.1 pp | Live 2026 Competitive (Ex-PSB Independent Incumbent) |
| 2 | `N.54 Pelawan` | Tier 1 | 84.9 | SUPP/GPS (27.7%) | DAP/PH (27.1%) | PSB (23.6%) | 0.63% (100) | -3,657 | -11.3 pp | -0.8 pp | Large | +45.9% | -53.1 pp | Live 2026 Competitive (PH/Local Challenger) |
| 3 | `N.68 Tanjong Batu` | Tier 1 | 79.6 | SUPP/GPS (35.4%) | DAP/PH (35.2%) | PBK (19.1%) | 0.20% (23) | -2,181 | -4.9 pp | +1.8 pp | Large | +66.3% | -16.0 pp | Live 2026 Competitive (PH/Local Challenger) |
| 4 | `N.10 Pending` | Tier 1 | 79.0 | DAP/PH (40.3%) | SUPP/GPS (36.1%) | PSB (14.4%) | 4.19% (540) | -1,318 | -22.3 pp | -2.2 pp | Large | +29.0% | -42.5 pp | Live 2026 Competitive (PH/Local Challenger) |
| 5 | `N.51 Bukit Assek` | Tier 2 | 65.6 | SUPP/GPS (34.9%) | DAP/PH (28.4%) | PBK (19.4%) | 6.52% (874) | -1,724 | -2.0 pp | -8.0 pp | Large | +26.5% | -42.5 pp | Live 2026 Competitive (PH/Local Challenger) |
| 6 | `N.34 Batang Ai` | Tier 2 | 64.5 | PRS/GPS (44.6%) | BEBAS/ALONE (34.3%) | PSB (19.0%) | 10.26% (738) | -628 | -29.6 pp | -2.0 pp | Small | +43.7% | +2.7 pp | Live 2026 Competitive (PH/Local Challenger) |
| 7 | `N.53 Bawang Assan` | Tier 2 | 64.3 | PSB/ALONE (43.2%) | SUPP/GPS (36.6%) | DAP (8.5%) | 6.63% (913) | -260 | -18.4 pp | +2.0 pp | Medium | +14.6% | -9.8 pp | Uncertain 2026 (Open Seat: Ex-PSB Incumbent Left PDP, Not Defending) |
| 8 | `N.32 Simanggang` | Tier 1 | 62.9 | SUPP/GPS (48.9%) | PSB/ALONE (46.8%) | DAP (2.6%) | 2.17% (175) | -37 | -1.8 pp | -3.4 pp | Medium | +55.7% | -5.1 pp | GPS Consolidation (PSB Runner-up Merged into PDP) |
| 9 | `N.47 Pakan` | Tier 2 | 59.6 | PBB/GPS (41.1%) | BEBAS/ALONE (32.1%) | PSB (18.7%) | 8.99% (714) | -770 | -9.8 pp | -1.4 pp | Medium | +31.0% | -19.8 pp | Live 2026 Competitive (PH/Local Challenger) |
| 10 | `N.49 Ngemah` | Tier 1 | 58.9 | PRS/GPS (46.2%) | PSB/ALONE (42.4%) | PBDSB (5.1%) | 3.78% (261) | -93 | +0.1 pp | -5.7 pp | Small | +43.2% | -1.6 pp | GPS Consolidation (PSB Runner-up Merged into PDP) |
| 11 | `N.33 Engkilili` | Tier 2 | 57.6 | PSB/ALONE (43.5%) | SUPP/GPS (27.5%) | BEBAS (27.0%) | 15.95% (1,191) | -822 | -27.3 pp | +4.7 pp | Medium | +33.4% | -8.1 pp | Uncertain 2026 (Ex-PSB Incumbent Left PDP Nov 2026) |
| 13 | `N.39 Krian` | Tier 2 | 50.9 | PDP/GPS (43.7%) | PSB/ALONE (33.2%) | BEBAS (20.0%) | 10.48% (932) | -845 | +2.6 pp | -2.8 pp | Medium | +39.2% | -52.2 pp | Live 2026 Competitive (PH/Local Challenger) |
| 15 | `N.48 Meluan` | Tier 2 | 44.5 | PDP/GPS (53.2%) | PSB/ALONE (44.9%) | PBK (1.9%) | 8.30% (822) | +636 | +15.8 pp | -5.4 pp | Medium | +37.9% | -39.5 pp | GPS Consolidation (PSB Runner-up Merged into PDP) |
| 16 | `N.12 Kota Sentosa` | Tier 2 | 44.0 | SUPP/GPS (43.0%) | DAP/PH (30.6%) | PSB (17.3%) | 12.48% (1,683) | -645 | +1.2 pp | +0.0 pp | Large | +61.0% | -29.9 pp | Live 2026 Competitive (PH/Local Challenger) |
| 17 | `N.74 Pujut` | Tier 2 | 43.0 | SUPP/GPS (44.9%) | DAP/PH (32.2%) | PSB (13.5%) | 12.64% (1,566) | -101 | +2.7 pp | +1.9 pp | Large | +59.2% | -20.1 pp | Live 2026 Competitive (PH/Local Challenger) |

### Tier 3 (Watchlist) Seats

| Rank | Seat | Score | 2021 Winner | 2nd Place | Majority | 16→21 Swing | Turnout Δ | Youth Gap | GE15 GPS Margin | 2026 Outlook |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | `N.80 Batu Danau` | 53.1 | PBB/GPS (53.1%) | PSB/ALONE (40.8%) | 12.38% (706) | -22.2 pp | -6.5 pp | -3.1 pp | +45.0 pp | GPS Consolidation (PSB Runner-up Merged into PDP) |
| 14 | `N.09 Padungan` | 50.1 | DAP/PH (50.4%) | SUPP/GPS (37.5%) | 12.89% (1,198) | -13.9 pp | -20.7 pp | +1.5 pp | -45.0 pp | Live 2026 Competitive (PH/Local Challenger) |
| 18 | `N.81 Ba'kelalan` | 39.3 | PSB/ALONE (54.7%) | PDP/GPS (40.8%) | 13.83% (680) | -0.5 pp | -12.1 pp | +5.8 pp | -20.9 pp | GPS Consolidation (PSB Incumbent Merged into PDP) |

---

## GE15 Seat-Level Cross-Check (GPS trailed or within 10 pp)

| Seat | Tier | 2021 GPS Margin (pp) | GE15 GPS | GE15 PH | GE15 PN | GE15 PSB | GE15 Other | GE15 GPS Margin (pp) | GE15 Leader |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `N.54 Pelawan` | Tier 1 | +0.6 | 19.6% | 72.7% | 0.0% | 7.7% | 0.0% | -53.1 | PH |
| `N.39 Krian` | Tier 2 | +10.5 | 21.8% | 4.2% | 74.0% | 0.0% | 0.0% | -52.2 | PN |
| `N.11 Batu Lintang` | Tier 1 | -0.8 | 23.7% | 72.8% | 0.0% | 3.5% | 0.0% | -49.1 | PH |
| `N.09 Padungan` | Tier 3 | -12.9 | 26.5% | 71.5% | 0.0% | 2.0% | 0.0% | -45.0 | PH |
| `N.51 Bukit Assek` | Tier 2 | +6.5 | 25.5% | 68.1% | 0.0% | 5.5% | 0.9% | -42.5 | PH |
| `N.10 Pending` | Tier 1 | -4.2 | 27.5% | 70.0% | 0.0% | 2.5% | 0.0% | -42.5 | PH |
| `N.48 Meluan` | Tier 2 | +8.3 | 30.3% | 0.0% | 0.0% | 0.0% | 69.7% | -39.5 | OTHER |
| `N.12 Kota Sentosa` | Tier 2 | +12.5 | 33.4% | 63.3% | 0.0% | 3.3% | 0.0% | -29.9 | PH |
| `N.02 Tasik Biru` | Safe | +35.8 | 35.5% | 59.1% | 0.0% | 0.0% | 5.5% | -23.6 | PH |
| `N.81 Ba'kelalan` | Tier 3 | -13.8 | 38.4% | 2.4% | 0.0% | 59.3% | 0.0% | -20.9 | PSB |
| `N.74 Pujut` | Tier 2 | +12.6 | 37.4% | 57.5% | 0.0% | 5.2% | 0.0% | -20.1 | PH |
| `N.38 Kalaka` | Safe | +53.4 | 37.8% | 4.5% | 57.7% | 0.0% | 0.0% | -19.9 | PN |
| `N.47 Pakan` | Tier 2 | +9.0 | 40.1% | 0.0% | 0.0% | 0.0% | 59.9% | -19.8 | OTHER |
| `N.68 Tanjong Batu` | Tier 1 | +0.2 | 40.1% | 56.1% | 3.8% | 0.0% | 0.0% | -16.0 | PH |
| `N.52 Dudong` | Safe | +29.1 | 40.5% | 51.0% | 0.0% | 7.3% | 1.3% | -10.5 | PH |
| `N.01 Opar` | Safe | +21.6 | 39.8% | 49.7% | 0.0% | 0.0% | 10.5% | -9.9 | PH |
| `N.53 Bawang Assan` | Tier 2 | -6.6 | 29.0% | 32.2% | 0.0% | 38.8% | 0.0% | -9.8 | PSB |
| `N.73 Piasau` | Safe | +48.9 | 42.5% | 51.6% | 0.0% | 5.9% | 0.0% | -9.1 | PH |
| `N.33 Engkilili` | Tier 2 | -15.9 | 32.6% | 4.0% | 22.7% | 40.7% | 0.0% | -8.1 | PSB |
| `N.40 Kabong` | Safe | +38.8 | 45.5% | 3.4% | 51.2% | 0.0% | 0.0% | -5.7 | PN |
| `N.32 Simanggang` | Tier 1 | +2.2 | 40.7% | 8.6% | 0.0% | 45.8% | 4.9% | -5.1 | PSB |
| `N.14 Batu Kawah` | Safe | +48.4 | 47.6% | 49.5% | 0.0% | 2.9% | 0.0% | -2.0 | PH |
| `N.75 Senadin` | Safe | +44.9 | 45.1% | 46.9% | 0.0% | 8.0% | 0.0% | -1.8 | PH |
| `N.49 Ngemah` | Tier 1 | +3.8 | 37.9% | 39.5% | 0.0% | 0.0% | 22.7% | -1.6 | PH |
| `N.50 Machan` | Safe | +27.0 | 42.3% | 41.2% | 0.0% | 0.0% | 16.5% | +1.1 | GPS |
| `N.34 Batang Ai` | Tier 2 | +10.3 | 36.0% | 3.7% | 33.3% | 26.9% | 0.0% | +2.7 | GPS |
| `N.13 Batu Kitang` | Safe | +38.1 | 49.9% | 47.1% | 0.0% | 2.9% | 0.0% | +2.8 | GPS |
| `N.45 Repok` | Safe | +53.3 | 53.2% | 46.8% | 0.0% | 0.0% | 0.0% | +6.4 | GPS |
| `N.31 Bukit Begunan` | Safe | +20.3 | 39.9% | 2.2% | 0.0% | 30.8% | 27.1% | +9.1 | GPS |
| `N.77 Telang Usan` | Safe | +37.5 | 54.3% | 45.2% | 0.0% | 0.0% | 0.5% | +9.1 | GPS |
| `N.59 Tamin` | Safe | +30.0 | 52.1% | 42.4% | 0.0% | 0.0% | 5.5% | +9.8 | GPS |

GE15 was a federal contest with different candidates; PH (DAP/PKR) typically polls better in federal than state contests in urban Sarawak, so treat these as an upper bound on opposition strength rather than a state-election forecast.

---

## Regional Breakdown

| Region | Seats | T1 | T2 | T3 | Safe | Non-Safe % | Live | Uncertain | Consolidated | Median Maj % | Median Roll Growth | GE15 GPS Trailed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Southern (Kuching-Samarahan-Serian-Sri Aman-Betong) | 40 | 3 | 4 | 1 | 32 | 20.0% | 6 | 1 | 1 | 40.5% | +49.3% | 12 |
| Central (Sarikei-Sibu-Mukah-Kapit) | 26 | 2 | 4 | 0 | 20 | 23.1% | 3 | 1 | 2 | 37.8% | +44.7% | 7 |
| Northern (Bintulu-Miri-Limbang-Lawas) | 16 | 1 | 1 | 2 | 12 | 25.0% | 2 | 0 | 2 | 50.2% | +58.7% | 5 |

- **Southern (N.01–N.40, 40 DUNs):** 8 of 40 seats are Tier 1–3 (20.0%). Live 2026: `N.11 Batu Lintang`, `N.10 Pending`, `N.34 Batang Ai`, `N.39 Krian`, `N.09 Padungan`, `N.12 Kota Sentosa`. Uncertain: `N.33 Engkilili`. GPS-consolidation scenario: `N.32 Simanggang`. GPS trailed at DUN level in GE15 in 12 seat(s): `N.11 Batu Lintang`, `N.10 Pending`, `N.32 Simanggang`, `N.33 Engkilili`, `N.39 Krian`, `N.09 Padungan`, `N.12 Kota Sentosa`, `N.01 Opar`, `N.02 Tasik Biru`, `N.40 Kabong`, `N.38 Kalaka`, `N.14 Batu Kawah`.
- **Central (N.41–N.66, 26 DUNs):** 6 of 26 seats are Tier 1–3 (23.1%). Live 2026: `N.54 Pelawan`, `N.51 Bukit Assek`, `N.47 Pakan`. Uncertain: `N.53 Bawang Assan`. GPS-consolidation scenario: `N.49 Ngemah`, `N.48 Meluan`. GPS trailed at DUN level in GE15 in 7 seat(s): `N.54 Pelawan`, `N.51 Bukit Assek`, `N.53 Bawang Assan`, `N.47 Pakan`, `N.49 Ngemah`, `N.48 Meluan`, `N.52 Dudong`.
- **Northern (N.67–N.82, 16 DUNs):** 4 of 16 seats are Tier 1–3 (25.0%). Live 2026: `N.68 Tanjong Batu`, `N.74 Pujut`. Uncertain: none. GPS-consolidation scenario: `N.80 Batu Danau`, `N.81 Ba'kelalan`. GPS trailed at DUN level in GE15 in 5 seat(s): `N.68 Tanjong Batu`, `N.74 Pujut`, `N.81 Ba'kelalan`, `N.73 Piasau`, `N.75 Senadin`.

The highest share of Tier 1–3 seats is in **Northern** (4/16 = 25.0%).

---

## Key Data Caveats & 2026 Context

1. **2021 COVID-era turnout:** Mean turnout fell from **70.5%** in 2016 (80 contested seats) to **63.3%** in 2021 (mean change -7.0 pp). Largest drops among Tier 1–3 seats: `N.54 Pelawan` (-22.9 pp), `N.10 Pending` (-22.0 pp), `N.09 Padungan` (-20.7 pp), `N.11 Batu Lintang` (-20.6 pp).
2. **Voter-roll growth (Undi18 + automatic registration):** PRN12 preceded both reforms. GE15 non-postal DUN rolls were a median **+52.0%** larger (from +14.6% in `N.53 Bawang Assan` to +101.0% in `N.75 Senadin`). Growth reflects all newly auto-registered adults, not only 18–20-year-olds; the 2026 roll will be larger again.
3. **PSB realignment is a scenario assumption:** PSB dissolved into GPS component PDP in Apr 2024. The consolidation label assumes former PSB voters follow; many 2021 PSB votes were anti-GPS protest votes. Seats treated as consolidation: `N.32 Simanggang`, `N.49 Ngemah`, `N.80 Batu Danau`, `N.48 Meluan`, `N.81 Ba'kelalan`. `N.11 Batu Lintang` stays live: incumbent See Chee How left PSB in Aug 2022 and sits as an Independent.
4. **Late-Nov 2026 changes:** `N.53 Bawang Assan`: Ex-PSB incumbent Wong Soon Koh joined PDP in Apr 2024 but quit PDP in late Nov 2026 and said he will not defend the seat (while stating continued support for GPS), leaving an open seat. `N.33 Engkilili`: Ex-PSB incumbent Johnichal Rayong joined PDP in Apr 2024 but quit PDP in late Nov 2026 (while stating continued support for GPS); his 2026 candidacy and alignment are unsettled.
5. **Edge cases:**
   - **`N.67 Jepak` by-election (2023-11-04):** PBB/GPS won 88.24% (majority 8,784 / 80.42%, turnout 48.57%), replacing its 2021 baseline (46.94% majority, 62.96% turnout).
   - **2016 uncontested seats:** `N.82 Bukit Sari`, `N.79 Bukit Kota` — 2016–2021 swing and turnout change are N/A and excluded from averages.
   - **Single-saluran seats:** `N.64 Baleh` had no multi-saluran ordinary polling centres in 2021, so the youth-stream gap is N/A.
6. **Method limits:** For Tier 1–3 seats the average score is 60.7, of which 40.0 points come from the two 2021-margin terms (Baseline % majority 29.4/40, Raw-vote majority 10.6/15, Plurality & split-vote 10.7/20, 2016→2021 swing 6.1/15, Turnout & saluran volatility 4.0/10) — the score is largely a margin ranking. Tier rules and score order can disagree: `N.39 Krian`, `N.48 Meluan`, `N.12 Kota Sentosa`, `N.74 Pujut` are Tier 2 but rank below the top Tier 3 seat; `N.33 Engkilili` is Tier 2 at 15.95% majority while `N.30 Balai Ringin` (15.04%) are Safe with smaller majorities. The saluran youth gap is a crude half-split proxy.
7. **GE15 caveat:** federal contest, different candidates, PSB contested federally, postal votes excluded (~2% of votes).
