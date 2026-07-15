from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import (
    commonteamroster,
    drafthistory,
)
from nba_api.stats.static import teams


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DIRECTORY = PROJECT_ROOT / "data" / "raw" / "projection_inputs"
DRAFT_FILE = RAW_DIRECTORY / "draft_history.csv"
ROSTER_DIRECTORY = RAW_DIRECTORY / "rosters"
ROSTER_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rosters_2025_26.csv"
)
MANUAL_ROOKIE_FILE = (
    PROJECT_ROOT / "data" / "manual" / "rookies_2026.csv"
)

ROSTER_SEASON = "2025-26"
FORECAST_DRAFT_YEAR = 2026


def download_draft_history(force: bool = False) -> pd.DataFrame:
    """Download NBA Draft history once and cache it."""

    RAW_DIRECTORY.mkdir(parents=True, exist_ok=True)

    if DRAFT_FILE.exists() and not force:
        print("Using cached NBA Draft history")
        return pd.read_csv(DRAFT_FILE)

    print("Downloading NBA Draft history")
    frame = drafthistory.DraftHistory(
        league_id="00",
        timeout=60,
    ).get_data_frames()[0]

    if frame.empty:
        raise RuntimeError("NBA Draft history returned no rows.")

    frame.to_csv(DRAFT_FILE, index=False)
    print(f"Saved draft history: {DRAFT_FILE}")
    return frame


def download_team_roster(
    team_id: int,
    abbreviation: str,
    force: bool = False,
) -> pd.DataFrame:
    """Download and cache one end-of-season roster."""

    ROSTER_DIRECTORY.mkdir(parents=True, exist_ok=True)
    path = ROSTER_DIRECTORY / f"{abbreviation}_{ROSTER_SEASON}.csv"

    if path.exists() and not force:
        print(f"Using cached roster for {abbreviation}")
        return pd.read_csv(path)

    print(f"Downloading roster for {abbreviation}")
    frame = commonteamroster.CommonTeamRoster(
        team_id=team_id,
        season=ROSTER_SEASON,
        league_id_nullable="00",
        timeout=60,
    ).get_data_frames()[0]

    if frame.empty:
        raise RuntimeError(f"No roster returned for {abbreviation}.")

    frame.to_csv(path, index=False)
    time.sleep(1.0)
    return frame


def build_roster_file(force: bool = False) -> pd.DataFrame:
    """Create one clean 2025-26 roster table for all 30 teams."""

    frames: list[pd.DataFrame] = []

    for team in sorted(
        teams.get_teams(),
        key=lambda item: item["abbreviation"],
    ):
        roster = download_team_roster(
            team_id=int(team["id"]),
            abbreviation=str(team["abbreviation"]),
            force=force,
        )

        required = {"PLAYER_ID", "PLAYER", "AGE", "EXP"}
        missing = required - set(roster.columns)

        if missing:
            raise ValueError(
                f"{team['abbreviation']} roster is missing {sorted(missing)}"
            )

        selected = roster[
            ["PLAYER_ID", "PLAYER", "AGE", "EXP"]
        ].copy()
        selected.insert(0, "team", team["abbreviation"])
        frames.append(selected)

    combined = pd.concat(frames, ignore_index=True).rename(
        columns={
            "PLAYER_ID": "player_id",
            "PLAYER": "player_name",
            "AGE": "roster_age",
            "EXP": "listed_experience",
        }
    )

    combined["player_id"] = pd.to_numeric(
        combined["player_id"], errors="raise"
    ).astype("Int64")

    if combined["player_id"].duplicated().any():
        duplicates = combined.loc[
            combined["player_id"].duplicated(keep=False),
            ["player_id", "player_name", "team"],
        ]
        raise ValueError(
            "A player appears on multiple rosters:\n"
            + duplicates.to_string(index=False)
        )

    ROSTER_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(ROSTER_OUTPUT, index=False)
    return combined


def clean_draft_history(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep the draft fields required by the projection model."""

    required = {
        "PERSON_ID",
        "PLAYER_NAME",
        "SEASON",
        "ROUND_NUMBER",
        "OVERALL_PICK",
        "TEAM_ABBREVIATION",
    }
    missing = required - set(frame.columns)

    if missing:
        raise ValueError(f"Draft history is missing {sorted(missing)}")

    cleaned = frame[
        [
            "PERSON_ID",
            "PLAYER_NAME",
            "SEASON",
            "ROUND_NUMBER",
            "OVERALL_PICK",
            "TEAM_ABBREVIATION",
        ]
    ].rename(
        columns={
            "PERSON_ID": "player_id",
            "PLAYER_NAME": "player_name",
            "SEASON": "draft_year",
            "ROUND_NUMBER": "draft_round",
            "OVERALL_PICK": "overall_pick",
            "TEAM_ABBREVIATION": "team",
        }
    )

    for column in [
        "player_id",
        "draft_year",
        "draft_round",
        "overall_pick",
    ]:
        cleaned[column] = pd.to_numeric(
            cleaned[column], errors="coerce"
        ).astype("Int64")

    cleaned = cleaned.loc[
        cleaned["draft_year"].le(FORECAST_DRAFT_YEAR)
    ].copy()

    if not MANUAL_ROOKIE_FILE.exists():
        raise FileNotFoundError(
            f"Missing official 2026 rookie ledger: {MANUAL_ROOKIE_FILE}"
        )

    manual_rookies = pd.read_csv(MANUAL_ROOKIE_FILE)
    manual_required = {
        "player_id",
        "player_name",
        "draft_year",
        "draft_round",
        "overall_pick",
        "team",
        "source_url",
        "source_updated_at",
        "verified_at_utc",
    }
    manual_missing = manual_required - set(manual_rookies.columns)

    if manual_missing:
        raise ValueError(
            f"Rookie ledger is missing {sorted(manual_missing)}"
        )
    if len(manual_rookies) != 60:
        raise ValueError("The 2026 rookie ledger must contain 60 picks.")
    if manual_rookies["overall_pick"].nunique() != 60:
        raise ValueError("The rookie ledger must contain picks 1 through 60.")
    if manual_rookies["source_url"].fillna("").eq("").any():
        raise ValueError("Every rookie row needs an official source URL.")

    manual_core = manual_rookies[
        [
            "player_id",
            "player_name",
            "draft_year",
            "draft_round",
            "overall_pick",
            "team",
        ]
    ].copy()

    for column in [
        "player_id",
        "draft_year",
        "draft_round",
        "overall_pick",
    ]:
        manual_core[column] = pd.to_numeric(
            manual_core[column], errors="coerce"
        ).astype("Int64")

    cleaned = cleaned.loc[
        cleaned["draft_year"] != FORECAST_DRAFT_YEAR
    ]
    cleaned = pd.concat([cleaned, manual_core], ignore_index=True)

    identified = cleaned.dropna(subset=["player_id"])

    if identified.duplicated(["draft_year", "player_id"]).any():
        raise ValueError("Duplicate player-year rows in Draft history.")

    output = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "draft_history.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output, index=False)
    return cleaned


def main() -> None:
    """Download every external input used by roster projections."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()

    draft = clean_draft_history(
        download_draft_history(force=arguments.force)
    )
    rosters = build_roster_file(force=arguments.force)

    print("\nPROJECTION INPUT PIPELINE COMPLETE\n")
    print(f"Draft rows: {len(draft):,}")
    print(
        "2026 draft rows: "
        f"{(draft['draft_year'] == FORECAST_DRAFT_YEAR).sum()}"
    )
    print(f"Roster players: {len(rosters):,}")
    print(f"Roster teams: {rosters['team'].nunique()}")
    print(f"Rosters: {ROSTER_OUTPUT}")


if __name__ == "__main__":
    main()
