from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

PLAYER_FILE = (
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

BASELINE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "baseline_2026_27.csv"
)

PLAYER_IMPACT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "player_impact.parquet"
)

TRADE_IMPACT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "trade_player_impacts.csv"
)

SCENARIO_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "standings_scenarios.csv"
)

OFFICIAL_STANDINGS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "standings_official_2026_27.csv"
)

SEASON_WEIGHTS = {
    "2023-24": 0.15,
    "2024-25": 0.30,
    "2025-26": 0.55,
}

TOTAL_NBA_WINS = 1230
GAMES_PER_TEAM = 82


def load_inputs() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Load player data, trades and baseline standings."""

    missing_files = [
        path
        for path in [
            PLAYER_FILE,
            TRADE_FILE,
            BASELINE_FILE,
        ]
        if not path.exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            f"Missing required files: {missing_files}"
        )

    player_seasons = pd.read_parquet(
        PLAYER_FILE
    )

    trades = pd.read_csv(
        TRADE_FILE,
        dtype={"player_id": "Int64"},
    )

    baseline = pd.read_csv(
        BASELINE_FILE
    )

    return player_seasons, trades, baseline


def calculate_player_impacts(
    player_seasons: pd.DataFrame,
) -> tuple[pd.DataFrame, float]:
    """Create transparent PIE-based player-win estimates."""

    required_columns = {
        "season",
        "player_id",
        "player_name",
        "team",
        "age",
        "games_played",
        "minutes_per_game",
        "availability",
        "player_impact_estimate",
        "net_rating",
        "plus_minus_per_game",
    }

    missing_columns = required_columns - set(
        player_seasons.columns
    )

    if missing_columns:
        raise ValueError(
            f"Player data is missing columns: "
            f"{sorted(missing_columns)}"
        )

    data = player_seasons.loc[
        player_seasons["season"].isin(
            SEASON_WEIGHTS
        )
    ].copy()

    data["season_weight"] = data["season"].map(
        SEASON_WEIGHTS
    )

    if data["season_weight"].isna().any():
        raise ValueError(
            "At least one season has no recency weight."
        )

    weighted_columns = [
        "player_impact_estimate",
        "minutes_per_game",
        "availability",
        "net_rating",
        "plus_minus_per_game",
    ]

    for column in weighted_columns:
        data[f"weighted_{column}_sum"] = (
            data[column] * data["season_weight"]
        )

    summary = (
        data.groupby(
            "player_id",
            as_index=False,
        )
        .agg(
            weight_sum=("season_weight", "sum"),
            seasons_used=("season", "nunique"),
            pie_sum=(
                "weighted_player_impact_estimate_sum",
                "sum",
            ),
            minutes_sum=(
                "weighted_minutes_per_game_sum",
                "sum",
            ),
            availability_sum=(
                "weighted_availability_sum",
                "sum",
            ),
            net_rating_sum=(
                "weighted_net_rating_sum",
                "sum",
            ),
            plus_minus_sum=(
                "weighted_plus_minus_per_game_sum",
                "sum",
            ),
        )
    )

    summary["weighted_pie"] = (
        summary["pie_sum"]
        / summary["weight_sum"]
    )

    summary["weighted_minutes"] = (
        summary["minutes_sum"]
        / summary["weight_sum"]
    )

    summary["weighted_availability"] = (
        summary["availability_sum"]
        / summary["weight_sum"]
    )

    summary["weighted_net_rating"] = (
        summary["net_rating_sum"]
        / summary["weight_sum"]
    )

    summary["weighted_plus_minus"] = (
        summary["plus_minus_sum"]
        / summary["weight_sum"]
    )

    latest_identity = (
        data.sort_values("season")
        .drop_duplicates(
            subset=["player_id"],
            keep="last",
        )
        [
            [
                "player_id",
                "player_name",
                "team",
                "age",
                "season",
            ]
        ]
        .rename(
            columns={
                "team": "latest_team",
                "age": "latest_age",
                "season": "latest_season",
            }
        )
    )

    summary = summary.merge(
        latest_identity,
        on="player_id",
        how="left",
        validate="one_to_one",
    )

    latest = data.loc[
        data["season"] == "2025-26"
    ].copy()

    replacement_pool = latest.loc[
        latest["minutes_per_game"].between(
            8,
            18,
        )
        & (latest["games_played"] >= 20)
    ]

    if len(replacement_pool) < 30:
        raise ValueError(
            "Replacement-player pool is too small."
        )

    replacement_pie = float(
        replacement_pool[
            "player_impact_estimate"
        ].median()
    )

    summary[
        "pie_above_replacement"
    ] = (
        summary["weighted_pie"]
        - replacement_pie
    )

    summary["minutes_share"] = (
        summary["weighted_minutes"] / 48
    )

    summary[
        "estimated_wins_above_replacement"
    ] = (
        summary["pie_above_replacement"]
        * summary["minutes_share"]
        * summary["weighted_availability"]
        * GAMES_PER_TEAM
    )

    summary[
        "estimated_wins_above_replacement"
    ] = summary[
        "estimated_wins_above_replacement"
    ].clip(
        lower=-2,
        upper=12,
    )

    summary["impact_confidence"] = (
        0.50
        * (
            summary["seasons_used"] / 3
        ).clip(upper=1)
        + 0.50
        * summary["weighted_availability"]
    )

    output_columns = [
        "player_id",
        "player_name",
        "latest_team",
        "latest_age",
        "latest_season",
        "seasons_used",
        "weighted_pie",
        "weighted_minutes",
        "weighted_availability",
        "weighted_net_rating",
        "weighted_plus_minus",
        "pie_above_replacement",
        "minutes_share",
        "estimated_wins_above_replacement",
        "impact_confidence",
    ]

    player_impacts = summary[
        output_columns
    ].sort_values(
        "estimated_wins_above_replacement",
        ascending=False,
    ).reset_index(drop=True)

    if player_impacts["player_id"].duplicated().any():
        raise ValueError(
            "Duplicate players found in impact table."
        )

    return player_impacts, replacement_pie


def connect_trades_to_impacts(
    trades: pd.DataFrame,
    player_impacts: pd.DataFrame,
) -> pd.DataFrame:
    """Join every traded player to one impact estimate."""

    trade_players = trades.loc[
        trades["asset_type"] == "PLAYER"
    ].copy()

    trade_players = trade_players.merge(
        player_impacts,
        on="player_id",
        how="left",
        validate="many_to_one",
    )

    missing = trade_players.loc[
        trade_players[
            "estimated_wins_above_replacement"
        ].isna()
    ]

    if not missing.empty:
        raise ValueError(
            "Missing impact scores for traded players: "
            f"{missing['asset_name'].tolist()}"
        )

    return trade_players


def calculate_team_deltas(
    trade_rows: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate value received minus value sent."""

    impact_column = (
        "estimated_wins_above_replacement"
    )

    received = (
        trade_rows.groupby("to_team")[
            impact_column
        ]
        .sum()
        .rename("wins_received")
    )

    sent = (
        trade_rows.groupby("from_team")[
            impact_column
        ]
        .sum()
        .rename("wins_sent")
    )

    teams = sorted(
        set(received.index)
        | set(sent.index)
    )

    deltas = pd.DataFrame({"team": teams})

    deltas = deltas.merge(
        received,
        left_on="team",
        right_index=True,
        how="left",
    )

    deltas = deltas.merge(
        sent,
        left_on="team",
        right_index=True,
        how="left",
    )

    deltas[
        ["wins_received", "wins_sent"]
    ] = deltas[
        ["wins_received", "wins_sent"]
    ].fillna(0)

    deltas["trade_win_delta"] = (
        deltas["wins_received"]
        - deltas["wins_sent"]
    )

    if not np.isclose(
        deltas["trade_win_delta"].sum(),
        0,
        atol=1e-8,
    ):
        raise ValueError(
            "Trade win deltas must sum to zero."
        )

    return deltas


def integerize_wins(
    raw_wins: np.ndarray,
) -> np.ndarray:
    """Round records while preserving 1,230 league wins."""

    adjusted_wins = raw_wins.astype(float).copy()

    adjusted_wins += (
        TOTAL_NBA_WINS - adjusted_wins.sum()
    ) / len(adjusted_wins)

    base_wins = np.floor(
        adjusted_wins
    ).astype(int)

    remaining = (
        TOTAL_NBA_WINS - int(base_wins.sum())
    )

    fractions = adjusted_wins - base_wins

    if remaining > 0:
        order = np.argsort(-fractions)
        base_wins[order[:remaining]] += 1

    elif remaining < 0:
        order = np.argsort(fractions)
        base_wins[
            order[: abs(remaining)]
        ] -= 1

    if int(base_wins.sum()) != TOTAL_NBA_WINS:
        raise ValueError(
            "Rounded standings do not total 1,230 wins."
        )

    if not np.all(
        (base_wins >= 0)
        & (base_wins <= GAMES_PER_TEAM)
    ):
        raise ValueError(
            "A projected record is outside 0-82."
        )

    return base_wins


def create_standings(
    baseline: pd.DataFrame,
    trade_rows: pd.DataFrame,
    scenario_id: str,
    scenario_status: str,
) -> pd.DataFrame:
    """Apply one trade scenario to baseline standings."""

    deltas = calculate_team_deltas(
        trade_rows
    )

    standings = baseline[
        [
            "conference",
            "team",
            "projected_wins",
        ]
    ].copy()

    standings = standings.rename(
        columns={
            "projected_wins": "baseline_wins",
        }
    )

    standings = standings.merge(
        deltas[
            ["team", "trade_win_delta"]
        ],
        on="team",
        how="left",
        validate="one_to_one",
    )

    standings["trade_win_delta"] = (
        standings["trade_win_delta"].fillna(0)
    )

    standings["adjusted_wins_raw"] = (
        standings["baseline_wins"]
        + standings["trade_win_delta"]
    )

    standings["projected_wins"] = (
        integerize_wins(
            standings[
                "adjusted_wins_raw"
            ].to_numpy()
        )
    )

    standings["projected_losses"] = (
        GAMES_PER_TEAM
        - standings["projected_wins"]
    )

    standings["projected_win_pct"] = (
        standings["projected_wins"]
        / GAMES_PER_TEAM
    )

    standings["scenario_id"] = scenario_id
    standings["scenario_status"] = (
        scenario_status
    )

    standings = standings.sort_values(
        [
            "conference",
            "projected_wins",
            "adjusted_wins_raw",
        ],
        ascending=[True, False, False],
    ).reset_index(drop=True)

    standings["conference_seed"] = (
        standings.groupby("conference")
        .cumcount()
        .add(1)
    )

    return standings


def build_all_scenarios(
    baseline: pd.DataFrame,
    trade_players: pd.DataFrame,
) -> pd.DataFrame:
    """Create official standings plus individual scenarios."""

    official_rows = trade_players.loc[
        trade_players["status"] == "OFFICIAL"
    ].copy()

    scenario_frames = [
        create_standings(
            baseline=baseline,
            trade_rows=official_rows,
            scenario_id="OFFICIAL_ONLY",
            scenario_status="OFFICIAL",
        )
    ]

    non_official = trade_players.loc[
        trade_players["status"] != "OFFICIAL"
    ].copy()

    for transaction_id in sorted(
        non_official["transaction_id"].unique()
    ):
        transaction_rows = non_official.loc[
            non_official["transaction_id"]
            == transaction_id
        ].copy()

        transaction_statuses = (
            transaction_rows["status"].unique()
        )

        if len(transaction_statuses) != 1:
            raise ValueError(
                f"{transaction_id} has mixed statuses."
            )

        scenario_rows = pd.concat(
            [
                official_rows,
                transaction_rows,
            ],
            ignore_index=True,
        )

        scenario_frames.append(
            create_standings(
                baseline=baseline,
                trade_rows=scenario_rows,
                scenario_id=transaction_id,
                scenario_status=str(
                    transaction_statuses[0]
                ),
            )
        )

    all_scenarios = pd.concat(
        scenario_frames,
        ignore_index=True,
    )

    return all_scenarios


def validate_outputs(
    player_impacts: pd.DataFrame,
    trade_players: pd.DataFrame,
    scenarios: pd.DataFrame,
) -> None:
    """Run final safety checks."""

    if trade_players["player_id"].nunique() != 40:
        raise ValueError(
            "Expected exactly 40 traded players."
        )

    if player_impacts[
        "impact_confidence"
    ].between(0, 1).all() is False:
        raise ValueError(
            "Impact confidence must be between 0 and 1."
        )

    wins_per_scenario = scenarios.groupby(
        "scenario_id"
    )["projected_wins"].sum()

    if not wins_per_scenario.eq(
        TOTAL_NBA_WINS
    ).all():
        raise ValueError(
            "Every scenario must total 1,230 wins."
        )

    teams_per_scenario = scenarios.groupby(
        "scenario_id"
    )["team"].nunique()

    if not teams_per_scenario.eq(30).all():
        raise ValueError(
            "Every scenario must contain 30 teams."
        )


def build_trade_impact() -> None:
    """Build player impact and trade-adjusted standings."""

    player_seasons, trades, baseline = (
        load_inputs()
    )

    player_impacts, replacement_pie = (
        calculate_player_impacts(
            player_seasons
        )
    )

    trade_players = connect_trades_to_impacts(
        trades,
        player_impacts,
    )

    scenarios = build_all_scenarios(
        baseline,
        trade_players,
    )

    validate_outputs(
        player_impacts,
        trade_players,
        scenarios,
    )

    official_rows = trade_players.loc[
        trade_players["status"] == "OFFICIAL"
    ]

    official_deltas = calculate_team_deltas(
        official_rows
    ).sort_values(
        "trade_win_delta",
        ascending=False,
    )

    official_standings = scenarios.loc[
        scenarios["scenario_id"]
        == "OFFICIAL_ONLY"
    ].copy()

    PLAYER_IMPACT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    player_impacts.to_parquet(
        PLAYER_IMPACT_FILE,
        index=False,
    )

    trade_players.to_csv(
        TRADE_IMPACT_FILE,
        index=False,
    )

    scenarios.to_csv(
        SCENARIO_FILE,
        index=False,
    )

    official_standings.to_csv(
        OFFICIAL_STANDINGS_FILE,
        index=False,
    )

    traded_display = trade_players[
        [
            "asset_name",
            "from_team",
            "to_team",
            "status",
            "weighted_pie",
            "weighted_minutes",
            "weighted_availability",
            "estimated_wins_above_replacement",
            "impact_confidence",
        ]
    ].copy()

    traded_display = traded_display.sort_values(
        "estimated_wins_above_replacement",
        ascending=False,
    )

    numeric_display_columns = [
        "weighted_pie",
        "weighted_minutes",
        "weighted_availability",
        "estimated_wins_above_replacement",
        "impact_confidence",
    ]

    traded_display[
        numeric_display_columns
    ] = traded_display[
        numeric_display_columns
    ].round(3)

    official_delta_display = (
        official_deltas.copy()
    )

    official_delta_display[
        [
            "wins_received",
            "wins_sent",
            "trade_win_delta",
        ]
    ] = official_delta_display[
        [
            "wins_received",
            "wins_sent",
            "trade_win_delta",
        ]
    ].round(2)

    standings_display = official_standings[
        [
            "conference",
            "conference_seed",
            "team",
            "baseline_wins",
            "trade_win_delta",
            "projected_wins",
            "projected_losses",
        ]
    ].copy()

    standings_display["trade_win_delta"] = (
        standings_display[
            "trade_win_delta"
        ].round(2)
    )

    print("\nTRADE IMPACT PIPELINE COMPLETE\n")

    print(
        f"Replacement-level PIE: "
        f"{replacement_pie:.4f}"
    )

    print(
        f"Players evaluated: "
        f"{len(player_impacts):,}"
    )

    print(
        f"Traded players matched: "
        f"{trade_players['player_id'].nunique()}"
    )

    print(
        f"Scenarios created: "
        f"{scenarios['scenario_id'].nunique()}"
    )

    print("\nTraded-player impact estimates:\n")
    print(traded_display.to_string(index=False))

    print("\nOfficial team trade deltas:\n")
    print(
        official_delta_display.to_string(
            index=False
        )
    )

    print(
        "\nOfficial trade-adjusted "
        "2026-27 standings:\n"
    )

    print(standings_display.to_string(index=False))

    print(f"\nPlayer impacts: {PLAYER_IMPACT_FILE}")
    print(f"Trade details: {TRADE_IMPACT_FILE}")
    print(f"All scenarios: {SCENARIO_FILE}")
    print(
        f"Official standings: "
        f"{OFFICIAL_STANDINGS_FILE}"
    )


if __name__ == "__main__":
    build_trade_impact()