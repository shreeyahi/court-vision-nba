from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

TRADE_STANDINGS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "standings_official_2026_27.csv"
)

ROSTER_MOVES_FILE = (
    PROJECT_ROOT
    / "data"
    / "manual"
    / "roster_moves_2026.csv"
)

PLAYER_IMPACT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "player_impact.parquet"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "offseason_standings_2026_27.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "official_standings_2026_27.csv"
)

MOVEMENT_REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "roster_move_impacts_2026.csv"
)

TOTAL_NBA_WINS = 1230
GAMES_PER_TEAM = 82


def integerize_wins(
    raw_wins: np.ndarray,
) -> np.ndarray:
    """Round wins while preserving exactly 1,230."""

    adjusted = raw_wins.astype(
        float,
        copy=True,
    )

    adjusted += (
        TOTAL_NBA_WINS - adjusted.sum()
    ) / len(adjusted)

    base_wins = np.floor(
        adjusted
    ).astype(int)

    remaining = (
        TOTAL_NBA_WINS - int(base_wins.sum())
    )

    fractions = adjusted - base_wins

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
            "Projected wins do not total 1,230."
        )

    return base_wins


def load_inputs() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Load trade standings, movements and impacts."""

    for path in [
        TRADE_STANDINGS_FILE,
        ROSTER_MOVES_FILE,
        PLAYER_IMPACT_FILE,
    ]:
        if not path.exists():
            raise FileNotFoundError(
                f"Missing required file: {path}"
            )

    standings = pd.read_csv(
        TRADE_STANDINGS_FILE
    )

    movements = pd.read_csv(
        ROSTER_MOVES_FILE,
        dtype={"player_id": "string"},
        keep_default_na=False,
    )

    impacts = pd.read_parquet(
        PLAYER_IMPACT_FILE
    )

    return standings, movements, impacts


def validate_movements(
    movements: pd.DataFrame,
) -> None:
    """Validate the manual roster-movement ledger."""

    required_columns = {
        "movement_id",
        "from_team",
        "to_team",
        "player_name",
        "player_id",
        "movement_type",
        "status",
        "source_url",
        "source_updated_at",
        "verified_at_utc",
        "notes",
    }

    missing_columns = required_columns - set(
        movements.columns
    )

    if missing_columns:
        raise ValueError(
            f"Movement ledger is missing: "
            f"{sorted(missing_columns)}"
        )

    if movements[
        "movement_id"
    ].duplicated().any():
        raise ValueError(
            "Duplicate movement IDs found."
        )

    valid_statuses = {
        "OFFICIAL",
        "REPORTED",
        "ON_HOLD",
    }

    invalid_statuses = (
        set(movements["status"])
        - valid_statuses
    )

    if invalid_statuses:
        raise ValueError(
            f"Invalid statuses: {invalid_statuses}"
        )

    if (
        movements["from_team"]
        == movements["to_team"]
    ).any():
        raise ValueError(
            "A movement cannot stay on the same team."
        )


def attach_player_impacts(
    movements: pd.DataFrame,
    impacts: pd.DataFrame,
) -> pd.DataFrame:
    """Attach NBA-based player impact when available."""

    movement_impacts = movements.copy()

    movement_impacts[
        "player_id_numeric"
    ] = pd.to_numeric(
        movement_impacts["player_id"],
        errors="coerce",
    ).astype("Int64")

    selected_impacts = impacts[
        [
            "player_id",
            "estimated_wins_above_replacement",
            "impact_confidence",
        ]
    ].copy()

    selected_impacts["player_id"] = (
        selected_impacts["player_id"].astype(
            "Int64"
        )
    )

    movement_impacts = movement_impacts.merge(
        selected_impacts,
        left_on="player_id_numeric",
        right_on="player_id",
        how="left",
        validate="many_to_one",
        suffixes=("", "_impact"),
    )

    known_player_mask = movement_impacts[
        "player_id_numeric"
    ].notna()

    missing_impact_mask = (
        known_player_mask
        & movement_impacts[
            "estimated_wins_above_replacement"
        ].isna()
    )

    if missing_impact_mask.any():
        missing_names = movement_impacts.loc[
            missing_impact_mask,
            "player_name",
        ].tolist()

        raise ValueError(
            f"Missing player impacts: {missing_names}"
        )

    movement_impacts[
        "impact_model_status"
    ] = np.where(
        known_player_mask,
        "MODELED",
        "NO_NBA_HISTORY",
    )

    movement_impacts[
        "estimated_wins_above_replacement"
    ] = movement_impacts[
        "estimated_wins_above_replacement"
    ].fillna(0)

    movement_impacts[
        "impact_confidence"
    ] = movement_impacts[
        "impact_confidence"
    ].fillna(0)

    return movement_impacts


def calculate_official_deltas(
    movement_impacts: pd.DataFrame,
    nba_teams: set[str],
) -> pd.DataFrame:
    """Calculate official free-agency team deltas."""

    official = movement_impacts.loc[
        movement_impacts["status"] == "OFFICIAL"
    ]

    deltas = {
        team: 0.0
        for team in nba_teams
    }

    impact_column = (
        "estimated_wins_above_replacement"
    )

    for row in official.itertuples(
        index=False
    ):
        player_value = float(
            getattr(row, impact_column)
        )

        if row.from_team in nba_teams:
            deltas[row.from_team] -= player_value

        if row.to_team in nba_teams:
            deltas[row.to_team] += player_value

    delta_frame = pd.DataFrame(
        {
            "team": list(deltas),
            "free_agency_win_delta": list(
                deltas.values()
            ),
        }
    )

    if not np.isclose(
        delta_frame[
            "free_agency_win_delta"
        ].sum(),
        0,
        atol=1e-8,
    ):
        raise ValueError(
            "Official roster deltas must sum to zero."
        )

    return delta_frame


def build_offseason_standings() -> pd.DataFrame:
    """Build final trade-and-free-agency standings."""

    standings, movements, impacts = (
        load_inputs()
    )

    validate_movements(movements)

    movement_impacts = (
        attach_player_impacts(
            movements,
            impacts,
        )
    )

    nba_teams = set(standings["team"])

    delta_frame = (
        calculate_official_deltas(
            movement_impacts,
            nba_teams,
        )
    )

    final_standings = standings.merge(
        delta_frame,
        on="team",
        how="left",
        validate="one_to_one",
    )

    final_standings[
        "free_agency_win_delta"
    ] = final_standings[
        "free_agency_win_delta"
    ].fillna(0)

    final_standings[
        "offseason_win_delta"
    ] = (
        final_standings["trade_win_delta"]
        + final_standings[
            "free_agency_win_delta"
        ]
    )

    final_standings[
        "adjusted_wins_raw"
    ] = (
        final_standings["baseline_wins"]
        + final_standings[
            "offseason_win_delta"
        ]
    )

    final_standings["projected_wins"] = (
        integerize_wins(
            final_standings[
                "adjusted_wins_raw"
            ].to_numpy()
        )
    )

    final_standings["projected_losses"] = (
        GAMES_PER_TEAM
        - final_standings["projected_wins"]
    )

    final_standings["projected_win_pct"] = (
        final_standings["projected_wins"]
        / GAMES_PER_TEAM
    )

    final_standings["scenario_id"] = (
        "ALL_OFFICIAL_OFFSEASON_MOVES"
    )

    final_standings["scenario_status"] = (
        "OFFICIAL"
    )

    final_standings = (
        final_standings.sort_values(
            [
                "conference",
                "projected_wins",
                "adjusted_wins_raw",
            ],
            ascending=[True, False, False],
        ).reset_index(drop=True)
    )

    final_standings[
        "conference_seed"
    ] = (
        final_standings.groupby(
            "conference"
        )
        .cumcount()
        .add(1)
    )

    if len(final_standings) != 30:
        raise ValueError(
            "Final standings must contain 30 teams."
        )

    if final_standings[
        "projected_wins"
    ].sum() != TOTAL_NBA_WINS:
        raise ValueError(
            "League wins must total 1,230."
        )

    if final_standings[
        "projected_losses"
    ].sum() != TOTAL_NBA_WINS:
        raise ValueError(
            "League losses must total 1,230."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_standings.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    final_standings.to_csv(
        REPORT_FILE,
        index=False,
    )

    movement_impacts.to_csv(
        MOVEMENT_REPORT_FILE,
        index=False,
    )

    print(
        "\nOFFSEASON STANDINGS COMPLETE\n"
    )

    print(
        "Official team-changing movements: "
        f"{(movement_impacts['status'] == 'OFFICIAL').sum()}"
    )

    print(
        "Reported movements excluded: "
        f"{(movement_impacts['status'] == 'REPORTED').sum()}"
    )

    for conference in ["East", "West"]:
        display = final_standings.loc[
            final_standings["conference"]
            == conference,
            [
                "conference_seed",
                "team",
                "projected_wins",
                "projected_losses",
                "trade_win_delta",
                "free_agency_win_delta",
                "offseason_win_delta",
            ],
        ].copy()

        display[
            [
                "trade_win_delta",
                "free_agency_win_delta",
                "offseason_win_delta",
            ]
        ] = display[
            [
                "trade_win_delta",
                "free_agency_win_delta",
                "offseason_win_delta",
            ]
        ].round(2)

        print(f"\n{conference.upper()}\n")
        print(display.to_string(index=False))

    print(f"\nOutput: {OUTPUT_FILE}")
    print(f"GitHub report: {REPORT_FILE}")

    return final_standings


if __name__ == "__main__":
    build_offseason_standings()