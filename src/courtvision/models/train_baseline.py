from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "team_seasons.parquet"
)

MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "baseline_win_pct.joblib"
)

PREDICTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "baseline_2026_27.csv"
)

FEATURE_COLUMNS = [
    "previous_win_pct",
    "previous_points_for_per_game",
    "previous_points_against_per_game",
    "previous_avg_point_margin",
    "two_season_win_pct",
    "two_season_avg_margin",
]

TARGET_COLUMN = "win_pct"
VALIDATION_SEASON = "2024-25"
TEST_SEASON = "2025-26"
PREDICTION_SEASON = "2026-27"
TOTAL_NBA_WINS = 1230


def load_team_seasons() -> pd.DataFrame:
    """Load the model-ready team-season report cards."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing {INPUT_FILE}. Run "
            f"build_team_seasons.py first."
        )

    team_seasons = pd.read_parquet(INPUT_FILE)

    required_columns = {
        "season",
        "team",
        "conference",
        TARGET_COLUMN,
        *FEATURE_COLUMNS,
    }

    missing_columns = required_columns - set(
        team_seasons.columns
    )

    if missing_columns:
        raise ValueError(
            f"Team-season data is missing columns: "
            f"{sorted(missing_columns)}"
        )

    return team_seasons


def create_candidate_models() -> dict[str, object]:
    """Create several models so we can compare them honestly."""

    return {
        "mean_baseline": DummyRegressor(
            strategy="mean",
        ),
        "ridge_0.1": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", Ridge(alpha=0.1)),
            ]
        ),
        "ridge_1": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", Ridge(alpha=1.0)),
            ]
        ),
        "ridge_10": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", Ridge(alpha=10.0)),
            ]
        ),
        "ridge_100": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", Ridge(alpha=100.0)),
            ]
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=500,
            max_depth=5,
            min_samples_leaf=4,
            max_features=0.8,
            random_state=42,
            n_jobs=-1,
        ),
    }


def calculate_metrics(
    actual: pd.Series,
    predicted: np.ndarray,
) -> dict[str, float]:
    """Measure prediction errors in win percentage and wins."""

    clipped_predictions = np.clip(predicted, 0, 1)

    mae_win_pct = mean_absolute_error(
        actual,
        clipped_predictions,
    )

    rmse_win_pct = np.sqrt(
        mean_squared_error(
            actual,
            clipped_predictions,
        )
    )

    return {
        "mae_win_pct": mae_win_pct,
        "mae_wins": mae_win_pct * 82,
        "rmse_win_pct": rmse_win_pct,
        "rmse_wins": rmse_win_pct * 82,
    }


def compare_models(
    training_data: pd.DataFrame,
    validation_data: pd.DataFrame,
) -> tuple[str, pd.DataFrame]:
    """Choose a model using only the validation season."""

    candidate_models = create_candidate_models()

    training_features = training_data[FEATURE_COLUMNS]
    training_target = training_data[TARGET_COLUMN]

    validation_features = validation_data[
        FEATURE_COLUMNS
    ]

    validation_target = validation_data[
        TARGET_COLUMN
    ]

    result_rows: list[dict[str, object]] = []

    for model_name, model in candidate_models.items():
        fitted_model = clone(model)

        fitted_model.fit(
            training_features,
            training_target,
        )

        predictions = fitted_model.predict(
            validation_features
        )

        metrics = calculate_metrics(
            validation_target,
            predictions,
        )

        result_rows.append(
            {
                "model": model_name,
                **metrics,
            }
        )

    results = pd.DataFrame(result_rows)

    results = results.sort_values(
        ["mae_wins", "rmse_wins"],
        ascending=True,
    ).reset_index(drop=True)

    selected_model_name = str(
        results.iloc[0]["model"]
    )

    return selected_model_name, results


def test_selected_model(
    selected_model_name: str,
    training_data: pd.DataFrame,
    validation_data: pd.DataFrame,
    test_data: pd.DataFrame,
) -> tuple[object, pd.DataFrame, dict[str, float]]:
    """Run one final honest test on the untouched test season."""

    candidate_models = create_candidate_models()

    selected_model = clone(
        candidate_models[selected_model_name]
    )

    development_data = pd.concat(
        [training_data, validation_data],
        ignore_index=True,
    )

    selected_model.fit(
        development_data[FEATURE_COLUMNS],
        development_data[TARGET_COLUMN],
    )

    test_predictions = np.clip(
        selected_model.predict(
            test_data[FEATURE_COLUMNS]
        ),
        0,
        1,
    )

    test_metrics = calculate_metrics(
        test_data[TARGET_COLUMN],
        test_predictions,
    )

    comparison = test_data[
        [
            "team",
            "conference",
            "wins",
            "losses",
            "win_pct",
        ]
    ].copy()

    comparison["predicted_win_pct"] = test_predictions

    comparison["predicted_wins"] = (
        comparison["predicted_win_pct"] * 82
    )

    comparison["absolute_error_wins"] = (
        comparison["predicted_wins"]
        - comparison["wins"]
    ).abs()

    comparison = comparison.sort_values(
        "absolute_error_wins",
        ascending=False,
    ).reset_index(drop=True)

    return selected_model, comparison, test_metrics


def build_future_features(
    team_seasons: pd.DataFrame,
) -> pd.DataFrame:
    """Turn 2025-26 results into inputs for 2026-27."""

    latest_data = team_seasons.loc[
        team_seasons["season"] == TEST_SEASON
    ].copy()

    if len(latest_data) != 30:
        raise ValueError(
            f"Expected 30 teams in {TEST_SEASON}, "
            f"but found {len(latest_data)}."
        )

    future = latest_data[
        ["team", "conference"]
    ].copy()

    future["season"] = PREDICTION_SEASON

    future["previous_win_pct"] = (
        latest_data["win_pct"].to_numpy()
    )

    future["previous_points_for_per_game"] = (
        latest_data["points_for_per_game"].to_numpy()
    )

    future["previous_points_against_per_game"] = (
        latest_data[
            "points_against_per_game"
        ].to_numpy()
    )

    future["previous_avg_point_margin"] = (
        latest_data["avg_point_margin"].to_numpy()
    )

    recent_two_seasons = (
        team_seasons.sort_values("season")
        .groupby("team", as_index=False)
        .tail(2)
    )

    two_season_averages = (
        recent_two_seasons.groupby("team")
        .agg(
            two_season_win_pct=(
                "win_pct",
                "mean",
            ),
            two_season_avg_margin=(
                "avg_point_margin",
                "mean",
            ),
        )
    )

    future["two_season_win_pct"] = (
        future["team"].map(
            two_season_averages[
                "two_season_win_pct"
            ]
        )
    )

    future["two_season_avg_margin"] = (
        future["team"].map(
            two_season_averages[
                "two_season_avg_margin"
            ]
        )
    )

    if future[FEATURE_COLUMNS].isna().any().any():
        raise ValueError(
            "Future prediction features contain missing values."
        )

    return future


def convert_to_integer_wins(
    predicted_win_pct: np.ndarray,
) -> np.ndarray:
    """Create integer records that total exactly 1,230 wins."""

    predicted_wins = np.clip(
        predicted_win_pct * 82,
        8,
        74,
    )

    predicted_wins = predicted_wins + (
        TOTAL_NBA_WINS - predicted_wins.sum()
    ) / len(predicted_wins)

    base_wins = np.floor(
        predicted_wins
    ).astype(int)

    remaining_wins = (
        TOTAL_NBA_WINS - int(base_wins.sum())
    )

    fractional_parts = (
        predicted_wins - base_wins
    )

    order = np.argsort(-fractional_parts)

    if remaining_wins > 0:
        base_wins[order[:remaining_wins]] += 1

    if int(base_wins.sum()) != TOTAL_NBA_WINS:
        raise ValueError(
            "Projected wins do not total 1,230."
        )

    return base_wins


def create_future_predictions(
    model: object,
    future: pd.DataFrame,
) -> pd.DataFrame:
    """Generate no-trade 2026-27 standings."""

    model_win_pct = np.clip(
        model.predict(future[FEATURE_COLUMNS]),
        0.10,
        0.90,
    )

    projected_wins = convert_to_integer_wins(
        model_win_pct
    )

    predictions = future[
        ["season", "conference", "team"]
    ].copy()

    predictions["model_win_pct"] = model_win_pct

    predictions["projected_wins"] = projected_wins

    predictions["projected_losses"] = (
        82 - predictions["projected_wins"]
    )

    predictions["projected_win_pct"] = (
        predictions["projected_wins"] / 82
    )

    predictions = predictions.sort_values(
        [
            "conference",
            "projected_wins",
            "model_win_pct",
        ],
        ascending=[True, False, False],
    ).reset_index(drop=True)

    predictions["conference_seed"] = (
        predictions.groupby("conference")
        .cumcount()
        .add(1)
    )

    return predictions


def train_baseline() -> None:
    """Select, test, save and use the baseline model."""

    team_seasons = load_team_seasons()

    model_data = team_seasons.dropna(
        subset=FEATURE_COLUMNS
    ).copy()

    training_data = model_data.loc[
        model_data["season"] < VALIDATION_SEASON
    ].copy()

    validation_data = model_data.loc[
        model_data["season"] == VALIDATION_SEASON
    ].copy()

    test_data = model_data.loc[
        model_data["season"] == TEST_SEASON
    ].copy()

    if len(validation_data) != 30:
        raise ValueError(
            "Validation season must contain 30 teams."
        )

    if len(test_data) != 30:
        raise ValueError(
            "Test season must contain 30 teams."
        )

    selected_name, validation_results = (
        compare_models(
            training_data,
            validation_data,
        )
    )

    _, test_comparison, test_metrics = (
        test_selected_model(
            selected_name,
            training_data,
            validation_data,
            test_data,
        )
    )

    final_model = clone(
        create_candidate_models()[selected_name]
    )

    final_model.fit(
        model_data[FEATURE_COLUMNS],
        model_data[TARGET_COLUMN],
    )

    future_features = build_future_features(
        team_seasons
    )

    future_predictions = (
        create_future_predictions(
            final_model,
            future_features,
        )
    )

    MODEL_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    PREDICTIONS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        {
            "model": final_model,
            "feature_columns": FEATURE_COLUMNS,
            "selected_model": selected_name,
            "training_through": TEST_SEASON,
        },
        MODEL_FILE,
    )

    future_predictions.to_csv(
        PREDICTIONS_FILE,
        index=False,
    )

    display_validation = validation_results.copy()

    for column in [
        "mae_win_pct",
        "rmse_win_pct",
    ]:
        display_validation[column] = (
            display_validation[column].round(4)
        )

    for column in [
        "mae_wins",
        "rmse_wins",
    ]:
        display_validation[column] = (
            display_validation[column].round(2)
        )

    display_test = test_comparison.head(10).copy()

    for column in [
        "win_pct",
        "predicted_win_pct",
    ]:
        display_test[column] = (
            display_test[column].round(3)
        )

    for column in [
        "predicted_wins",
        "absolute_error_wins",
    ]:
        display_test[column] = (
            display_test[column].round(1)
        )

    print("\nBASELINE MODEL TRAINING COMPLETE\n")
    print("Validation results:")
    print(
        display_validation.to_string(index=False)
    )

    print(f"\nSelected model: {selected_name}")

    print(
        f"Honest {TEST_SEASON} test MAE: "
        f"{test_metrics['mae_wins']:.2f} wins"
    )

    print(
        f"Honest {TEST_SEASON} test RMSE: "
        f"{test_metrics['rmse_wins']:.2f} wins"
    )

    print("\nLargest test-season errors:")
    print(display_test.to_string(index=False))

    print(
        f"\n{PREDICTION_SEASON} no-trade baseline:\n"
    )

    print(
        future_predictions[
            [
                "conference",
                "conference_seed",
                "team",
                "projected_wins",
                "projected_losses",
                "projected_win_pct",
            ]
        ].to_string(index=False)
    )

    print(f"\nModel: {MODEL_FILE}")
    print(f"Predictions: {PREDICTIONS_FILE}")


if __name__ == "__main__":
    train_baseline()