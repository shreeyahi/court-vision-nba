# CourtVision Data Dictionary

## Trade Ledger

File: `data/manual/trades_2026.csv`

Each row represents one asset moving from one NBA team to another.

| Column | Description |
|---|---|
| `transaction_id` | Stable identifier shared by all assets in one transaction |
| `announced_date` | Date the transaction was first announced |
| `effective_date` | Date the transaction became official |
| `from_team` | Abbreviation of the sending team |
| `to_team` | Abbreviation of the receiving team |
| `asset_type` | PLAYER, DRAFT_PICK, PICK_SWAP, DRAFT_RIGHTS, or CASH |
| `asset_name` | Human-readable player or asset description |
| `player_id` | Official NBA player ID for player assets |
| `status` | OFFICIAL, REPORTED, or ON_HOLD |
| `source_url` | NBA.com verification source |
| `source_updated_at` | Date the source was updated or checked |
| `verified_at_utc` | Date CourtVision verified the row |
| `notes` | Audit and scenario notes |

## Historical Games

Generated file: `data/processed/games.parquet`

| Column | Description |
|---|---|
| `game_id` | Official NBA game identifier |
| `game_date` | Date the game was played |
| `season` | NBA season label |
| `home_team_id` | Official NBA home-team ID |
| `home_team` | Home-team abbreviation |
| `away_team_id` | Official NBA away-team ID |
| `away_team` | Away-team abbreviation |
| `home_points` | Points scored by the home team |
| `away_points` | Points scored by the away team |
| `home_win` | 1 if the home team won, otherwise 0 |
| `point_margin` | Home points minus away points |

## Team-Season Features

Generated file: `data/processed/team_seasons.parquet`

| Column | Description |
|---|---|
| `season` | NBA season |
| `team` | Team abbreviation |
| `conference` | East or West |
| `games` | Games played |
| `wins` | Games won |
| `losses` | Games lost |
| `win_pct` | Wins divided by games |
| `points_for` | Total points scored |
| `points_against` | Total points allowed |
| `points_for_per_game` | Average points scored |
| `points_against_per_game` | Average points allowed |
| `avg_point_margin` | Average scoring margin |
| `home_games` | Home games played |
| `home_wins` | Home games won |
| `home_win_pct` | Home winning percentage |
| `away_games` | Away games played |
| `away_wins` | Away games won |
| `away_win_pct` | Away winning percentage |
| `previous_win_pct` | Previous-season win percentage |
| `previous_points_for_per_game` | Previous-season scoring |
| `previous_points_against_per_game` | Previous-season points allowed |
| `previous_avg_point_margin` | Previous-season average margin |
| `two_season_win_pct` | Prior two-season mean win percentage |
| `two_season_avg_margin` | Prior two-season mean point margin |

## Player-Season Statistics

Generated file: `data/processed/player_seasons.parquet`

| Column | Description |
|---|---|
| `season` | NBA season |
| `player_id` | Official NBA player identifier |
| `player_name` | Player name |
| `team` | Team abbreviation |
| `age` | Player age |
| `games_played` | Regular-season appearances |
| `minutes_per_game` | Average playing time |
| `points_per_game` | Average points |
| `rebounds_per_game` | Average rebounds |
| `assists_per_game` | Average assists |
| `steals_per_game` | Average steals |
| `blocks_per_game` | Average blocks |
| `turnovers_per_game` | Average turnovers |
| `plus_minus_per_game` | Average plus-minus |
| `offensive_rating` | NBA offensive rating |
| `defensive_rating` | NBA defensive rating |
| `net_rating` | Offensive rating minus defensive rating |
| `effective_field_goal_percentage` | Shooting efficiency with extra weight for threes |
| `true_shooting_percentage` | Shooting efficiency including free throws |
| `usage_percentage` | Share of team possessions used |
| `player_impact_estimate` | NBA Player Impact Estimate |
| `availability` | Games played divided by 82 and capped at 1 |

## Player Impact

Generated file: `data/processed/player_impact.parquet`

| Column | Description |
|---|---|
| `player_id` | Official NBA player ID |
| `player_name` | Latest NBA player name |
| `latest_team` | Most recent team in the player dataset |
| `latest_age` | Most recent age |
| `seasons_used` | Number of seasons used in the estimate |
| `weighted_pie` | Recency-weighted Player Impact Estimate |
| `weighted_minutes` | Recency-weighted minutes per game |
| `weighted_availability` | Recency-weighted availability |
| `weighted_net_rating` | Recency-weighted net rating |
| `pie_above_replacement` | Weighted PIE minus replacement PIE |
| `minutes_share` | Weighted minutes divided by 48 |
| `estimated_wins_above_replacement` | CourtVision player-win estimate |
| `impact_confidence` | Confidence based on seasons and availability |

## Official Standings Report

Published file: `reports/official_standings_2026_27.csv`

| Column | Description |
|---|---|
| `conference` | East or West |
| `team` | Team abbreviation |
| `baseline_wins` | No-trade projected wins |
| `trade_win_delta` | Wins added or removed by official trades |
| `adjusted_wins_raw` | Baseline plus unrounded trade adjustment |
| `projected_wins` | Normalized integer wins |
| `projected_losses` | 82 minus projected wins |
| `projected_win_pct` | Projected wins divided by 82 |
| `scenario_id` | Transaction scenario identifier |
| `scenario_status` | Status used by the scenario |
| `conference_seed` | Projected conference position |

## Playoff Probability Report

Published file: `reports/playoff_probabilities_2026_27.csv`

| Column | Description |
|---|---|
| `conference` | East or West |
| `team` | Team abbreviation |
| `projected_wins` | Trade-adjusted projected wins |
| `projected_losses` | Trade-adjusted projected losses |
| `average_seed` | Mean conference seed across simulations |
| `top_six_probability` | Probability of avoiding the Play-In |
| `play_in_probability` | Probability of finishing seeds 7–10 |
| `playoff_probability` | Probability of reaching round one |
| `second_round_probability` | Probability of winning round one |
| `conference_finals_probability` | ECF or WCF probability |
| `nba_finals_probability` | Probability of winning the conference |
| `championship_probability` | Probability of winning the NBA championship |
| `conference_final` | ECF for East teams or WCF for West teams |

## Simulation Metadata

Published file: `reports/simulation_metadata.json`

| Field | Description |
|---|---|
| `scenario_id` | Transaction scenario simulated |
| `simulations` | Number of Monte Carlo seasons |
| `random_seed` | Seed used for reproducibility |
| `forecast_mae_wins` | Historical forecast error used as uncertainty |
| `historical_home_win_rate` | Home win rate from historical games |
| `home_advantage_probability` | Home-court probability adjustment |