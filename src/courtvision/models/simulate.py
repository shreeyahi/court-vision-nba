from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]

SCENARIO_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "standings_scenarios.csv"
)

GAMES_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "games.parquet"
)

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

DEFAULT_SCENARIO = "OFFICIAL_ONLY"
DEFAULT_SIMULATIONS = 20_000
DEFAULT_RANDOM_SEED = 42

# This came from our untouched 2025-26 test season.
DEFAULT_FORECAST_MAE_WINS = 9.56

TOTAL_NBA_WINS = 1230
GAMES_PER_TEAM = 82

COUNT_METRICS = [
    "top_six",
    "play_in",
    "playoffs",
    "second_round",
    "conference_finals",
    "nba_finals",
    "championship",
]


def load_scenario(
    scenario_id: str,
) -> pd.DataFrame:
    """Load one trade-adjusted standings scenario."""

    if not SCENARIO_FILE.exists():
        raise FileNotFoundError(
            f"Missing {SCENARIO_FILE}. Run "
            f"build_trade_impact.py first."
        )

    all_scenarios = pd.read_csv(
        SCENARIO_FILE
    )

    available_scenarios = sorted(
        all_scenarios[
            "scenario_id"
        ].unique()
    )

    if scenario_id not in available_scenarios:
        raise ValueError(
            f"Unknown scenario {scenario_id!r}. "
            f"Available: {available_scenarios}"
        )

    standings = all_scenarios.loc[
        all_scenarios["scenario_id"]
        == scenario_id
    ].copy()

    if len(standings) != 30:
        raise ValueError(
            f"Scenario {scenario_id} should have "
            f"30 teams, but has {len(standings)}."
        )

    if standings["team"].duplicated().any():
        raise ValueError(
            "Scenario contains duplicate teams."
        )

    conference_counts = standings.groupby(
        "conference"
    )["team"].nunique()

    if not conference_counts.eq(15).all():
        raise ValueError(
            "Each conference must contain 15 teams."
        )

    return standings


def calculate_home_advantage() -> tuple[
    float,
    float,
]:
    """Estimate home advantage from historical games."""

    if not GAMES_FILE.exists():
        raise FileNotFoundError(
            f"Missing {GAMES_FILE}. Run "
            f"fetch_games.py first."
        )

    games = pd.read_parquet(
        GAMES_FILE,
        columns=["home_win"],
    )

    historical_home_win_rate = float(
        games["home_win"].mean()
    )

    home_advantage = (
        historical_home_win_rate - 0.50
    )

    home_advantage = float(
        np.clip(
            home_advantage,
            0.02,
            0.12,
        )
    )

    return (
        historical_home_win_rate,
        home_advantage,
    )


def game_win_probability(
    team_a: str,
    team_b: str,
    strengths: dict[str, float],
    home_team: str,
    home_advantage: float,
) -> float:
    """Calculate Team A's chance using the Log5 formula."""

    strength_a = strengths[team_a]
    strength_b = strengths[team_b]

    denominator = (
        strength_a
        + strength_b
        - 2 * strength_a * strength_b
    )

    if np.isclose(denominator, 0):
        probability_a = 0.50
    else:
        probability_a = (
            strength_a
            - strength_a * strength_b
        ) / denominator

    if home_team == team_a:
        probability_a += home_advantage
    elif home_team == team_b:
        probability_a -= home_advantage
    else:
        raise ValueError(
            f"{home_team} is not playing in "
            f"{team_a} vs. {team_b}."
        )

    return float(
        np.clip(
            probability_a,
            0.05,
            0.95,
        )
    )


def simulate_game(
    team_a: str,
    team_b: str,
    strengths: dict[str, float],
    home_team: str,
    home_advantage: float,
    random_generator: np.random.Generator,
) -> str:
    """Simulate one basketball game."""

    probability_a = game_win_probability(
        team_a=team_a,
        team_b=team_b,
        strengths=strengths,
        home_team=home_team,
        home_advantage=home_advantage,
    )

    if random_generator.random() < probability_a:
        return team_a

    return team_b


def simulate_series(
    team_a: str,
    team_b: str,
    strengths: dict[str, float],
    home_court_team: str,
    home_advantage: float,
    random_generator: np.random.Generator,
) -> str:
    """Simulate a best-of-seven 2-2-1-1-1 series."""

    if home_court_team not in {
        team_a,
        team_b,
    }:
        raise ValueError(
            "Home-court team must be in the series."
        )

    road_team = (
        team_b
        if home_court_team == team_a
        else team_a
    )

    home_sequence = [
        home_court_team,
        home_court_team,
        road_team,
        road_team,
        home_court_team,
        road_team,
        home_court_team,
    ]

    wins = {
        team_a: 0,
        team_b: 0,
    }

    for home_team in home_sequence:
        winner = simulate_game(
            team_a=team_a,
            team_b=team_b,
            strengths=strengths,
            home_team=home_team,
            home_advantage=home_advantage,
            random_generator=random_generator,
        )

        wins[winner] += 1

        if wins[winner] == 4:
            return winner

    raise RuntimeError(
        "Best-of-seven series produced no winner."
    )


def simulate_play_in(
    ordered_teams: list[str],
    strengths: dict[str, float],
    home_advantage: float,
    random_generator: np.random.Generator,
) -> dict[int, str]:
    """Simulate the NBA 7-10 Play-In Tournament."""

    seed_seven = ordered_teams[6]
    seed_eight = ordered_teams[7]
    seed_nine = ordered_teams[8]
    seed_ten = ordered_teams[9]

    seven_eight_winner = simulate_game(
        team_a=seed_seven,
        team_b=seed_eight,
        strengths=strengths,
        home_team=seed_seven,
        home_advantage=home_advantage,
        random_generator=random_generator,
    )

    seven_eight_loser = (
        seed_eight
        if seven_eight_winner == seed_seven
        else seed_seven
    )

    nine_ten_winner = simulate_game(
        team_a=seed_nine,
        team_b=seed_ten,
        strengths=strengths,
        home_team=seed_nine,
        home_advantage=home_advantage,
        random_generator=random_generator,
    )

    final_play_in_winner = simulate_game(
        team_a=seven_eight_loser,
        team_b=nine_ten_winner,
        strengths=strengths,
        home_team=seven_eight_loser,
        home_advantage=home_advantage,
        random_generator=random_generator,
    )

    playoff_seeds = {
        seed_number: ordered_teams[
            seed_number - 1
        ]
        for seed_number in range(1, 7)
    }

    playoff_seeds[7] = seven_eight_winner
    playoff_seeds[8] = final_play_in_winner

    return playoff_seeds


def choose_home_court(
    team_a: str,
    team_b: str,
    seed_by_team: dict[str, int],
) -> str:
    """Give conference home court to the better seed."""

    if seed_by_team[team_a] < seed_by_team[team_b]:
        return team_a

    return team_b


def simulate_conference_playoffs(
    playoff_seeds: dict[int, str],
    strengths: dict[str, float],
    home_advantage: float,
    random_generator: np.random.Generator,
    counts: dict[
        str,
        dict[str, int],
    ],
) -> str:
    """Simulate one complete conference bracket."""

    seed_by_team = {
        team: seed
        for seed, team in playoff_seeds.items()
    }

    first_round_matchups = [
        (1, 8),
        (4, 5),
        (3, 6),
        (2, 7),
    ]

    first_round_winners: list[str] = []

    for higher_seed, lower_seed in (
        first_round_matchups
    ):
        team_a = playoff_seeds[higher_seed]
        team_b = playoff_seeds[lower_seed]

        winner = simulate_series(
            team_a=team_a,
            team_b=team_b,
            strengths=strengths,
            home_court_team=team_a,
            home_advantage=home_advantage,
            random_generator=random_generator,
        )

        first_round_winners.append(winner)
        counts["second_round"][winner] += 1

    semifinal_matchups = [
        (
            first_round_winners[0],
            first_round_winners[1],
        ),
        (
            first_round_winners[2],
            first_round_winners[3],
        ),
    ]

    conference_finalists: list[str] = []

    for team_a, team_b in semifinal_matchups:
        home_court_team = choose_home_court(
            team_a,
            team_b,
            seed_by_team,
        )

        winner = simulate_series(
            team_a=team_a,
            team_b=team_b,
            strengths=strengths,
            home_court_team=home_court_team,
            home_advantage=home_advantage,
            random_generator=random_generator,
        )

        conference_finalists.append(winner)

        counts[
            "conference_finals"
        ][winner] += 1

    team_a = conference_finalists[0]
    team_b = conference_finalists[1]

    home_court_team = choose_home_court(
        team_a,
        team_b,
        seed_by_team,
    )

    conference_champion = simulate_series(
        team_a=team_a,
        team_b=team_b,
        strengths=strengths,
        home_court_team=home_court_team,
        home_advantage=home_advantage,
        random_generator=random_generator,
    )

    counts[
        "nba_finals"
    ][conference_champion] += 1

    return conference_champion


def sample_regular_season(
    projected_wins: np.ndarray,
    forecast_mae_wins: float,
    random_generator: np.random.Generator,
) -> np.ndarray:
    """Sample future records using honest test error."""

    forecast_errors = random_generator.laplace(
        loc=0,
        scale=forecast_mae_wins,
        size=len(projected_wins),
    )

    sampled_wins = (
        projected_wins + forecast_errors
    )

    for _ in range(5):
        sampled_wins = np.clip(
            sampled_wins,
            5,
            77,
        )

        sampled_wins += (
            TOTAL_NBA_WINS
            - sampled_wins.sum()
        ) / len(sampled_wins)

    sampled_wins = np.clip(
        sampled_wins,
        5,
        77,
    )

    return sampled_wins


def run_simulations(
    standings: pd.DataFrame,
    simulations: int,
    random_seed: int,
    forecast_mae_wins: float,
    home_advantage: float,
) -> pd.DataFrame:
    """Run every season and postseason simulation."""

    if simulations < 100:
        raise ValueError(
            "Use at least 100 simulations."
        )

    if forecast_mae_wins <= 0:
        raise ValueError(
            "Forecast MAE must be positive."
        )

    random_generator = (
        np.random.default_rng(
            random_seed
        )
    )

    teams = standings["team"].tolist()

    projected_wins = standings[
        "projected_wins"
    ].to_numpy(dtype=float)

    conferences = standings.set_index(
        "team"
    )["conference"].to_dict()

    conference_teams = {
        conference: standings.loc[
            standings["conference"]
            == conference,
            "team",
        ].tolist()
        for conference in ["East", "West"]
    }

    counts = {
        metric: {
            team: 0
            for team in teams
        }
        for metric in COUNT_METRICS
    }

    seed_sums = {
        team: 0.0
        for team in teams
    }

    for _ in range(simulations):
        sampled_wins_array = (
            sample_regular_season(
                projected_wins,
                forecast_mae_wins,
                random_generator,
            )
        )

        sampled_wins = dict(
            zip(
                teams,
                sampled_wins_array,
            )
        )

        strengths = {
            team: float(
                np.clip(
                    sampled_wins[team]
                    / GAMES_PER_TEAM,
                    0.10,
                    0.90,
                )
            )
            for team in teams
        }

        conference_playoff_seeds: dict[
            str,
            dict[int, str],
        ] = {}

        for conference in ["East", "West"]:
            ordered_teams = sorted(
                conference_teams[conference],
                key=lambda team: (
                    sampled_wins[team],
                    random_generator.random(),
                ),
                reverse=True,
            )

            for seed, team in enumerate(
                ordered_teams,
                start=1,
            ):
                seed_sums[team] += seed

                if seed <= 6:
                    counts["top_six"][team] += 1

                elif seed <= 10:
                    counts["play_in"][team] += 1

            playoff_seeds = simulate_play_in(
                ordered_teams=ordered_teams,
                strengths=strengths,
                home_advantage=home_advantage,
                random_generator=random_generator,
            )

            conference_playoff_seeds[
                conference
            ] = playoff_seeds

            for team in playoff_seeds.values():
                counts["playoffs"][team] += 1

        east_champion = (
            simulate_conference_playoffs(
                playoff_seeds=(
                    conference_playoff_seeds[
                        "East"
                    ]
                ),
                strengths=strengths,
                home_advantage=home_advantage,
                random_generator=random_generator,
                counts=counts,
            )
        )

        west_champion = (
            simulate_conference_playoffs(
                playoff_seeds=(
                    conference_playoff_seeds[
                        "West"
                    ]
                ),
                strengths=strengths,
                home_advantage=home_advantage,
                random_generator=random_generator,
                counts=counts,
            )
        )

        if sampled_wins[east_champion] > (
            sampled_wins[west_champion]
        ):
            finals_home_court = east_champion

        elif sampled_wins[west_champion] > (
            sampled_wins[east_champion]
        ):
            finals_home_court = west_champion

        else:
            finals_home_court = (
                east_champion
                if random_generator.random() < 0.50
                else west_champion
            )

        nba_champion = simulate_series(
            team_a=east_champion,
            team_b=west_champion,
            strengths=strengths,
            home_court_team=finals_home_court,
            home_advantage=home_advantage,
            random_generator=random_generator,
        )

        counts[
            "championship"
        ][nba_champion] += 1

    result_rows: list[
        dict[str, object]
    ] = []

    indexed_standings = standings.set_index(
        "team"
    )

    for team in teams:
        conference = conferences[team]

        result_rows.append(
            {
                "scenario_id": (
                    indexed_standings.loc[
                        team,
                        "scenario_id",
                    ]
                ),
                "scenario_status": (
                    indexed_standings.loc[
                        team,
                        "scenario_status",
                    ]
                ),
                "conference": conference,
                "team": team,
                "projected_wins": (
                    indexed_standings.loc[
                        team,
                        "projected_wins",
                    ]
                ),
                "projected_losses": (
                    indexed_standings.loc[
                        team,
                        "projected_losses",
                    ]
                ),
                "average_seed": (
                    seed_sums[team]
                    / simulations
                ),
                "top_six_probability": (
                    counts["top_six"][team]
                    / simulations
                ),
                "play_in_probability": (
                    counts["play_in"][team]
                    / simulations
                ),
                "playoff_probability": (
                    counts["playoffs"][team]
                    / simulations
                ),
                "second_round_probability": (
                    counts["second_round"][team]
                    / simulations
                ),
                "conference_finals_probability": (
                    counts[
                        "conference_finals"
                    ][team]
                    / simulations
                ),
                "nba_finals_probability": (
                    counts["nba_finals"][team]
                    / simulations
                ),
                "championship_probability": (
                    counts["championship"][team]
                    / simulations
                ),
                "conference_final": (
                    "ECF"
                    if conference == "East"
                    else "WCF"
                ),
            }
        )

    results = pd.DataFrame(result_rows)

    results = results.sort_values(
        [
            "conference",
            "championship_probability",
            "nba_finals_probability",
        ],
        ascending=[True, False, False],
    ).reset_index(drop=True)

    validate_results(results)

    return results


def validate_results(
    results: pd.DataFrame,
) -> None:
    """Validate probability totals across every round."""

    if len(results) != 30:
        raise ValueError(
            "Simulation result must contain 30 teams."
        )

    if not np.isclose(
        results[
            "championship_probability"
        ].sum(),
        1,
    ):
        raise ValueError(
            "Championship probabilities must sum to 1."
        )

    expected_conference_totals = {
        "top_six_probability": 6,
        "play_in_probability": 4,
        "playoff_probability": 8,
        "second_round_probability": 4,
        "conference_finals_probability": 2,
        "nba_finals_probability": 1,
    }

    for conference in ["East", "West"]:
        conference_results = results.loc[
            results["conference"]
            == conference
        ]

        for column, expected_total in (
            expected_conference_totals.items()
        ):
            actual_total = conference_results[
                column
            ].sum()

            if not np.isclose(
                actual_total,
                expected_total,
            ):
                raise ValueError(
                    f"{conference} {column} totals "
                    f"{actual_total}, expected "
                    f"{expected_total}."
                )


def safe_scenario_name(
    scenario_id: str,
) -> str:
    """Create a safe filename from a scenario ID."""

    safe_name = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        scenario_id,
    )

    return safe_name.strip("_").lower()


def display_results(
    results: pd.DataFrame,
) -> None:
    """Print readable ECF, WCF and title odds."""

    display = results[
        [
            "conference",
            "team",
            "projected_wins",
            "average_seed",
            "playoff_probability",
            "conference_final",
            "conference_finals_probability",
            "nba_finals_probability",
            "championship_probability",
        ]
    ].copy()

    display["average_seed"] = (
        display["average_seed"].round(2)
    )

    probability_columns = [
        "playoff_probability",
        "conference_finals_probability",
        "nba_finals_probability",
        "championship_probability",
    ]

    display[probability_columns] = (
        display[probability_columns]
        .mul(100)
        .round(1)
    )

    display = display.rename(
        columns={
            "playoff_probability": "playoffs_%",
            "conference_finals_probability": (
                "ECF_WCF_%"
            ),
            "nba_finals_probability": "finals_%",
            "championship_probability": "title_%",
        }
    )

    print("\nPLAYOFF SIMULATION COMPLETE\n")

    for conference in ["East", "West"]:
        print(f"{conference}:\n")

        conference_display = display.loc[
            display["conference"]
            == conference
        ].sort_values(
            [
                "ECF_WCF_%",
                "finals_%",
            ],
            ascending=False,
        )

        print(
            conference_display.to_string(
                index=False
            )
        )

        print()

    title_display = display.sort_values(
        "title_%",
        ascending=False,
    ).head(10)

    print("Top 10 championship probabilities:\n")
    print(title_display.to_string(index=False))


def parse_arguments() -> argparse.Namespace:
    """Read command-line simulation options."""

    parser = argparse.ArgumentParser(
        description=(
            "Simulate NBA standings, play-in, "
            "playoffs and championship."
        )
    )

    parser.add_argument(
        "--scenario",
        default=DEFAULT_SCENARIO,
        help=(
            "Trade scenario ID. Default: "
            "OFFICIAL_ONLY."
        ),
    )

    parser.add_argument(
        "--simulations",
        type=int,
        default=DEFAULT_SIMULATIONS,
        help="Number of Monte Carlo seasons.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Random seed for reproducible results.",
    )

    parser.add_argument(
        "--forecast-mae-wins",
        type=float,
        default=DEFAULT_FORECAST_MAE_WINS,
        help=(
            "Historical mean absolute forecast "
            "error in wins."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Run and save the playoff simulator."""

    arguments = parse_arguments()

    standings = load_scenario(
        arguments.scenario
    )

    (
        historical_home_win_rate,
        home_advantage,
    ) = calculate_home_advantage()

    print(
        f"Running {arguments.simulations:,} "
        f"simulations for "
        f"{arguments.scenario}..."
    )

    print(
        f"Forecast uncertainty: "
        f"{arguments.forecast_mae_wins:.2f} "
        f"MAE wins"
    )

    print(
        f"Historical home win rate: "
        f"{historical_home_win_rate:.3f}"
    )

    results = run_simulations(
        standings=standings,
        simulations=arguments.simulations,
        random_seed=arguments.seed,
        forecast_mae_wins=(
            arguments.forecast_mae_wins
        ),
        home_advantage=home_advantage,
    )

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    scenario_name = safe_scenario_name(
        arguments.scenario
    )

    output_file = OUTPUT_DIRECTORY / (
        f"playoff_probabilities_"
        f"{scenario_name}.csv"
    )

    results.to_csv(
        output_file,
        index=False,
    )

    if arguments.scenario == DEFAULT_SCENARIO:
        default_output_file = (
            OUTPUT_DIRECTORY
            / "playoff_probabilities.csv"
        )

        results.to_csv(
            default_output_file,
            index=False,
        )

    metadata_file = OUTPUT_DIRECTORY / (
        f"simulation_metadata_"
        f"{scenario_name}.json"
    )

    metadata = {
        "scenario_id": arguments.scenario,
        "simulations": arguments.simulations,
        "random_seed": arguments.seed,
        "forecast_mae_wins": (
            arguments.forecast_mae_wins
        ),
        "historical_home_win_rate": (
            historical_home_win_rate
        ),
        "home_advantage_probability": (
            home_advantage
        ),
    }

    with metadata_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=2,
        )

    display_results(results)

    print(f"\nProbabilities: {output_file}")
    print(f"Metadata: {metadata_file}")


if __name__ == "__main__":
    main()