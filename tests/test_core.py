from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from courtvision.data.fetch_games import (
    convert_team_rows_to_games,
)
from courtvision.data.validate import (
    TRADE_FILE,
    validate_trade_file,
)
from courtvision.features.build_trade_impact import (
    calculate_team_deltas,
    integerize_wins,
)
from courtvision.features.build_roster_projections import (
    development_group,
    draft_bucket,
    normalize_minutes_and_value,
)
from courtvision.models.simulate import (
    game_win_probability,
    run_simulations,
    sample_regular_season,
    simulate_play_in,
    simulate_series,
)


def test_duplicate_matchup_label_is_parsed() -> None:
    """Protect the 2024-25 MIA/WAS bug from returning."""

    team_rows = pd.DataFrame(
        [
            {
                "GAME_ID": "0022400147",
                "GAME_DATE": "2024-11-02",
                "TEAM_ID": 1610612764,
                "TEAM_ABBREVIATION": "WAS",
                "MATCHUP": "MIA @ WAS",
                "WL": "L",
                "PTS": 98,
            },
            {
                "GAME_ID": "0022400147",
                "GAME_DATE": "2024-11-02",
                "TEAM_ID": 1610612748,
                "TEAM_ABBREVIATION": "MIA",
                "MATCHUP": "MIA @ WAS",
                "WL": "W",
                "PTS": 118,
            },
        ]
    )

    games = convert_team_rows_to_games(
        team_rows=team_rows,
        season="2024-25",
    )

    assert len(games) == 1

    game = games.iloc[0]

    assert game["home_team"] == "WAS"
    assert game["away_team"] == "MIA"
    assert game["home_points"] == 98
    assert game["away_points"] == 118
    assert game["home_win"] == 0
    assert game["point_margin"] == -20


def test_home_advantage_changes_game_probability() -> None:
    """Equal teams should favor whichever team is home."""

    strengths = {
        "AAA": 0.50,
        "BBB": 0.50,
    }

    home_probability = game_win_probability(
        team_a="AAA",
        team_b="BBB",
        strengths=strengths,
        home_team="AAA",
        home_advantage=0.064,
    )

    away_probability = game_win_probability(
        team_a="AAA",
        team_b="BBB",
        strengths=strengths,
        home_team="BBB",
        home_advantage=0.064,
    )

    assert home_probability == pytest.approx(
        0.564
    )

    assert away_probability == pytest.approx(
        0.436
    )


def test_series_is_reproducible() -> None:
    """The same random seed must return the same result."""

    strengths = {
        "AAA": 0.60,
        "BBB": 0.45,
    }

    winner_one = simulate_series(
        team_a="AAA",
        team_b="BBB",
        strengths=strengths,
        home_court_team="AAA",
        home_advantage=0.064,
        random_generator=np.random.default_rng(
            123
        ),
    )

    winner_two = simulate_series(
        team_a="AAA",
        team_b="BBB",
        strengths=strengths,
        home_court_team="AAA",
        home_advantage=0.064,
        random_generator=np.random.default_rng(
            123
        ),
    )

    assert winner_one == winner_two
    assert winner_one in {"AAA", "BBB"}


def test_play_in_preserves_top_six() -> None:
    """Seeds 1-6 should survive the Play-In unchanged."""

    ordered_teams = [
        f"T{number:02d}"
        for number in range(1, 16)
    ]

    strengths = {
        team: 0.50
        for team in ordered_teams
    }

    playoff_seeds = simulate_play_in(
        ordered_teams=ordered_teams,
        strengths=strengths,
        home_advantage=0.064,
        random_generator=np.random.default_rng(
            42
        ),
    )

    assert len(playoff_seeds) == 8
    assert len(set(playoff_seeds.values())) == 8

    for seed in range(1, 7):
        assert playoff_seeds[seed] == (
            ordered_teams[seed - 1]
        )


def test_sampled_season_preserves_league_wins() -> None:
    """One simulated league should remain near 1,230 wins."""

    projected_wins = np.full(
        30,
        41.0,
    )

    sampled_wins = sample_regular_season(
        projected_wins=projected_wins,
        forecast_mae_wins=9.56,
        random_generator=np.random.default_rng(
            42
        ),
    )

    assert len(sampled_wins) == 30

    assert sampled_wins.sum() == pytest.approx(
        1230
    )

    assert np.all(sampled_wins >= 5)
    assert np.all(sampled_wins <= 77)


def test_integer_records_total_1230_wins() -> None:
    """Rounded projected standings must remain possible."""

    raw_wins = np.full(
        30,
        41.2,
    )

    integer_wins = integerize_wins(
        raw_wins
    )

    assert integer_wins.sum() == 1230
    assert np.all(integer_wins >= 0)
    assert np.all(integer_wins <= 82)


def test_trade_deltas_are_zero_sum() -> None:
    """Value received by one team must leave another."""

    trade_rows = pd.DataFrame(
        [
            {
                "from_team": "AAA",
                "to_team": "BBB",
                "estimated_wins_above_replacement": 2.0,
            },
            {
                "from_team": "BBB",
                "to_team": "AAA",
                "estimated_wins_above_replacement": 1.0,
            },
        ]
    )

    deltas = calculate_team_deltas(
        trade_rows
    ).set_index("team")

    assert deltas[
        "trade_win_delta"
    ].sum() == pytest.approx(0)

    assert deltas.loc[
        "AAA",
        "trade_win_delta",
    ] == pytest.approx(-1)

    assert deltas.loc[
        "BBB",
        "trade_win_delta",
    ] == pytest.approx(1)


def create_synthetic_standings() -> pd.DataFrame:
    """Create 30 fake teams for a fast simulator test."""

    rows: list[dict[str, object]] = []

    projected_records = [
        56,
        54,
        52,
        50,
        48,
        46,
        44,
        42,
        40,
        38,
        36,
        34,
        32,
        30,
        28,
    ]

    for conference, prefix in [
        ("East", "E"),
        ("West", "W"),
    ]:
        for index, wins in enumerate(
            projected_records,
            start=1,
        ):
            rows.append(
                {
                    "scenario_id": "TEST",
                    "scenario_status": "OFFICIAL",
                    "conference": conference,
                    "team": (
                        f"{prefix}{index:02d}"
                    ),
                    "projected_wins": wins,
                    "projected_losses": 82 - wins,
                }
            )

    return pd.DataFrame(rows)


def test_complete_simulation_smoke_test() -> None:
    """Run 100 complete seasons and validate totals."""

    standings = create_synthetic_standings()

    results = run_simulations(
        standings=standings,
        simulations=100,
        random_seed=42,
        forecast_mae_wins=9.56,
        home_advantage=0.064,
    )

    assert len(results) == 30

    assert results[
        "championship_probability"
    ].sum() == pytest.approx(1)

    for conference in ["East", "West"]:
        conference_results = results.loc[
            results["conference"]
            == conference
        ]

        assert conference_results[
            "playoff_probability"
        ].sum() == pytest.approx(8)

        assert conference_results[
            "conference_finals_probability"
        ].sum() == pytest.approx(2)

        assert conference_results[
            "nba_finals_probability"
        ].sum() == pytest.approx(1)


def test_current_trade_ledger_passes() -> None:
    """The committed manual ledger must remain valid."""

    exit_code = validate_trade_file(
        TRADE_FILE
    )

    assert exit_code == 0


def test_forecast_season_experience_labels() -> None:
    """Career labels must describe the predicted 2026-27 season."""

    assert development_group(0, 20) == "ROOKIE"
    assert development_group(1, 21) == "SOPHOMORE"
    assert development_group(2, 22) == "THIRD_YEAR"
    assert development_group(12, 35) == "VETERAN_34_36"


@pytest.mark.parametrize(
    ("pick", "expected"),
    [
        (1, "PICKS_01_03"),
        (8, "PICKS_04_10"),
        (17, "PICKS_11_20"),
        (27, "PICKS_21_30"),
        (44, "SECOND_ROUND"),
        (np.nan, "UNDRAFTED_OR_INTERNATIONAL"),
    ],
)
def test_rookie_draft_buckets(
    pick: float,
    expected: str,
) -> None:
    """Every rookie must receive a stable historical prior."""

    assert draft_bucket(pick) == expected


def test_projected_rosters_allocate_240_minutes() -> None:
    """Rookies and injuries cannot create impossible team minutes."""

    rows = []

    for team in ["AAA", "BBB"]:
        for number in range(10):
            rows.append(
                {
                    "team": team,
                    "projected_pie": 0.10,
                    "projected_minutes_per_game": 24.0,
                    "availability_low": 0.50,
                    "availability_base": 0.75,
                    "availability_high": 1.00,
                    "return_effectiveness_low": 0.80,
                    "return_effectiveness_base": 0.90,
                    "return_effectiveness_high": 1.00,
                }
            )

    normalized = normalize_minutes_and_value(
        pd.DataFrame(rows),
        replacement=0.08,
    )

    totals = normalized.groupby("team")[
        "allocated_season_mpg_base"
    ].sum()

    assert np.allclose(totals.to_numpy(), 240)


def test_injury_ranges_change_sampled_season() -> None:
    """Known injury uncertainty must reach Monte Carlo standings."""

    projected = np.full(30, 41.0)
    low = np.zeros(30)
    high = np.zeros(30)
    low[0] = -8.0
    high[0] = 3.0

    sampled = sample_regular_season(
        projected_wins=projected,
        forecast_mae_wins=9.56,
        random_generator=np.random.default_rng(42),
        injury_adjustment_low=low,
        injury_adjustment_high=high,
    )

    assert sampled.sum() == pytest.approx(1230)
    assert np.all(sampled >= 5)
    assert np.all(sampled <= 77)
