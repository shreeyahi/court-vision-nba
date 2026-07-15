# CourtVision Data Dictionary

## Manual Trade Ledger

File: `data/manual/trades_2026.csv`

| Column | Description |
|---|---|
| `transaction_id` | Stable identifier shared by all assets in one transaction |
| `announced_date` | Date first announced |
| `effective_date` | Date the move became official |
| `from_team` | Sending team abbreviation |
| `to_team` | Receiving team abbreviation |
| `asset_type` | PLAYER, DRAFT_PICK, PICK_SWAP, DRAFT_RIGHTS, or CASH |
| `asset_name` | Human-readable asset |
| `player_id` | Official NBA player ID when applicable |
| `status` | OFFICIAL, REPORTED, or ON_HOLD |
| `source_url` | Verification source |
| `source_updated_at` | Source date |
| `verified_at_utc` | CourtVision verification date |
| `notes` | Audit notes |

## Additional Roster Movements

File: `data/manual/roster_moves_2026.csv`

| Column | Description |
|---|---|
| `movement_id` | Stable movement identifier |
| `from_team` | Previous team or origin |
| `to_team` | New team |
| `player_name` | Player name |
| `player_id` | Official NBA player ID when available |
| `movement_type` | Free agency, waiver, sign-and-trade, or related movement |
| `status` | OFFICIAL or REPORTED |
| `source_url` | Verification source |
| `source_updated_at` | Source date |
| `verified_at_utc` | CourtVision verification date |
| `notes` | Audit notes |

## 2026 Rookie Ledger

File: `data/manual/rookies_2026.csv`

| Column | Description |
|---|---|
| `player_id` | NBA player ID when the Draft History endpoint provides one |
| `player_name` | Drafted player |
| `draft_year` | 2026 |
| `draft_round` | Round 1 or 2 |
| `overall_pick` | Overall selection number, 1–60 |
| `team` | Team holding the player after the recorded draft-night movement snapshot |
| `source_url` | Official NBA draft-results page |
| `source_updated_at` | Source update date |
| `verified_at_utc` | CourtVision verification date |

## Current Injury Ledger

File: `data/manual/injuries_2026.csv`

| Column | Description |
|---|---|
| `player_id` | Official NBA player ID |
| `player_name` | Player name |
| `team` | Projected team |
| `injury_status` | RETURNING or REHAB |
| `availability_low` | Pessimistic share of 82 games available |
| `availability_base` | Base-case share of games available |
| `availability_high` | Optimistic share of games available |
| `return_effectiveness_low` | Pessimistic post-return effectiveness multiplier |
| `return_effectiveness_base` | Base effectiveness multiplier |
| `return_effectiveness_high` | Optimistic effectiveness multiplier |
| `source_url` | Official injury/recovery source |
| `source_updated_at` | Source date |
| `verified_at_utc` | CourtVision verification date |
| `notes` | Separates source facts from CourtVision assumptions |

## Historical Games

Generated file: `data/processed/games.parquet`

| Column | Description |
|---|---|
| `game_id` | Official NBA game identifier |
| `game_date` | Game date |
| `season` | NBA season |
| `home_team_id` | Official home-team ID |
| `home_team` | Home-team abbreviation |
| `away_team_id` | Official away-team ID |
| `away_team` | Away-team abbreviation |
| `home_points` | Home points |
| `away_points` | Away points |
| `home_win` | 1 for a home win, otherwise 0 |
| `point_margin` | Home points minus away points |

## Player-Season Statistics

Generated file: `data/processed/player_seasons.parquet`

| Column | Description |
|---|---|
| `season` | NBA season, 2015–16 through 2025–26 |
| `player_id` | Official NBA player ID |
| `player_name` | Player name |
| `team` | Team abbreviation |
| `age` | NBA-reported age |
| `games_played` | Regular-season appearances |
| `minutes_per_game` | Average minutes |
| `points_per_game` | Average points |
| `points_per_36` | Scoring normalized to 36 minutes |
| `rebounds_per_game` | Average rebounds |
| `assists_per_game` | Average assists |
| `steals_per_game` | Average steals |
| `blocks_per_game` | Average blocks |
| `turnovers_per_game` | Average turnovers |
| `plus_minus_per_game` | Average plus-minus |
| `offensive_rating` | NBA offensive rating |
| `defensive_rating` | NBA defensive rating |
| `net_rating` | Offensive minus defensive rating |
| `effective_field_goal_percentage` | Shooting efficiency with three-point weighting |
| `true_shooting_percentage` | Shooting efficiency including free throws |
| `usage_percentage` | Share of team possessions used |
| `player_impact_estimate` | NBA Player Impact Estimate |
| `availability` | Games played divided by 82, capped at 1 |

## Age and Development Curves

Published file: `reports/development_curves_2026_27.csv`

| Column | Description |
|---|---|
| `development_group` | Sophomore, third-year, or veteran age band |
| `target` | PIE, MPG, points per 36, or availability |
| `sample_size` | Historical paired player seasons in the group |
| `raw_mean_delta` | Unshrunk next-season change |
| `league_mean_delta` | Overall historical change |
| `shrunk_delta` | Final change used by the model |

## Player Projection Backtest

Published file: `reports/player_projection_backtest.csv`

| Column | Description |
|---|---|
| `target` | Projected player outcome |
| `rows` | Held-out 2025–26 player pairs |
| `naive_mae` | No-change forecast error |
| `curve_mae` | Development-curve error |
| `selected_model` | Curve or no-change baseline selected from the test |

## Player Projections

Published file: `reports/player_projections_2026_27.csv`

| Column | Description |
|---|---|
| `player_key` | NBA ID or normalized-name fallback |
| `player_id` | Official NBA ID when available |
| `player_name` | Player name |
| `team` | Projected 2026–27 team |
| `projected_age` | Age used by the forecast |
| `seasons_played_before_2026_27` | Completed NBA seasons |
| `experience_group` | ROOKIE, SOPHOMORE, THIRD_YEAR, or veteran age band |
| `draft_bucket` | Rookie prior group or NOT_APPLICABLE |
| `model_status` | NBA_HISTORY, ROOKIE_PRIOR, or NO_NBA_HISTORY_PRIOR |
| `injury_status` | Current override state |
| `projected_pie` | Age/career-adjusted PIE |
| `effective_pie_base` | PIE after base return-effectiveness adjustment |
| `projected_minutes_per_game` | Projected role when active |
| `projected_points_per_36` | Projected scoring rate |
| `projected_points_per_game` | Projected scoring rate converted through expected minutes |
| `model_availability` | Historical availability projection |
| `availability_low/base/high` | Injury-scenario availability |
| `return_effectiveness_low/base/high` | Injury-scenario effectiveness |
| `desired_season_mpg_low/base/high` | Role minutes multiplied by availability |
| `allocated_season_mpg_low/base/high` | Minutes after team normalization to 240 |
| `projected_wins_above_replacement_low/base/high` | Player value under each injury scenario |

## Team Roster Deltas

Published file: `reports/team_roster_deltas_2026_27.csv`

| Column | Description |
|---|---|
| `team` | Team abbreviation |
| `old_roster_value` | Actual 2025–26 roster value |
| `new_roster_value_low/base/high` | Projected roster value by injury scenario |
| `roster_win_delta_low/base/high` | New roster value minus old roster value |
| `injury_downside_wins` | Base value minus low value |
| `injury_upside_wins` | High value minus base value |

## Official Standings

Published file: `reports/official_standings_2026_27.csv`

| Column | Description |
|---|---|
| `season` | 2026–27 |
| `conference` | East or West |
| `team` | Team abbreviation |
| `model_win_pct` | Unrounded historical baseline prediction |
| `historical_baseline_wins/losses/win_pct` | Pre-roster-adjustment record |
| `old_roster_value` | 2025–26 roster value |
| `new_roster_value_low/base/high` | Projected values by injury scenario |
| `roster_win_delta_low/base/high` | Roster changes in estimated wins |
| `adjusted_wins_low/base/high_raw` | Baseline plus unrounded roster delta |
| `projected_wins` | Normalized base-case wins |
| `projected_losses` | 82 minus projected wins |
| `projected_win_pct` | Projected wins divided by 82 |
| `injury_win_adjustment_low/high` | Simulation range relative to the base case |
| `scenario_id` | ROSTER_PROJECTION_V2 |
| `scenario_status` | Snapshot description |
| `conference_seed` | Projected conference position |

## Playoff Probabilities

Generated file: `data/processed/playoff_probabilities_roster_projection_v2.csv`

| Column | Description |
|---|---|
| `conference` | East or West |
| `team` | Team abbreviation |
| `projected_wins/losses` | Base standings record |
| `average_seed` | Mean seed across simulations |
| `top_six_probability` | Probability of avoiding the Play-In |
| `play_in_probability` | Probability of finishing seeds 7–10 |
| `playoff_probability` | Probability of reaching round one |
| `second_round_probability` | Probability of winning round one |
| `conference_finals_probability` | ECF or WCF probability |
| `nba_finals_probability` | Probability of winning the conference |
| `championship_probability` | NBA title probability |
| `conference_final` | ECF or WCF label |
