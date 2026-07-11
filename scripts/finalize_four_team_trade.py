from pathlib import Path
import shutil

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRADE_FILE = (
    PROJECT_ROOT
    / "data"
    / "manual"
    / "trades_2026.csv"
)

BACKUP_FILE = (
    PROJECT_ROOT
    / "data"
    / "snapshots"
    / "trades_before_four_team_final.csv"
)

OLD_IDS = {
    "2026_MIN_BKN_CHI_01",
    "2026_MIN_CHA_01",
}

FINAL_ID = "2026_MIN_BKN_CHI_CHA_01"

OFFICIAL_URL = (
    "https://www.nba.com/hornets/news/"
    "charlotte-hornets-acquire-naz-reid-"
    "multiple-draft-picks-from-minnesota-"
    "for-lamelo-ball-and-josh-green"
)


def finalize_trade() -> None:
    """Promote the final four-team trade to official."""

    BACKUP_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not BACKUP_FILE.exists():
        shutil.copy2(
            TRADE_FILE,
            BACKUP_FILE,
        )

    ledger = pd.read_csv(
        TRADE_FILE,
        dtype=str,
        keep_default_na=False,
    )

    matching_ids = OLD_IDS | {FINAL_ID}

    trade_mask = ledger[
        "transaction_id"
    ].isin(matching_ids)

    if trade_mask.sum() < 15:
        raise ValueError(
            "Could not find all four-team trade rows."
        )

    ledger.loc[
        trade_mask,
        "transaction_id",
    ] = FINAL_ID

    ledger.loc[
        trade_mask,
        "effective_date",
    ] = "2026-07-10"

    ledger.loc[
        trade_mask,
        "status",
    ] = "OFFICIAL"

    ledger.loc[
        trade_mask,
        "source_url",
    ] = OFFICIAL_URL

    ledger.loc[
        trade_mask,
        "source_updated_at",
    ] = "2026-07-10"

    ledger.loc[
        trade_mask,
        "verified_at_utc",
    ] = "2026-07-11"

    ledger.loc[
        trade_mask,
        "notes",
    ] = (
        "Official four-team trade finalized "
        "July 10 2026"
    )

    gueye_mask = (
        ledger["transaction_id"].eq(FINAL_ID)
        & ledger["player_id"].eq("1631338")
    )

    ledger.loc[
        gueye_mask,
        "to_team",
    ] = "CHA"

    spagnolo_exists = (
        ledger["transaction_id"].eq(FINAL_ID)
        & ledger["asset_name"].str.contains(
            "Matteo Spagnolo",
            regex=False,
        )
    ).any()

    if not spagnolo_exists:
        spagnolo_row = {
            "transaction_id": FINAL_ID,
            "announced_date": "2026-07-10",
            "effective_date": "2026-07-10",
            "from_team": "MIN",
            "to_team": "CHA",
            "asset_type": "DRAFT_RIGHTS",
            "asset_name": (
                "Matteo Spagnolo draft rights "
                "No. 50 pick in 2022"
            ),
            "player_id": "",
            "status": "OFFICIAL",
            "source_url": OFFICIAL_URL,
            "source_updated_at": "2026-07-10",
            "verified_at_utc": "2026-07-11",
            "notes": (
                "Official four-team trade finalized "
                "July 10 2026"
            ),
        }

        ledger = pd.concat(
            [
                ledger,
                pd.DataFrame([spagnolo_row]),
            ],
            ignore_index=True,
        )

    ledger.to_csv(
        TRADE_FILE,
        index=False,
    )

    print("FOUR-TEAM TRADE UPDATED")
    print("Trade rows updated:", int(trade_mask.sum()))
    print("Spagnolo added:", not spagnolo_exists)
    print("Total ledger rows:", len(ledger))
    print("Backup:", BACKUP_FILE)


if __name__ == "__main__":
    finalize_trade()