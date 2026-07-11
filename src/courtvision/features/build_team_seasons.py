from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "games.parquet"
OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "team_seasons.parquet"
)

EASTERN_TEAMS = {
    "ATL",
    "BOS",
    "BKN",
    "CHA",
    "CHI",
    "CLE",
    "DET",
    "IND",
    "MIA",
    "MIL",
    "NYK",
    "ORL",
    "PHI",
    "TOR",
    "WAS",
}

WESTERN_TEAMS = {
    "DAL",
    "DEN",
    "GSW",
    "HOU",
    "LAC",
    "LAL",
    "MEM",
    "MIN",
    "NOP",
    "OKC",
    "PHX",
    "POR",
    "SAC",
    "SAS",
    "UTA",
}

REQUIRED_COLUMNS = {
    "game_id",
    "game_date",
    "season",
    "home_team",
    "away_team",
    "home_points",
    "away_points",
    "home_win",
}


def load_games() -> pd.DataFrame:
    """Load and validate the historical game dataset."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing {INPUT_FILE}. Run fetch_games.py first."
        )

    games = pd.read_parquet(INPUT_FILE)

    missing_columns = REQUIRED_COLUMNS - set(games.columns)

    if missing_columns:
        raise ValueError(
            f"Game data is missing columns: "
            f"{sorted(missing_columns)}"
        )

    if games.empty:
        raise ValueError("The historical game dataset is empty.")

    return games


def create_team_game_rows(
    games: pd.DataFrame,
) -> pd.DataFrame:
    """Create one row for each team in each game."""

    home_rows = pd.DataFrame(
        {
            "game_id": games["game_id"],
            "game_date": games["game_date"],
            "season": games["season"],
            "team": games["home_team"],
            "opponent": games["away_team"],
            "is_home": 1,
            "win": games["home_win"].astype(int),
            "points_for": games["home_points"],
            "points_against": games["away_points"],
        }
    )

    away_rows = pd.DataFrame(
        {
            "game_id": games["game_id"],
            "game_date": games["game_date"],
            "season": games["season"],
            "team": games["away_team"],
            "opponent": games["home_team"],
            "is_home": 0,
            "win": 1 - games["home_win"].astype(int),
            "points_for": games["away_points"],
            "points_against": games["home_points"],
        }
    )

    team_games = pd.concat(
        [home_rows, away_rows],
        ignore_index=True,
    )

    team_games["point_margin"] = (
        team_games["points_for"]
        - team_games["points_against"]
    )

    team_games["home_win"] = (
        team_games["win"] * team_games["is_home"]
    )

    team_games["away_win"] = (
        team_games["win"]
        * (1 - team_games["is_home"])
    )

    return team_games


def add_conference(
    team_seasons: pd.DataFrame,
) -> pd.DataFrame:
    """Attach East or West to every NBA team."""

    team_seasons["conference"] = team_seasons["team"].map(
        lambda team: (
            "East"
            if team in EASTERN_TEAMS
            else "West"
            if team in WESTERN_TEAMS
            else None
        )
    )

    unknown_teams = team_seasons.loc[
        team_seasons["conference"].isna(),
        "team",
    ].unique()

    if len(unknown_teams) > 0:
        raise ValueError(
            f"Unknown conference for teams: "
            f"{sorted(unknown_teams)}"
        )

    return team_seasons


def add_previous_season_features(
    team_seasons: pd.DataFrame,
) -> pd.DataFrame:
    """Add past information without leaking future results."""

    team_seasons = team_seasons.sort_values(
        ["team", "season"]
    ).reset_index(drop=True)

    previous_columns = [
        "win_pct",
        "points_for_per_game",
        "points_against_per_game",
        "avg_point_margin",
    ]

    for column in previous_columns:
        team_seasons[f"previous_{column}"] = (
            team_seasons.groupby("team")[column].shift(1)
        )

    team_seasons["two_season_win_pct"] = (
        team_seasons.groupby("team")["win_pct"].transform(
            lambda values: (
                values.shift(1)
                .rolling(2, min_periods=1)
                .mean()
            )
        )
    )

    team_seasons["two_season_avg_margin"] = (
        team_seasons.groupby("team")[
            "avg_point_margin"
        ].transform(
            lambda values: (
                values.shift(1)
                .rolling(2, min_periods=1)
                .mean()
            )
        )
    )

    return team_seasons


def validate_team_seasons(
    team_seasons: pd.DataFrame,
    games: pd.DataFrame,
) -> None:
    """Stop immediately if the report cards look wrong."""

    if team_seasons.duplicated(
        subset=["season", "team"]
    ).any():
        raise ValueError(
            "Duplicate team-season rows were found."
        )

    if not (
        team_seasons["wins"] + team_seasons["losses"]
        == team_seasons["games"]
    ).all():
        raise ValueError(
            "At least one team's wins and losses do not "
            "equal its games played."
        )

    if not team_seasons["win_pct"].between(0, 1).all():
        raise ValueError("win_pct must stay between 0 and 1.")

    teams_per_season = team_seasons.groupby(
        "season"
    )["team"].nunique()

    if not teams_per_season.eq(30).all():
        raise ValueError(
            "Every season should contain exactly 30 teams."
        )

    wins_per_season = team_seasons.groupby(
        "season"
    )["wins"].sum()

    games_per_season = games.groupby("season").size()

    if not wins_per_season.equals(games_per_season):
        raise ValueError(
            "The number of wins does not equal the number "
            "of games in at least one season."
        )


def build_team_seasons() -> pd.DataFrame:
    """Build one model-ready report card per team per season."""

    games = load_games()
    team_games = create_team_game_rows(games)

    team_seasons = (
        team_games.groupby(
            ["season", "team"],
            as_index=False,
        )
        .agg(
            games=("game_id", "count"),
            wins=("win", "sum"),
            points_for=("points_for", "sum"),
            points_against=("points_against", "sum"),
            points_for_per_game=("points_for", "mean"),
            points_against_per_game=(
                "points_against",
                "mean",
            ),
            avg_point_margin=("point_margin", "mean"),
            home_games=("is_home", "sum"),
            home_wins=("home_win", "sum"),
            away_wins=("away_win", "sum"),
        )
    )

    team_seasons["losses"] = (
        team_seasons["games"] - team_seasons["wins"]
    )

    team_seasons["away_games"] = (
        team_seasons["games"]
        - team_seasons["home_games"]
    )

    team_seasons["win_pct"] = (
        team_seasons["wins"] / team_seasons["games"]
    )

    team_seasons["home_win_pct"] = (
        team_seasons["home_wins"]
        / team_seasons["home_games"]
    )

    team_seasons["away_win_pct"] = (
        team_seasons["away_wins"]
        / team_seasons["away_games"]
    )

    team_seasons = add_conference(team_seasons)

    team_seasons = add_previous_season_features(
        team_seasons
    )

    team_seasons = team_seasons.sort_values(
        ["season", "conference", "win_pct"],
        ascending=[True, True, False],
    ).reset_index(drop=True)

    validate_team_seasons(team_seasons, games)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    team_seasons.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    latest_season = team_seasons["season"].max()

    latest_standings = team_seasons.loc[
        team_seasons["season"] == latest_season,
        [
            "conference",
            "team",
            "wins",
            "losses",
            "win_pct",
            "avg_point_margin",
        ],
    ].copy()

    latest_standings["win_pct"] = (
        latest_standings["win_pct"].round(3)
    )

    latest_standings["avg_point_margin"] = (
        latest_standings["avg_point_margin"].round(2)
    )

    print("\nTEAM-SEASON FEATURES COMPLETE\n")
    print(f"Rows: {len(team_seasons):,}")
    print(
        f"Seasons: "
        f"{team_seasons['season'].nunique()}"
    )
    print(
        f"Teams per season: "
        f"{team_seasons.groupby('season')['team'].nunique().min()}"
    )
    print(f"Output: {OUTPUT_FILE}")
    print(f"\n{latest_season} standings:\n")
    print(latest_standings.to_string(index=False))

    return team_seasons


if __name__ == "__main__":
    build_team_seasons()