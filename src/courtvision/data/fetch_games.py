from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIRECTORY = PROJECT_ROOT / "data" / "raw" / "games"
PROCESSED_DIRECTORY = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIRECTORY / "games.parquet"

SEASONS = [
    "2015-16",
    "2016-17",
    "2017-18",
    "2018-19",
    "2019-20",
    "2020-21",
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
    "2025-26",
]


def download_season(
    season: str,
    force: bool = False,
    maximum_attempts: int = 3,
) -> pd.DataFrame:
    """Download one season of NBA team game logs."""

    RAW_DIRECTORY.mkdir(parents=True, exist_ok=True)
    raw_file = RAW_DIRECTORY / f"team_games_{season}.csv"

    if raw_file.exists() and not force:
        print(f"Using cached data for {season}")
        return pd.read_csv(raw_file, dtype={"GAME_ID": "string"})

    for attempt in range(1, maximum_attempts + 1):
        try:
            print(
                f"Downloading {season} "
                f"(attempt {attempt}/{maximum_attempts})"
            )

            endpoint = leaguegamefinder.LeagueGameFinder(
                player_or_team_abbreviation="T",
                season_nullable=season,
                season_type_nullable="Regular Season",
                league_id_nullable="00",
                timeout=60,
            )

            frame = endpoint.get_data_frames()[0]

            if frame.empty:
                raise RuntimeError(
                    f"The NBA API returned no data for {season}."
                )

            frame["GAME_ID"] = frame["GAME_ID"].astype("string")
            frame.to_csv(raw_file, index=False)

            print(f"Saved raw data: {raw_file}")
            time.sleep(1.5)

            return frame

        except Exception as error:
            print(f"Attempt {attempt} failed: {error}")

            if attempt == maximum_attempts:
                raise

            wait_seconds = 2**attempt
            print(f"Waiting {wait_seconds} seconds before retrying.")
            time.sleep(wait_seconds)

    raise RuntimeError(f"Unable to download season {season}.")


def convert_team_rows_to_games(
    team_rows: pd.DataFrame,
    season: str,
) -> pd.DataFrame:
    """Convert two team rows per game into one home-vs-away row."""

    required_columns = {
        "GAME_ID",
        "GAME_DATE",
        "TEAM_ID",
        "TEAM_ABBREVIATION",
        "MATCHUP",
        "WL",
        "PTS",
    }

    missing_columns = required_columns - set(team_rows.columns)

    if missing_columns:
        raise ValueError(
            f"{season} is missing required columns: "
            f"{sorted(missing_columns)}"
        )

    game_records: list[dict[str, object]] = []

    for game_id, game_rows in team_rows.groupby("GAME_ID"):
        if len(game_rows) != 2:
            raise ValueError(
                f"Game {game_id} in {season} has "
                f"{len(game_rows)} team rows instead of 2."
            )

        home_abbreviations: set[str] = set()
        away_abbreviations: set[str] = set()

        for matchup in game_rows["MATCHUP"].astype(str):
            if " @ " in matchup:
                away_abbreviation, home_abbreviation = matchup.split(
                    " @ ",
                    maxsplit=1,
                )
            elif " vs. " in matchup:
                home_abbreviation, away_abbreviation = matchup.split(
                    " vs. ",
                    maxsplit=1,
                )
            else:
                raise ValueError(
                    f"Unknown matchup format {matchup!r} "
                    f"for game {game_id} in {season}."
                )

            home_abbreviations.add(home_abbreviation.strip())
            away_abbreviations.add(away_abbreviation.strip())

        if (
            len(home_abbreviations) != 1
            or len(away_abbreviations) != 1
        ):
            raise ValueError(
                f"Conflicting matchup labels for game "
                f"{game_id} in {season}."
            )

        home_abbreviation = home_abbreviations.pop()
        away_abbreviation = away_abbreviations.pop()

        home_rows = game_rows[
            game_rows["TEAM_ABBREVIATION"]
            == home_abbreviation
        ]

        away_rows = game_rows[
            game_rows["TEAM_ABBREVIATION"]
            == away_abbreviation
        ]

        if len(home_rows) != 1 or len(away_rows) != 1:
            raise ValueError(
                f"Could not match teams for game {game_id} "
                f"in {season}: away={away_abbreviation}, "
                f"home={home_abbreviation}."
            )

        home = home_rows.iloc[0]
        away = away_rows.iloc[0]

        home_points = int(home["PTS"])
        away_points = int(away["PTS"])

        game_records.append(
            {
                "game_id": str(game_id),
                "game_date": home["GAME_DATE"],
                "season": season,
                "home_team_id": int(home["TEAM_ID"]),
                "home_team": home["TEAM_ABBREVIATION"],
                "away_team_id": int(away["TEAM_ID"]),
                "away_team": away["TEAM_ABBREVIATION"],
                "home_points": home_points,
                "away_points": away_points,
                "home_win": int(home["WL"] == "W"),
                "point_margin": home_points - away_points,
            }
        )

    games = pd.DataFrame(game_records)

    games["game_date"] = pd.to_datetime(
        games["game_date"],
        errors="raise",
    )

    games = games.sort_values(
        ["game_date", "game_id"]
    ).reset_index(drop=True)

    if games["game_id"].duplicated().any():
        duplicates = games.loc[
            games["game_id"].duplicated(),
            "game_id",
        ].tolist()

        raise ValueError(
            f"Duplicate game IDs found in {season}: {duplicates[:5]}"
        )

    invalid_home_wins = set(games["home_win"]) - {0, 1}

    if invalid_home_wins:
        raise ValueError(
            f"Invalid home_win values: {invalid_home_wins}"
        )

    print(f"{season}: created {len(games):,} games")

    return games


def build_game_dataset(force: bool = False) -> pd.DataFrame:
    """Download, clean, combine, validate and save every season."""

    season_frames: list[pd.DataFrame] = []

    for season in SEASONS:
        team_rows = download_season(
            season=season,
            force=force,
        )

        games = convert_team_rows_to_games(
            team_rows=team_rows,
            season=season,
        )

        season_frames.append(games)

    all_games = pd.concat(
        season_frames,
        ignore_index=True,
    )

    all_games = all_games.sort_values(
        ["game_date", "game_id"]
    ).reset_index(drop=True)

    if all_games["game_id"].duplicated().any():
        raise ValueError(
            "Duplicate game IDs were found across seasons."
        )

    if (all_games["home_team"] == all_games["away_team"]).any():
        raise ValueError(
            "At least one game has the same home and away team."
        )

    if not all_games["home_win"].isin([0, 1]).all():
        raise ValueError(
            "home_win contains a value other than 0 or 1."
        )

    PROCESSED_DIRECTORY.mkdir(parents=True, exist_ok=True)
    all_games.to_parquet(OUTPUT_FILE, index=False)

    print("\nHISTORICAL GAME PIPELINE COMPLETE\n")
    print(f"Seasons: {all_games['season'].nunique()}")
    print(f"Games: {len(all_games):,}")
    print(
        f"Date range: {all_games['game_date'].min().date()} "
        f"to {all_games['game_date'].max().date()}"
    )
    print(f"Teams: {all_games['home_team'].nunique()}")
    print(f"Output: {OUTPUT_FILE}")

    return all_games


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and process historical NBA games."
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Download every season again instead of using cached CSV files.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_arguments()
    build_game_dataset(force=arguments.force)