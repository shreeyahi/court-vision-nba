# CourtVision Model Card

## Overview

CourtVision forecasts 2026–27 NBA standings and postseason outcomes from complete projected rosters as of July 15, 2026.

The system contains four connected components:

1. Historical regular-season team baseline
2. Player age and career-stage projection model
3. Rookie and current-injury projection layers
4. Monte Carlo regular-season and postseason simulator

## Intended Use

CourtVision is designed for sports-analytics education, reproducible data engineering, portfolio review, and NBA roster scenario analysis.

It is not intended for gambling, medical prediction, financial decisions, or professional player evaluation.

## Data

### Historical games

- Seasons: 2015–16 through 2025–26
- Games: 13,209
- Teams: 30
- Source: NBA statistics endpoints

### Player statistics

- Seasons: 2015–16 through 2025–26
- Player-season rows: 5,968
- Unique players: 1,554
- Fields include age, games, minutes, PPG, points per 36, PIE, ratings, efficiency, usage, and availability

### Projected rosters

- Base: official 2025–26 NBA team rosters
- Official trades and roster moves applied
- 2026 draft class: 60 players
- Final projected player rows: 592
- Team-minute requirement: exactly 240 regulation minutes per game

### Manual auditable inputs

- `trades_2026.csv`: trade assets and transaction states
- `roster_moves_2026.csv`: additional team-changing movements
- `rookies_2026.csv`: official 2026 draft snapshot
- `injuries_2026.csv`: sourced current injuries and explicit modeling assumptions

## Regular-Season Baseline

The baseline predicts win percentage using only lagged team information:

- Previous win percentage
- Previous points scored per game
- Previous points allowed per game
- Previous average point margin
- Previous two-season win percentage
- Previous two-season average margin

| Split | Seasons |
|---|---|
| Training | Through 2023–24 |
| Validation | 2024–25 |
| Final untouched test | 2025–26 |

Candidate models include a mean baseline, Ridge regression, and random forest. Ridge with `alpha=1` won the validation comparison.

| Evaluation | MAE wins | RMSE wins |
|---|---:|---:|
| 2024–25 validation | 8.16 | 10.60 |
| 2025–26 untouched test | 9.56 | 11.63 |

The 9.56-win test MAE is included as uncertainty in the Monte Carlo simulation.

## Player Development Model

Player seasons are paired only with the immediately following season. Changes are estimated for:

- Player Impact Estimate
- Minutes per game
- Points per 36 minutes
- Availability

Forecast groups describe the predicted 2026–27 season:

- Rookie: zero completed NBA seasons
- Sophomore: one completed season
- Third-year: two completed seasons
- Veterans: age bands from 24-and-under through 37-plus

Sophomores and third-year players use career-stage groups. Veteran players use age bands. This prevents separate age and experience effects from double-counting the same development.

Group changes are winsorized at the 5th and 95th percentiles and shrunk toward the league mean with a prior strength of 40 observations.

### Held-out 2025–26 player backtest

| Target | Rows | No-change MAE | Curve MAE | Selected model |
|---|---:|---:|---:|---|
| PIE | 424 | 0.017337 | **0.017283** | Development curve |
| Minutes per game | 424 | 4.603302 | **4.434008** | Development curve |
| Points per 36 | 424 | 2.579846 | **2.555421** | Development curve |
| Availability | 424 | 0.222734 | **0.219899** | Development curve |

If a development curve does not beat the no-change forecast, CourtVision automatically uses a zero adjustment for that target.

## Scoring Projection

PPG is an explanation output, not an additional win feature:

`points per 36 = PPG / MPG × 36`

`projected PPG = projected points per 36 × projected MPG / 36`

This prevents scoring from being counted once through PIE and again through raw PPG.

## Rookie Model

CourtVision does not assign zero impact to players without NBA history. It estimates rookie PIE, role, scoring rate, and availability from the 2015–2025 draft classes.

Draft buckets:

- Picks 1–3
- Picks 4–10
- Picks 11–20
- Picks 21–30
- Second round
- Undrafted or international

Bucket estimates are shrunk toward the overall rookie mean with a prior strength of 25 players. Players who were drafted but did not appear during their rookie NBA season remain in the historical availability and role calculation.

Summer League data receives zero weight because CourtVision has not validated a Summer League-to-NBA translation model.

## Injury and Availability Model

Every player receives a historical availability projection. Known current injuries may replace it with low, base, and high availability and return-effectiveness scenarios.

Current overrides:

- Kyrie Irving
- Jimmy Butler III
- Moses Moody
- Dereck Lively II

Every override requires a source URL and verification date. The source establishes injury or recovery status; numeric scenarios are CourtVision assumptions and are not medical timelines.

The base scenario determines the published standings. Low and high scenarios create team-specific injury-win ranges sampled by the Monte Carlo simulator.

## Full-Roster Value

Replacement level is the median 2025–26 PIE among players who played at least 20 games and averaged 8–18 minutes. The current replacement PIE is `0.0775`.

For each injury scenario:

`effective PIE = replacement PIE + (projected PIE - replacement PIE) × return effectiveness`

`player value = (effective PIE - replacement PIE) × allocated season minutes / 48 × 82`

Projected minutes are normalized to exactly 240 per team. Injury absences therefore move minutes toward teammates instead of creating impossible extra playing time.

`roster win delta = projected 2026-27 roster value - actual 2025-26 roster value`

`adjusted team wins = historical baseline wins + roster win delta`

League records are re-centered and integerized to exactly 1,230 wins and 1,230 losses.

## Monte Carlo Simulator

| Setting | Value |
|---|---:|
| Simulations | 20,000 |
| Random seed | 42 |
| Team forecast uncertainty | 9.56 MAE wins |
| Historical home win rate | 0.564 |
| Home-court adjustment | 0.064 |

Each simulation:

1. Samples team forecast error
2. Samples team-specific injury uncertainty
3. Rebuilds conference standings
4. Simulates seeds 7–10 through the Play-In
5. Simulates every best-of-seven series
6. Records ECF, WCF, NBA Finals, and championship results

Game probabilities use Log5 plus historical home advantage. Series use a 2-2-1-1-1 home-court structure.

## Validation Rules

Automated checks require:

- 30 teams and 15 per conference
- 60 2026 draft rows
- Exactly 240 projected minutes per team
- Forecast-season rookie, sophomore, and third-year labels
- Valid low ≤ base ≤ high injury ranges
- Source URLs for every injury override
- 1,230 league wins and losses
- Eight playoff teams per conference
- Championship probabilities summing to 1.0
- Reproducible simulation output from a fixed seed

## Current Results

| Team | Championship probability |
|---|---:|
| Oklahoma City Thunder | 9.80% |
| San Antonio Spurs | 9.64% |
| Detroit Pistons | 7.22% |
| Cleveland Cavaliers | 6.04% |
| Houston Rockets | 5.49% |

Close probabilities should not be treated as meaningful certainty given the team model's 9.56-win test error.

## Limitations

1. The 2026 offseason remains active.
2. Injury scenarios are assumptions, not medical forecasts.
3. Rookie priors do not directly model college competition, position, or team fit.
4. Summer League is excluded.
5. PIE can miss defense, lineup chemistry, and low-usage impact.
6. Training-camp role changes are unknown.
7. Coaching and tactical changes are not modeled directly.
8. The team-level test error is large enough that close seeds remain highly uncertain.
9. Results become stale when transactions or injury statuses change.

## Reproducibility

The repository publishes source ledgers, fixed seeds, chronological tests, player backtest metrics, development curves, player projections, team roster deltas, standings, and automated regression tests.
