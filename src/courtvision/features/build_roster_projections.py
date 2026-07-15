from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PLAYER_FILE = (
    PROJECT_ROOT / "data" / "processed" / "player_seasons.parquet"
)
ROSTER_FILE = (
    PROJECT_ROOT / "data" / "processed" / "rosters_2025_26.csv"
)
DRAFT_FILE = PROJECT_ROOT / "data" / "processed" / "draft_history.csv"
TRADE_FILE = PROJECT_ROOT / "data" / "manual" / "trades_2026.csv"
MOVEMENT_FILE = (
    PROJECT_ROOT / "data" / "manual" / "roster_moves_2026.csv"
)
INJURY_FILE = PROJECT_ROOT / "data" / "manual" / "injuries_2026.csv"
BASELINE_FILE = (
    PROJECT_ROOT / "data" / "processed" / "baseline_2026_27.csv"
)

PLAYER_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "player_projections_2026_27.csv"
)
TEAM_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "team_roster_deltas_2026_27.csv"
)
CURVE_OUTPUT = (
    PROJECT_ROOT / "reports" / "development_curves_2026_27.csv"
)
METRIC_OUTPUT = (
    PROJECT_ROOT / "reports" / "player_projection_backtest.csv"
)
PLAYER_REPORT = (
    PROJECT_ROOT / "reports" / "player_projections_2026_27.csv"
)
TEAM_REPORT = (
    PROJECT_ROOT / "reports" / "team_roster_deltas_2026_27.csv"
)

FORECAST_START_YEAR = 2026
LATEST_SEASON = "2025-26"
GAMES_PER_TEAM = 82
TEAM_MINUTES_PER_GAME = 240.0
SHRINKAGE_STRENGTH = 40.0
ROOKIE_SHRINKAGE_STRENGTH = 25.0
RECENT_SEASON_WEIGHTS = {
    "2023-24": 0.15,
    "2024-25": 0.30,
    "2025-26": 0.55,
}
RATE_COLUMNS = [
    "player_impact_estimate",
    "minutes_per_game",
    "points_per_36",
]
DELTA_TARGETS = [
    "player_impact_estimate",
    "minutes_per_game",
    "points_per_36",
    "availability",
]


def season_start_year(season: str) -> int:
    """Return 2025 from a season label such as 2025-26."""

    return int(str(season).split("-")[0])


def normalize_name(value: object) -> str:
    """Create a conservative player-name matching key."""

    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def draft_bucket(overall_pick: object) -> str:
    """Create stable rookie-prior groups from draft position."""

    if pd.isna(overall_pick):
        return "UNDRAFTED_OR_INTERNATIONAL"

    pick = int(overall_pick)

    if pick <= 3:
        return "PICKS_01_03"
    if pick <= 10:
        return "PICKS_04_10"
    if pick <= 20:
        return "PICKS_11_20"
    if pick <= 30:
        return "PICKS_21_30"
    return "SECOND_ROUND"


def development_group(
    seasons_played: int,
    projected_age: float,
) -> str:
    """Use career year first, then veteran age bands."""

    if seasons_played <= 0:
        return "ROOKIE"
    if seasons_played == 1:
        return "SOPHOMORE"
    if seasons_played == 2:
        return "THIRD_YEAR"
    if projected_age <= 24:
        return "VETERAN_24_AND_UNDER"
    if projected_age <= 27:
        return "VETERAN_25_27"
    if projected_age <= 30:
        return "VETERAN_28_30"
    if projected_age <= 33:
        return "VETERAN_31_33"
    if projected_age <= 36:
        return "VETERAN_34_36"
    return "VETERAN_37_PLUS"


def parse_completed_seasons(value: object) -> int | None:
    """Convert NBA roster EXP into seasons completed by summer 2026."""

    text = str(value).strip().upper()

    if text in {"", "NAN", "NONE"}:
        return None
    if text == "R":
        return 1

    try:
        return int(float(text)) + 1
    except ValueError:
        return None


def load_inputs() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    set[str],
]:
    """Load and type every input used by the roster model."""

    paths = [
        PLAYER_FILE,
        ROSTER_FILE,
        DRAFT_FILE,
        TRADE_FILE,
        MOVEMENT_FILE,
        INJURY_FILE,
        BASELINE_FILE,
    ]
    missing = [path for path in paths if not path.exists()]

    if missing:
        raise FileNotFoundError(f"Missing projection inputs: {missing}")

    players = pd.read_parquet(PLAYER_FILE)
    rosters = pd.read_csv(
        ROSTER_FILE,
        dtype={"player_id": "Int64", "listed_experience": "string"},
    )
    draft = pd.read_csv(DRAFT_FILE, dtype={"player_id": "Int64"})
    trades = pd.read_csv(
        TRADE_FILE,
        dtype={"player_id": "string"},
        keep_default_na=False,
    )
    movements = pd.read_csv(
        MOVEMENT_FILE,
        dtype={"player_id": "string"},
        keep_default_na=False,
    )
    injuries = pd.read_csv(INJURY_FILE, dtype={"player_id": "Int64"})
    nba_teams = set(pd.read_csv(BASELINE_FILE)["team"])

    if len(nba_teams) != 30:
        raise ValueError("The baseline must contain 30 NBA teams.")

    players["season_start"] = players["season"].map(season_start_year)

    if "points_per_36" not in players.columns:
        players["points_per_36"] = np.where(
            players["minutes_per_game"] > 0,
            players["points_per_game"]
            / players["minutes_per_game"]
            * 36,
            0.0,
        )

    return (
        players,
        rosters,
        draft,
        trades,
        movements,
        injuries,
        nba_teams,
    )


def add_experience_to_history(
    players: pd.DataFrame,
    draft: pd.DataFrame,
) -> pd.DataFrame:
    """Add completed NBA seasons without mislabeling old veterans."""

    data = players.sort_values(["player_id", "season_start"]).copy()
    draft_years = (
        draft[["player_id", "draft_year"]]
        .dropna(subset=["player_id", "draft_year"])
        .drop_duplicates("player_id", keep="last")
    )
    data = data.merge(
        draft_years,
        on="player_id",
        how="left",
        validate="many_to_one",
    )
    data["observed_season_number"] = (
        data.groupby("player_id").cumcount() + 1
    )
    data["first_observed_start"] = data.groupby("player_id")[
        "season_start"
    ].transform("min")

    drafted_experience = (
        data["season_start"] - data["draft_year"] + 1
    )
    observed_experience = data["observed_season_number"].astype(float)
    early_censored = data["first_observed_start"].eq(
        players["season_start"].min()
    )
    observed_experience = np.where(
        early_censored,
        np.maximum(observed_experience, 3),
        observed_experience,
    )
    data["seasons_played"] = drafted_experience.fillna(
        pd.Series(observed_experience, index=data.index)
    )
    data["seasons_played"] = (
        data["seasons_played"].clip(lower=1).astype(int)
    )
    return data


def create_development_pairs(history: pd.DataFrame) -> pd.DataFrame:
    """Pair each player-season only with the immediately following year."""

    current_columns = [
        "player_id",
        "season_start",
        "age",
        "seasons_played",
        "games_played",
        *DELTA_TARGETS,
    ]
    current = history[current_columns].copy()
    following = history[
        ["player_id", "season_start", *DELTA_TARGETS]
    ].copy()
    following["season_start"] -= 1
    following = following.rename(
        columns={column: f"next_{column}" for column in DELTA_TARGETS}
    )

    pairs = current.merge(
        following,
        on=["player_id", "season_start"],
        how="inner",
        validate="one_to_one",
    )
    pairs = pairs.loc[
        (pairs["games_played"] >= 10)
        & (pairs["minutes_per_game"] >= 5)
    ].copy()
    pairs["target_season_start"] = pairs["season_start"] + 1
    pairs["projected_age"] = pairs["age"] + 1
    pairs["development_group"] = pairs.apply(
        lambda row: development_group(
            int(row["seasons_played"]),
            float(row["projected_age"]),
        ),
        axis=1,
    )

    for target in DELTA_TARGETS:
        delta = pairs[f"next_{target}"] - pairs[target]
        lower, upper = delta.quantile([0.05, 0.95])
        pairs[f"delta_{target}"] = delta.clip(lower, upper)

    return pairs


def fit_development_curves(pairs: pd.DataFrame) -> pd.DataFrame:
    """Fit shrunk age/career-stage changes for four player outcomes."""

    rows: list[dict[str, object]] = []

    for target in DELTA_TARGETS:
        column = f"delta_{target}"
        league_delta = float(pairs[column].mean())
        grouped = pairs.groupby("development_group")[column]

        for group, values in grouped:
            count = int(values.count())
            raw_delta = float(values.mean())
            weight = count / (count + SHRINKAGE_STRENGTH)
            rows.append(
                {
                    "development_group": group,
                    "target": target,
                    "sample_size": count,
                    "raw_mean_delta": raw_delta,
                    "league_mean_delta": league_delta,
                    "shrunk_delta": (
                        weight * raw_delta
                        + (1 - weight) * league_delta
                    ),
                }
            )

    return pd.DataFrame(rows)


def backtest_development_curves(pairs: pd.DataFrame) -> pd.DataFrame:
    """Compare V2 curves with a no-change forecast on 2025-26."""

    training = pairs.loc[pairs["target_season_start"] < 2025]
    testing = pairs.loc[pairs["target_season_start"] == 2025].copy()

    if training.empty or testing.empty:
        return pd.DataFrame(
            columns=["target", "rows", "naive_mae", "curve_mae"]
        )

    curves = fit_development_curves(training)
    rows: list[dict[str, object]] = []

    for target in DELTA_TARGETS:
        lookup = curves.loc[
            curves["target"] == target,
            ["development_group", "shrunk_delta"],
        ]
        evaluated = testing.merge(
            lookup,
            on="development_group",
            how="left",
            validate="many_to_one",
        )
        evaluated["shrunk_delta"] = evaluated["shrunk_delta"].fillna(0)
        actual = evaluated[f"next_{target}"]
        naive = evaluated[target]
        curve = evaluated[target] + evaluated["shrunk_delta"]
        rows.append(
            {
                "target": target,
                "rows": len(evaluated),
                "naive_mae": mean_absolute_error(actual, naive),
                "curve_mae": mean_absolute_error(actual, curve),
            }
        )

    metrics = pd.DataFrame(rows)
    metrics["selected_model"] = np.where(
        metrics["curve_mae"] < metrics["naive_mae"],
        "DEVELOPMENT_CURVE",
        "NO_CHANGE_BASELINE",
    )
    return metrics


def replacement_pie(players: pd.DataFrame) -> float:
    """Estimate replacement level from current low-minute NBA players."""

    latest = players.loc[players["season"] == LATEST_SEASON]
    pool = latest.loc[
        latest["minutes_per_game"].between(8, 18)
        & (latest["games_played"] >= 20)
    ]

    if len(pool) < 30:
        raise ValueError("Replacement-player pool is too small.")

    return float(pool["player_impact_estimate"].median())


def build_rookie_priors(
    players: pd.DataFrame,
    draft: pd.DataFrame,
    replacement: float,
) -> pd.DataFrame:
    """Learn rookie outcomes from older draft classes, not Summer League."""

    historical_draft = draft.loc[
        draft["draft_year"].between(2015, 2025)
    ].copy()
    historical_draft["draft_bucket"] = historical_draft[
        "overall_pick"
    ].map(draft_bucket)

    rookie_stats = players[
        [
            "player_id",
            "season_start",
            "player_impact_estimate",
            "minutes_per_game",
            "points_per_36",
            "availability",
        ]
    ].rename(columns={"season_start": "draft_year"})
    rookies = historical_draft.merge(
        rookie_stats,
        on=["player_id", "draft_year"],
        how="left",
        validate="one_to_one",
    )
    rookies["minutes_per_game"] = rookies["minutes_per_game"].fillna(0)
    rookies["availability"] = rookies["availability"].fillna(0)

    played = rookies["minutes_per_game"] > 0
    overall = {
        "player_impact_estimate": float(
            rookies.loc[played, "player_impact_estimate"].mean()
        ),
        "minutes_per_game": float(rookies["minutes_per_game"].mean()),
        "points_per_36": float(rookies.loc[played, "points_per_36"].mean()),
        "availability": float(rookies["availability"].mean()),
    }
    overall["player_impact_estimate"] = np.nan_to_num(
        overall["player_impact_estimate"], nan=replacement
    )
    overall["points_per_36"] = np.nan_to_num(
        overall["points_per_36"], nan=12.0
    )

    rows: list[dict[str, object]] = []

    for bucket, group in rookies.groupby("draft_bucket"):
        count = len(group)
        weight = count / (count + ROOKIE_SHRINKAGE_STRENGTH)
        played_group = group.loc[group["minutes_per_game"] > 0]
        row: dict[str, object] = {
            "draft_bucket": bucket,
            "sample_size": count,
        }

        for target in DELTA_TARGETS:
            source = played_group if target in {
                "player_impact_estimate",
                "points_per_36",
            } else group
            raw = float(source[target].mean())
            raw = float(np.nan_to_num(raw, nan=overall[target]))
            row[target] = weight * raw + (1 - weight) * overall[target]

        rows.append(row)

    rows.append(
        {
            "draft_bucket": "UNDRAFTED_OR_INTERNATIONAL",
            "sample_size": 0,
            "player_impact_estimate": replacement,
            "minutes_per_game": 7.0,
            "points_per_36": overall["points_per_36"] * 0.85,
            "availability": 0.25,
        }
    )
    return pd.DataFrame(rows)


def add_or_move_player(
    roster: pd.DataFrame,
    player_id: object,
    player_name: str,
    destination: str,
    nba_teams: set[str],
) -> pd.DataFrame:
    """Move a player by NBA ID, adding new external arrivals when needed."""

    result = roster.copy()
    numeric_id = pd.to_numeric(player_id, errors="coerce")

    if pd.notna(numeric_id):
        mask = result["player_id"].eq(int(numeric_id))
    else:
        mask = result["name_key"].eq(normalize_name(player_name))

    if destination not in nba_teams:
        return result.loc[~mask].copy()

    if mask.any():
        result.loc[mask, "team"] = destination
        return result

    new_row = pd.DataFrame(
        [
            {
                "team": destination,
                "player_id": numeric_id,
                "player_name": player_name,
                "roster_age": np.nan,
                "listed_experience": pd.NA,
                "name_key": normalize_name(player_name),
            }
        ]
    )
    return pd.concat([result, new_row], ignore_index=True)


def build_forecast_roster(
    rosters: pd.DataFrame,
    draft: pd.DataFrame,
    trades: pd.DataFrame,
    movements: pd.DataFrame,
    nba_teams: set[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply every official move and add the 2026 draft class."""

    roster = rosters.copy()
    roster["name_key"] = roster["player_name"].map(normalize_name)

    official_trade_players = trades.loc[
        (trades["status"] == "OFFICIAL")
        & (trades["asset_type"] == "PLAYER")
    ]

    for row in official_trade_players.itertuples(index=False):
        roster = add_or_move_player(
            roster,
            row.player_id,
            row.asset_name,
            row.to_team,
            nba_teams,
        )

    for row in movements.loc[
        movements["status"] == "OFFICIAL"
    ].itertuples(index=False):
        roster = add_or_move_player(
            roster,
            row.player_id,
            row.player_name,
            row.to_team,
            nba_teams,
        )

    current_draft = draft.loc[draft["draft_year"] == 2026].copy()
    current_draft["draft_bucket"] = current_draft["overall_pick"].map(
        draft_bucket
    )
    current_draft["name_key"] = current_draft["player_name"].map(
        normalize_name
    )

    rights = trades.loc[
        (trades["status"] == "OFFICIAL")
        & (trades["asset_type"] == "DRAFT_RIGHTS")
    ]

    for row in rights.itertuples(index=False):
        asset_key = normalize_name(
            re.split(r"\s+(?:draft rights|No\.)", row.asset_name)[0]
        )
        current_draft.loc[
            current_draft["name_key"] == asset_key,
            "team",
        ] = row.to_team

    rookie_roster = current_draft[
        ["team", "player_id", "player_name", "name_key"]
    ].copy()
    rookie_roster["roster_age"] = np.nan
    rookie_roster["listed_experience"] = "R"
    roster = roster.loc[
        ~roster["player_id"].isin(rookie_roster["player_id"].dropna())
    ]
    roster = pd.concat([roster, rookie_roster], ignore_index=True)
    roster = roster.loc[roster["team"].isin(nba_teams)].copy()

    identity = roster["player_id"].astype("string").fillna(
        "NAME:" + roster["name_key"]
    )
    roster["player_key"] = identity

    if roster["player_key"].duplicated().any():
        duplicates = roster.loc[
            roster["player_key"].duplicated(keep=False),
            ["player_key", "player_name", "team"],
        ]
        raise ValueError(
            "Duplicate forecast-roster players:\n"
            + duplicates.to_string(index=False)
        )

    return roster, current_draft


def weighted_profile(
    player_rows: pd.DataFrame,
    completed_seasons: int,
) -> dict[str, float]:
    """Build recent rate, role and availability baselines."""

    selected = player_rows.loc[
        player_rows["season"].isin(RECENT_SEASON_WEIGHTS)
    ].copy()
    selected["weight"] = selected["season"].map(RECENT_SEASON_WEIGHTS)

    if selected.empty:
        raise ValueError("Cannot profile a player with no NBA history.")

    result: dict[str, float] = {}

    for column in RATE_COLUMNS:
        valid = selected[column].notna()
        result[column] = float(
            np.average(
                selected.loc[valid, column],
                weights=selected.loc[valid, "weight"],
            )
        )

    first_start = int(player_rows["season_start"].min())
    availability_values: list[float] = []
    availability_weights: list[float] = []

    for season, weight in RECENT_SEASON_WEIGHTS.items():
        start = season_start_year(season)

        if start < first_start and completed_seasons <= 3:
            continue

        match = selected.loc[selected["season"] == season]
        value = 0.0 if match.empty else float(match.iloc[0]["availability"])
        availability_values.append(value)
        availability_weights.append(weight)

    result["availability"] = float(
        np.average(availability_values, weights=availability_weights)
    )
    return result


def curve_lookup(curves: pd.DataFrame) -> dict[tuple[str, str], float]:
    """Turn the long development table into a safe lookup."""

    return {
        (str(row.development_group), str(row.target)): float(
            row.shrunk_delta
        )
        for row in curves.itertuples(index=False)
    }


def project_players(
    roster: pd.DataFrame,
    current_draft: pd.DataFrame,
    history: pd.DataFrame,
    curves: pd.DataFrame,
    rookie_priors: pd.DataFrame,
    injuries: pd.DataFrame,
    replacement: float,
) -> pd.DataFrame:
    """Project rate, role, availability and scoring for every player."""

    delta_lookup = curve_lookup(curves)
    rookie_lookup = rookie_priors.set_index("draft_bucket").to_dict("index")
    identified_rookies = current_draft.dropna(subset=["player_id"])
    draft_id_lookup = identified_rookies.set_index("player_id").to_dict(
        "index"
    )
    draft_name_lookup = current_draft.set_index("name_key").to_dict("index")
    injury_lookup = injuries.set_index("player_id").to_dict("index")
    rows: list[dict[str, object]] = []

    for roster_row in roster.itertuples(index=False):
        player_id = (
            None if pd.isna(roster_row.player_id) else int(roster_row.player_id)
        )
        player_history = history.loc[history["player_id"] == player_id]
        current_rookie = draft_id_lookup.get(player_id)

        if current_rookie is None:
            current_rookie = draft_name_lookup.get(roster_row.name_key)
        completed = parse_completed_seasons(roster_row.listed_experience)

        if completed is None and not player_history.empty:
            completed = int(player_history["seasons_played"].max())

        if current_rookie is not None:
            completed = 0

        completed = 0 if completed is None else completed

        if pd.notna(roster_row.roster_age):
            projected_age = float(roster_row.roster_age) + 1
        elif not player_history.empty:
            latest = player_history.sort_values("season_start").iloc[-1]
            projected_age = float(latest["age"]) + (
                FORECAST_START_YEAR - int(latest["season_start"])
            )
        else:
            projected_age = 20.5 if completed == 0 else 27.0

        group = development_group(completed, projected_age)
        model_status = "NBA_HISTORY"

        if current_rookie is not None:
            bucket = str(current_rookie["draft_bucket"])
            prior = rookie_lookup[bucket]
            model_status = "ROOKIE_PRIOR"
            base = {target: float(prior[target]) for target in DELTA_TARGETS}
        elif player_history.empty:
            bucket = "UNDRAFTED_OR_INTERNATIONAL"
            prior = rookie_lookup[bucket]
            model_status = "NO_NBA_HISTORY_PRIOR"
            base = {target: float(prior[target]) for target in DELTA_TARGETS}
        else:
            base = weighted_profile(player_history, completed)
            bucket = "NOT_APPLICABLE"

            for target in DELTA_TARGETS:
                base[target] += delta_lookup.get((group, target), 0.0)

        projected_pie = float(
            np.clip(base["player_impact_estimate"], -0.05, 0.26)
        )
        projected_mpg = float(np.clip(base["minutes_per_game"], 0, 38))
        projected_points_36 = float(np.clip(base["points_per_36"], 0, 40))
        model_availability = float(np.clip(base["availability"], 0.05, 1))

        injury = injury_lookup.get(player_id)

        if injury is None:
            availability_low = model_availability
            availability_base = model_availability
            availability_high = model_availability
            effect_low = effect_base = effect_high = 1.0
            injury_status = "NO_CURRENT_OVERRIDE"
        else:
            availability_low = float(injury["availability_low"])
            availability_base = float(injury["availability_base"])
            availability_high = float(injury["availability_high"])
            effect_low = float(injury["return_effectiveness_low"])
            effect_base = float(injury["return_effectiveness_base"])
            effect_high = float(injury["return_effectiveness_high"])
            injury_status = str(injury["injury_status"])

        if not (
            0 <= availability_low <= availability_base <= availability_high <= 1
        ):
            raise ValueError(
                f"Invalid availability range for {roster_row.player_name}."
            )

        effective_pie_base = replacement + (
            projected_pie - replacement
        ) * effect_base
        effective_points_36 = projected_points_36 * effect_base
        projected_ppg = effective_points_36 * projected_mpg / 36

        rows.append(
            {
                "player_key": roster_row.player_key,
                "player_id": player_id,
                "player_name": roster_row.player_name,
                "team": roster_row.team,
                "projected_age": projected_age,
                "seasons_played_before_2026_27": completed,
                "experience_group": group,
                "draft_bucket": bucket,
                "model_status": model_status,
                "injury_status": injury_status,
                "projected_pie": projected_pie,
                "effective_pie_base": effective_pie_base,
                "projected_minutes_per_game": projected_mpg,
                "projected_points_per_36": projected_points_36,
                "projected_points_per_game": projected_ppg,
                "model_availability": model_availability,
                "availability_low": availability_low,
                "availability_base": availability_base,
                "availability_high": availability_high,
                "return_effectiveness_low": effect_low,
                "return_effectiveness_base": effect_base,
                "return_effectiveness_high": effect_high,
            }
        )

    return pd.DataFrame(rows)


def normalize_minutes_and_value(
    projections: pd.DataFrame,
    replacement: float,
) -> pd.DataFrame:
    """Allocate exactly 240 season-average minutes to every team."""

    output = projections.copy()

    for scenario in ["low", "base", "high"]:
        availability = f"availability_{scenario}"
        effectiveness = f"return_effectiveness_{scenario}"
        desired = f"desired_season_mpg_{scenario}"
        allocated = f"allocated_season_mpg_{scenario}"
        value = f"projected_wins_above_replacement_{scenario}"
        output[desired] = (
            output["projected_minutes_per_game"] * output[availability]
        )
        totals = output.groupby("team")[desired].transform("sum")

        if (totals <= 0).any():
            raise ValueError("A team has no projected rotation minutes.")

        output[allocated] = output[desired] * TEAM_MINUTES_PER_GAME / totals
        effective_pie = replacement + (
            output["projected_pie"] - replacement
        ) * output[effectiveness]
        output[value] = (
            (effective_pie - replacement)
            * (output[allocated] / 48)
            * GAMES_PER_TEAM
        ).clip(lower=-2, upper=12)

    minute_check = output.groupby("team")[
        "allocated_season_mpg_base"
    ].sum()

    if not np.allclose(minute_check.to_numpy(), TEAM_MINUTES_PER_GAME):
        raise ValueError("Projected team minutes do not equal 240.")

    return output


def actual_team_values(
    players: pd.DataFrame,
    replacement: float,
    nba_teams: set[str],
) -> pd.DataFrame:
    """Measure the roster value already embedded in the 2025-26 baseline."""

    latest = players.loc[
        (players["season"] == LATEST_SEASON)
        & players["team"].isin(nba_teams)
    ].copy()
    latest["actual_season_mpg"] = (
        latest["minutes_per_game"] * latest["availability"]
    )
    totals = latest.groupby("team")["actual_season_mpg"].transform("sum")
    latest["allocated_actual_mpg"] = (
        latest["actual_season_mpg"] * TEAM_MINUTES_PER_GAME / totals
    )
    latest["actual_wins_above_replacement"] = (
        (latest["player_impact_estimate"] - replacement)
        * (latest["allocated_actual_mpg"] / 48)
        * GAMES_PER_TEAM
    ).clip(lower=-2, upper=12)
    values = (
        latest.groupby("team", as_index=False)[
            "actual_wins_above_replacement"
        ]
        .sum()
        .rename(columns={"actual_wins_above_replacement": "old_roster_value"})
    )
    return values


def build_team_deltas(
    projections: pd.DataFrame,
    actual_values: pd.DataFrame,
    nba_teams: set[str],
) -> pd.DataFrame:
    """Compare the complete projected roster with last season's roster."""

    value_columns = {
        f"projected_wins_above_replacement_{scenario}": (
            f"new_roster_value_{scenario}"
        )
        for scenario in ["low", "base", "high"]
    }
    future = (
        projections.groupby("team", as_index=False)[list(value_columns)]
        .sum()
        .rename(columns=value_columns)
    )
    teams = pd.DataFrame({"team": sorted(nba_teams)})
    result = teams.merge(
        actual_values,
        on="team",
        how="left",
        validate="one_to_one",
    ).merge(
        future,
        on="team",
        how="left",
        validate="one_to_one",
    )

    if result.isna().any().any():
        raise ValueError("At least one team is missing a roster value.")

    for scenario in ["low", "base", "high"]:
        result[f"roster_win_delta_{scenario}"] = (
            result[f"new_roster_value_{scenario}"]
            - result["old_roster_value"]
        )

    result["injury_downside_wins"] = (
        result["roster_win_delta_base"] - result["roster_win_delta_low"]
    ).clip(lower=0)
    result["injury_upside_wins"] = (
        result["roster_win_delta_high"] - result["roster_win_delta_base"]
    ).clip(lower=0)
    return result


def validate_injuries(injuries: pd.DataFrame) -> None:
    """Reject unsourced or internally impossible injury assumptions."""

    required = {
        "player_id",
        "player_name",
        "team",
        "injury_status",
        "availability_low",
        "availability_base",
        "availability_high",
        "return_effectiveness_low",
        "return_effectiveness_base",
        "return_effectiveness_high",
        "source_url",
        "source_updated_at",
        "verified_at_utc",
        "notes",
    }
    missing = required - set(injuries.columns)

    if missing:
        raise ValueError(f"Injury ledger is missing {sorted(missing)}")
    if injuries["player_id"].duplicated().any():
        raise ValueError("Duplicate player IDs in injury ledger.")
    if injuries["source_url"].fillna("").eq("").any():
        raise ValueError("Every injury override needs a source URL.")

    valid = (
        injuries["availability_low"].between(0, 1)
        & injuries["availability_base"].between(0, 1)
        & injuries["availability_high"].between(0, 1)
        & (
            injuries["availability_low"]
            <= injuries["availability_base"]
        )
        & (
            injuries["availability_base"]
            <= injuries["availability_high"]
        )
    )

    if not valid.all():
        raise ValueError("Invalid injury availability range.")


def build_roster_projections() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the complete age, development, rookie and injury model."""

    (
        players,
        rosters,
        draft,
        trades,
        movements,
        injuries,
        nba_teams,
    ) = load_inputs()
    validate_injuries(injuries)
    history = add_experience_to_history(players, draft)
    pairs = create_development_pairs(history)
    curves = fit_development_curves(pairs)
    metrics = backtest_development_curves(pairs)

    if not metrics.empty:
        rejected_targets = set(
            metrics.loc[
                metrics["selected_model"] == "NO_CHANGE_BASELINE",
                "target",
            ]
        )
        curves.loc[
            curves["target"].isin(rejected_targets),
            "shrunk_delta",
        ] = 0.0

    replacement = replacement_pie(players)
    rookie_priors = build_rookie_priors(players, draft, replacement)
    roster, current_draft = build_forecast_roster(
        rosters,
        draft,
        trades,
        movements,
        nba_teams,
    )
    projections = project_players(
        roster,
        current_draft,
        history,
        curves,
        rookie_priors,
        injuries,
        replacement,
    )
    projections = normalize_minutes_and_value(projections, replacement)
    actual_values = actual_team_values(players, replacement, nba_teams)
    team_deltas = build_team_deltas(projections, actual_values, nba_teams)

    for path in [
        PLAYER_OUTPUT,
        TEAM_OUTPUT,
        CURVE_OUTPUT,
        METRIC_OUTPUT,
        PLAYER_REPORT,
        TEAM_REPORT,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)

    projections.to_csv(PLAYER_OUTPUT, index=False)
    projections.to_csv(PLAYER_REPORT, index=False)
    team_deltas.to_csv(TEAM_OUTPUT, index=False)
    team_deltas.to_csv(TEAM_REPORT, index=False)
    curves.to_csv(CURVE_OUTPUT, index=False)
    metrics.to_csv(METRIC_OUTPUT, index=False)

    print("\nROSTER PROJECTION PIPELINE COMPLETE\n")
    print(f"Projected players: {len(projections):,}")
    print(
        "2026 drafted rookies: "
        f"{(projections['model_status'] == 'ROOKIE_PRIOR').sum()}"
    )
    print(
        "Other players with no NBA history: "
        f"{(projections['model_status'] == 'NO_NBA_HISTORY_PRIOR').sum()}"
    )
    print(
        "Sophomores: "
        f"{(projections['experience_group'] == 'SOPHOMORE').sum()}"
    )
    print(
        "Third-year players: "
        f"{(projections['experience_group'] == 'THIRD_YEAR').sum()}"
    )
    print(f"Known injury overrides: {len(injuries)}")
    print(f"Replacement PIE: {replacement:.4f}")
    print(f"Players: {PLAYER_OUTPUT}")
    print(f"Team deltas: {TEAM_OUTPUT}")

    if not metrics.empty:
        print("\n2025-26 PLAYER BACKTEST\n")
        print(metrics.round(4).to_string(index=False))

    return projections, team_deltas


if __name__ == "__main__":
    build_roster_projections()
