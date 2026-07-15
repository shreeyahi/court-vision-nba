from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RAW_DIRECTORY = (
    PROJECT_ROOT / "data" / "raw" / "players"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "player_seasons.parquet"
)

TRADE_FILE = (
    PROJECT_ROOT
    / "data"
    / "manual"
    / "trades_2026.csv"
)

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

BASE_COLUMNS = [
    "PLAYER_ID",
    "PLAYER_NAME",
    "TEAM_ABBREVIATION",
    "AGE",
    "GP",
    "MIN",
    "PTS",
    "REB",
    "AST",
    "STL",
    "BLK",
    "TOV",
    "FGM",
    "FGA",
    "FG3M",
    "FG3A",
    "FTM",
    "FTA",
    "PLUS_MINUS",
]

ADVANCED_COLUMNS = [
    "PLAYER_ID",
    "OFF_RATING",
    "DEF_RATING",
    "NET_RATING",
    "AST_PCT",
    "AST_TO",
    "AST_RATIO",
    "OREB_PCT",
    "DREB_PCT",
    "REB_PCT",
    "TM_TOV_PCT",
    "EFG_PCT",
    "TS_PCT",
    "USG_PCT",
    "PACE",
    "PIE",
]


def download_measure(
    season: str,
    measure: str,
    force: bool = False,
    maximum_attempts: int = 3,
) -> pd.DataFrame:
    """Download one type of player statistics."""

    RAW_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw_file = RAW_DIRECTORY / (
        f"player_{measure.lower()}_{season}.csv"
    )

    if raw_file.exists() and not force:
        print(
            f"Using cached {measure} player data "
            f"for {season}"
        )

        return pd.read_csv(
            raw_file,
            dtype={"PLAYER_ID": "Int64"},
        )

    for attempt in range(
        1,
        maximum_attempts + 1,
    ):
        try:
            print(
                f"Downloading {season} {measure} stats "
                f"(attempt {attempt}/{maximum_attempts})"
            )

            endpoint = (
                leaguedashplayerstats
                .LeagueDashPlayerStats(
                    season=season,
                    season_type_all_star=(
                        "Regular Season"
                    ),
                    measure_type_detailed_defense=(
                        measure
                    ),
                    per_mode_detailed="PerGame",
                    league_id_nullable="00",
                    timeout=60,
                )
            )

            frame = endpoint.get_data_frames()[0]

            if frame.empty:
                raise RuntimeError(
                    f"No {measure} player data "
                    f"returned for {season}."
                )

            frame["PLAYER_ID"] = (
                frame["PLAYER_ID"].astype("Int64")
            )

            frame.to_csv(
                raw_file,
                index=False,
            )

            print(f"Saved raw data: {raw_file}")

            time.sleep(1.5)

            return frame

        except Exception as error:
            print(
                f"Attempt {attempt} failed: {error}"
            )

            if attempt == maximum_attempts:
                raise

            wait_seconds = 2**attempt

            print(
                f"Waiting {wait_seconds} seconds "
                f"before retrying."
            )

            time.sleep(wait_seconds)

    raise RuntimeError(
        f"Unable to download {season} {measure}."
    )


def select_required_columns(
    frame: pd.DataFrame,
    required_columns: list[str],
    season: str,
    measure: str,
) -> pd.DataFrame:
    """Keep only the fields needed by CourtVision."""

    missing_columns = set(required_columns) - set(
        frame.columns
    )

    if missing_columns:
        raise ValueError(
            f"{season} {measure} data is missing: "
            f"{sorted(missing_columns)}"
        )

    selected = frame[required_columns].copy()

    if selected["PLAYER_ID"].duplicated().any():
        duplicates = selected.loc[
            selected["PLAYER_ID"].duplicated(),
            "PLAYER_ID",
        ].tolist()

        raise ValueError(
            f"Duplicate player IDs in {season} "
            f"{measure}: {duplicates[:5]}"
        )

    return selected


def combine_season(
    season: str,
    force: bool = False,
) -> pd.DataFrame:
    """Combine box-score and advanced player statistics."""

    base = download_measure(
        season=season,
        measure="Base",
        force=force,
    )

    advanced = download_measure(
        season=season,
        measure="Advanced",
        force=force,
    )

    base = select_required_columns(
        frame=base,
        required_columns=BASE_COLUMNS,
        season=season,
        measure="Base",
    )

    advanced = select_required_columns(
        frame=advanced,
        required_columns=ADVANCED_COLUMNS,
        season=season,
        measure="Advanced",
    )

    combined = base.merge(
        advanced,
        on="PLAYER_ID",
        how="left",
        validate="one_to_one",
    )

    combined.insert(0, "season", season)

    combined = combined.rename(
        columns={
            "PLAYER_ID": "player_id",
            "PLAYER_NAME": "player_name",
            "TEAM_ABBREVIATION": "team",
            "AGE": "age",
            "GP": "games_played",
            "MIN": "minutes_per_game",
            "PTS": "points_per_game",
            "REB": "rebounds_per_game",
            "AST": "assists_per_game",
            "STL": "steals_per_game",
            "BLK": "blocks_per_game",
            "TOV": "turnovers_per_game",
            "FGM": "field_goals_made_per_game",
            "FGA": "field_goals_attempted_per_game",
            "FG3M": "threes_made_per_game",
            "FG3A": "threes_attempted_per_game",
            "FTM": "free_throws_made_per_game",
            "FTA": "free_throws_attempted_per_game",
            "PLUS_MINUS": "plus_minus_per_game",
            "OFF_RATING": "offensive_rating",
            "DEF_RATING": "defensive_rating",
            "NET_RATING": "net_rating",
            "AST_PCT": "assist_percentage",
            "AST_TO": "assist_to_turnover",
            "AST_RATIO": "assist_ratio",
            "OREB_PCT": "offensive_rebound_percentage",
            "DREB_PCT": "defensive_rebound_percentage",
            "REB_PCT": "rebound_percentage",
            "TM_TOV_PCT": "turnover_percentage",
            "EFG_PCT": "effective_field_goal_percentage",
            "TS_PCT": "true_shooting_percentage",
            "USG_PCT": "usage_percentage",
            "PACE": "pace",
            "PIE": "player_impact_estimate",
        }
    )

    combined["availability"] = np.minimum(
        combined["games_played"] / 82,
        1,
    )

    combined["points_per_36"] = np.where(
        combined["minutes_per_game"] > 0,
        (
            combined["points_per_game"]
            / combined["minutes_per_game"]
            * 36
        ),
        0.0,
    )

    print(
        f"{season}: combined "
        f"{len(combined):,} players"
    )

    return combined


def report_trade_coverage(
    player_seasons: pd.DataFrame,
) -> None:
    """Show whether traded players match official NBA IDs."""

    trades = pd.read_csv(
        TRADE_FILE,
        dtype={"player_id": "Int64"},
    )

    traded_players = (
        trades.loc[
            trades["asset_type"] == "PLAYER",
            ["player_id", "asset_name"],
        ]
        .drop_duplicates("player_id")
        .copy()
    )

    latest_players = set(
        player_seasons.loc[
            player_seasons["season"] == "2025-26",
            "player_id",
        ].dropna()
    )

    traded_players["matched_latest_season"] = (
        traded_players["player_id"].isin(
            latest_players
        )
    )

    missing_players = traded_players.loc[
        ~traded_players["matched_latest_season"]
    ]

    matched_count = int(
        traded_players[
            "matched_latest_season"
        ].sum()
    )

    print("\nTRADE LEDGER COVERAGE")
    print(
        f"Matched in 2025-26: "
        f"{matched_count}/{len(traded_players)}"
    )

    if not missing_players.empty:
        print(
            "\nNot found in the latest season "
            "(we can use an earlier season):"
        )

        print(
            missing_players[
                ["player_id", "asset_name"]
            ].to_string(index=False)
        )


def validate_player_seasons(
    player_seasons: pd.DataFrame,
) -> None:
    """Validate the combined player dataset."""

    if player_seasons.empty:
        raise ValueError(
            "Player-season data is empty."
        )

    if player_seasons.duplicated(
        subset=["season", "player_id"]
    ).any():
        raise ValueError(
            "Duplicate player-season rows found."
        )

    if (
        player_seasons["games_played"] < 0
    ).any():
        raise ValueError(
            "games_played cannot be negative."
        )

    if not player_seasons[
        "availability"
    ].between(0, 1).all():
        raise ValueError(
            "availability must be between 0 and 1."
        )

    if player_seasons["player_id"].isna().any():
        raise ValueError(
            "At least one player ID is missing."
        )


def build_player_dataset(
    force: bool = False,
) -> pd.DataFrame:
    """Build the historical player-season dataset."""

    season_frames: list[pd.DataFrame] = []

    for season in SEASONS:
        season_frame = combine_season(
            season=season,
            force=force,
        )

        season_frames.append(season_frame)

    player_seasons = pd.concat(
        season_frames,
        ignore_index=True,
    )

    player_seasons = player_seasons.sort_values(
        ["season", "player_name"]
    ).reset_index(drop=True)

    validate_player_seasons(player_seasons)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    player_seasons.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print("\nPLAYER DATA PIPELINE COMPLETE\n")
    print(f"Rows: {len(player_seasons):,}")
    print(
        f"Unique players: "
        f"{player_seasons['player_id'].nunique():,}"
    )
    print(
        f"Seasons: "
        f"{player_seasons['season'].nunique()}"
    )
    print(f"Output: {OUTPUT_FILE}")

    report_trade_coverage(player_seasons)

    return player_seasons


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Download and process NBA player statistics."
        )
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Redownload player data instead of using cache.",
    )

    arguments = parser.parse_args()

    build_player_dataset(force=arguments.force)
