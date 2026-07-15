from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
BASELINE_FILE = (
    PROJECT_ROOT / "data" / "processed" / "baseline_2026_27.csv"
)
ROSTER_DELTA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "team_roster_deltas_2026_27.csv"
)
OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "offseason_standings_2026_27.csv"
)
REPORT_FILE = (
    PROJECT_ROOT / "reports" / "official_standings_2026_27.csv"
)

TOTAL_NBA_WINS = 1230
GAMES_PER_TEAM = 82


def integerize_wins(raw_wins: np.ndarray) -> np.ndarray:
    """Round wins while preserving exactly 1,230 league wins."""

    adjusted = raw_wins.astype(float, copy=True)
    adjusted += (TOTAL_NBA_WINS - adjusted.sum()) / len(adjusted)
    base_wins = np.floor(adjusted).astype(int)
    remaining = TOTAL_NBA_WINS - int(base_wins.sum())
    fractions = adjusted - base_wins

    if remaining > 0:
        order = np.argsort(-fractions)
        base_wins[order[:remaining]] += 1
    elif remaining < 0:
        order = np.argsort(fractions)
        base_wins[order[: abs(remaining)]] -= 1

    if int(base_wins.sum()) != TOTAL_NBA_WINS:
        raise ValueError("Projected wins do not total 1,230.")

    return base_wins


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the historical team baseline and complete roster deltas."""

    for path in [BASELINE_FILE, ROSTER_DELTA_FILE]:
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {path}")

    baseline = pd.read_csv(BASELINE_FILE)
    deltas = pd.read_csv(ROSTER_DELTA_FILE)

    if len(baseline) != 30 or baseline["team"].nunique() != 30:
        raise ValueError("Baseline must contain 30 unique teams.")
    if len(deltas) != 30 or deltas["team"].nunique() != 30:
        raise ValueError("Roster deltas must contain 30 unique teams.")

    return baseline, deltas


def build_offseason_standings() -> pd.DataFrame:
    """Project standings from every official 2026-27 roster."""

    baseline, deltas = load_inputs()
    final = baseline.merge(
        deltas,
        on="team",
        how="left",
        validate="one_to_one",
    )

    for scenario in ["low", "base", "high"]:
        delta = f"roster_win_delta_{scenario}"
        final[f"adjusted_wins_{scenario}_raw"] = (
            final["projected_wins"] + final[delta]
        )

    final = final.rename(
        columns={
            "projected_wins": "historical_baseline_wins",
            "projected_losses": "historical_baseline_losses",
            "projected_win_pct": "historical_baseline_win_pct",
        }
    )
    final["projected_wins"] = integerize_wins(
        final["adjusted_wins_base_raw"].to_numpy()
    )
    final["projected_losses"] = GAMES_PER_TEAM - final["projected_wins"]
    final["projected_win_pct"] = final["projected_wins"] / GAMES_PER_TEAM
    final["injury_win_adjustment_low"] = (
        final["roster_win_delta_low"] - final["roster_win_delta_base"]
    )
    final["injury_win_adjustment_high"] = (
        final["roster_win_delta_high"] - final["roster_win_delta_base"]
    )
    final["scenario_id"] = "ROSTER_PROJECTION_V2"
    final["scenario_status"] = "OFFICIAL_MOVES_WITH_INJURY_RANGES"
    final = final.sort_values(
        ["conference", "projected_wins", "adjusted_wins_base_raw"],
        ascending=[True, False, False],
    ).reset_index(drop=True)
    final["conference_seed"] = final.groupby("conference").cumcount() + 1

    if int(final["projected_wins"].sum()) != TOTAL_NBA_WINS:
        raise ValueError("League wins must total 1,230.")
    if int(final["projected_losses"].sum()) != TOTAL_NBA_WINS:
        raise ValueError("League losses must total 1,230.")
    if not (
        final["injury_win_adjustment_low"].le(0).all()
        and final["injury_win_adjustment_high"].ge(0).all()
    ):
        raise ValueError("Injury ranges do not surround the base case.")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(OUTPUT_FILE, index=False)
    final.to_csv(REPORT_FILE, index=False)

    print("\nCOURTVISION V2 STANDINGS COMPLETE\n")

    for conference in ["East", "West"]:
        display = final.loc[
            final["conference"] == conference,
            [
                "conference_seed",
                "team",
                "projected_wins",
                "projected_losses",
                "roster_win_delta_base",
                "injury_win_adjustment_low",
                "injury_win_adjustment_high",
            ],
        ].copy()
        numeric = display.select_dtypes(include="number").columns
        display[numeric] = display[numeric].round(2)
        print(f"\n{conference.upper()}\n")
        print(display.to_string(index=False))

    print(f"\nOutput: {OUTPUT_FILE}")
    print(f"GitHub report: {REPORT_FILE}")
    return final


if __name__ == "__main__":
    build_offseason_standings()
