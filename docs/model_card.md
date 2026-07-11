# CourtVision Model Card

## Overview

CourtVision forecasts 2026–27 NBA standings and postseason outcomes after applying verified offseason player trades.

The project contains three connected models:

1. A regular-season team baseline
2. A player and trade impact model
3. A Monte Carlo postseason simulator

## Intended Use

CourtVision is designed for:

- Sports analytics education
- Data-engineering demonstrations
- Machine-learning portfolio review
- NBA transaction scenario analysis
- Reproducible statistical research

It is not intended for gambling, financial decisions, medical prediction, or professional player evaluation.

## Data

### Historical games

- Seasons: 2015–16 through 2025–26
- Games: 13,209
- Teams: 30
- Source: NBA statistics endpoints

### Player statistics

- Seasons: 2023–24 through 2025–26
- Player-season rows: 1,723
- Unique players: 802
- Traded players matched by NBA ID: 40/40

### Transaction ledger

- Snapshot date: July 11, 2026
- Asset rows: 96
- Transactions: 13
- Official transactions: 11
- Non-official scenarios: 2

Only official transactions affect the default forecast. Reported and on-hold transactions remain separate scenarios.

## Regular-Season Baseline

The baseline predicts a team’s current-season win percentage using information available before that season.

### Features

- Previous win percentage
- Previous points scored per game
- Previous points allowed per game
- Previous average point margin
- Previous two-season win percentage
- Previous two-season average margin

All performance features are lagged to prevent target leakage.

### Time-aware split

| Split | Seasons |
|---|---|
| Training | Through 2023–24 |
| Validation | 2024–25 |
| Final untouched test | 2025–26 |

The data is not randomly shuffled because future seasons must not be used to predict past seasons.

### Candidate models

- Mean prediction baseline
- Ridge regression with several regularization strengths
- Random forest regression

The selected model was Ridge regression with `alpha=1`.

## Performance

| Evaluation | MAE wins | RMSE wins |
|---|---:|---:|
| 2024–25 validation | 8.16 | 10.60 |
| 2025–26 untouched test | 9.56 | 11.63 |

The 2025–26 test season was not used for model selection.

The honest 9.56-win test error is included in the Monte Carlo simulator instead of being hidden.

## Player Impact

Player value uses the NBA Player Impact Estimate, playing time, and availability.

### Recency weights

| Season | Weight |
|---|---:|
| 2023–24 | 0.15 |
| 2024–25 | 0.30 |
| 2025–26 | 0.55 |

Replacement level is the median 2025–26 PIE among players who:

- Played at least 20 games
- Averaged between 8 and 18 minutes per game

The calculated replacement-level PIE was `0.0775`.

### Estimated wins above replacement

The transparent formula is:

`(weighted PIE - replacement PIE) × (weighted minutes / 48) × weighted availability × 82`

This value is a CourtVision estimate, not an official NBA statistic.

## Trade Impact

For each team:

`trade win delta = player value received - player value sent`

League-wide player-trade adjustments sum to zero because each player leaves one team and joins another.

Draft picks and draft rights remain in the ledger but do not receive immediate 2026–27 on-court value.

## Monte Carlo Simulator

Default settings:

| Setting | Value |
|---|---:|
| Simulations | 20,000 |
| Random seed | 42 |
| Forecast uncertainty | 9.56 MAE wins |
| Historical home win rate | 0.564 |
| Home-court adjustment | 0.064 |

Each simulation:

1. Samples regular-season forecast error
2. Rebuilds conference standings
3. Simulates seeds 7–10 through the Play-In
4. Simulates every best-of-seven series
5. Uses a 2-2-1-1-1 home-court structure
6. Records ECF, WCF, Finals, and championship outcomes

Game probabilities use the Log5 formula plus historical home advantage.

## Validation Rules

Every completed simulation must produce:

- 30 teams
- 15 teams in each conference
- 8 playoff teams per conference
- 4 second-round teams per conference
- 2 conference-final teams per conference
- 1 NBA Finals team per conference
- Championship probabilities totaling exactly 1.0

## Current Results

Top championship probabilities from the official transaction scenario:

| Team | Probability |
|---|---:|
| San Antonio Spurs | 12.0% |
| Oklahoma City Thunder | 9.5% |
| Detroit Pistons | 9.1% |
| New York Knicks | 5.4% |
| Houston Rockets | 5.4% |

## Limitations

1. The model focuses on trades and does not model every free-agent signing.
2. Future injuries cannot be known.
3. Historical availability may not equal future availability.
4. PIE may undervalue low-usage defenders and lineup fit.
5. Traded players may receive different minutes or roles.
6. Coaching and tactical changes are not modeled directly.
7. Rookies have limited NBA performance history.
8. Draft assets receive no immediate on-court value.
9. The final test error is large enough that standings uncertainty must remain broad.
10. Results become stale when transaction statuses change.

## Reproducibility

The repository includes:

- Stable NBA player IDs
- Cached raw downloads
- A permanent transaction validator
- Chronological train, validation, and test splits
- Fixed simulation seeds
- Published result snapshots
- Automated regression tests
- GitHub Actions quality checks