from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRADE_FILE = PROJECT_ROOT / "data" / "manual" / "trades_2026.csv"

EXPECTED_COLUMNS = [
    "transaction_id",
    "announced_date",
    "effective_date",
    "from_team",
    "to_team",
    "asset_type",
    "asset_name",
    "player_id",
    "status",
    "source_url",
    "source_updated_at",
    "verified_at_utc",
    "notes",
]

TEAM_CODES = {
    "ATL",
    "BOS",
    "BKN",
    "CHA",
    "CHI",
    "CLE",
    "DAL",
    "DEN",
    "DET",
    "GSW",
    "HOU",
    "IND",
    "LAC",
    "LAL",
    "MEM",
    "MIA",
    "MIL",
    "MIN",
    "NOP",
    "NYK",
    "OKC",
    "ORL",
    "PHI",
    "PHX",
    "POR",
    "SAC",
    "SAS",
    "TOR",
    "UTA",
    "WAS",
}

VALID_STATUSES = {"OFFICIAL", "REPORTED", "ON_HOLD"}

VALID_ASSET_TYPES = {
    "PLAYER",
    "DRAFT_PICK",
    "PICK_SWAP",
    "DRAFT_RIGHTS",
    "CASH",
}


def is_valid_date(value: str) -> bool:
    """Return True when value uses YYYY-MM-DD format."""
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def validate_trade_file(path: Path) -> int:
    """Validate the trade ledger and return a shell exit code."""
    errors: list[str] = []

    if not path.exists():
        print(f"ERROR: Trade file was not found: {path}")
        return 1

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    if not rows:
        print("ERROR: Trade file is empty.")
        return 1

    header = rows[0]

    if header != EXPECTED_COLUMNS:
        errors.append(
            "Header does not match the expected columns.\n"
            f"Expected: {EXPECTED_COLUMNS}\n"
            f"Received: {header}"
        )

    records: list[tuple[int, dict[str, str]]] = []
    seen_rows: set[tuple[str, ...]] = set()

    for line_number, row in enumerate(rows[1:], start=2):
        if not row:
            errors.append(f"Line {line_number}: completely empty row.")
            continue

        if len(row) != len(EXPECTED_COLUMNS):
            errors.append(
                f"Line {line_number}: expected {len(EXPECTED_COLUMNS)} "
                f"columns but found {len(row)}."
            )
            continue

        row_key = tuple(row)

        if row_key in seen_rows:
            errors.append(f"Line {line_number}: exact duplicate row.")

        seen_rows.add(row_key)

        record = dict(zip(EXPECTED_COLUMNS, row))
        records.append((line_number, record))

    required_fields = {
        "transaction_id",
        "announced_date",
        "from_team",
        "to_team",
        "asset_type",
        "asset_name",
        "status",
        "source_url",
        "source_updated_at",
        "verified_at_utc",
    }

    for line_number, record in records:
        for field in required_fields:
            if not record[field].strip():
                errors.append(
                    f"Line {line_number}: required field '{field}' is empty."
                )

        if (
            record["from_team"] not in TEAM_CODES
            or record["to_team"] not in TEAM_CODES
        ):
            errors.append(
                f"Line {line_number}: invalid team code "
                f"{record['from_team']} -> {record['to_team']}."
            )

        if record["from_team"] == record["to_team"]:
            errors.append(
                f"Line {line_number}: from_team and to_team cannot match."
            )

        if record["status"] not in VALID_STATUSES:
            errors.append(
                f"Line {line_number}: invalid status '{record['status']}'."
            )

        if record["asset_type"] not in VALID_ASSET_TYPES:
            errors.append(
                f"Line {line_number}: invalid asset type "
                f"'{record['asset_type']}'."
            )

        if record["asset_type"] == "PLAYER":
            if not record["player_id"]:
                errors.append(
                    f"Line {line_number}: player '{record['asset_name']}' "
                    "is missing a player ID."
                )
            elif not record["player_id"].isdigit():
                errors.append(
                    f"Line {line_number}: player ID must contain only numbers."
                )

        for date_field in (
            "announced_date",
            "source_updated_at",
            "verified_at_utc",
        ):
            if record[date_field] and not is_valid_date(record[date_field]):
                errors.append(
                    f"Line {line_number}: '{date_field}' must use YYYY-MM-DD."
                )

        if record["effective_date"] and not is_valid_date(
            record["effective_date"]
        ):
            errors.append(
                f"Line {line_number}: effective_date must use YYYY-MM-DD."
            )

        if not record["source_url"].startswith("https://www.nba.com/"):
            errors.append(
                f"Line {line_number}: source must be an NBA.com URL."
            )

    transactions: dict[str, list[dict[str, str]]] = defaultdict(list)

    for _, record in records:
        transactions[record["transaction_id"]].append(record)

    for transaction_id, transaction_rows in transactions.items():
        statuses = {row["status"] for row in transaction_rows}

        if len(statuses) != 1:
            errors.append(
                f"Transaction {transaction_id}: contains multiple statuses."
            )

        involved_teams = {
            team
            for row in transaction_rows
            for team in (row["from_team"], row["to_team"])
        }

        if len(involved_teams) < 2:
            errors.append(
                f"Transaction {transaction_id}: must involve two or more teams."
            )

    if errors:
        print("\nTRADE LEDGER FAILED VALIDATION\n")

        for error in errors:
            print(f"- {error}")

        print(f"\nTotal errors: {len(errors)}")
        return 1

    status_counts = Counter(record["status"] for _, record in records)

    official_transactions = {
        transaction_id
        for transaction_id, transaction_rows in transactions.items()
        if transaction_rows[0]["status"] == "OFFICIAL"
    }

    scenario_transactions = set(transactions) - official_transactions

    blank_effective_dates = sum(
        not record["effective_date"] for _, record in records
    )

    print("\nTRADE LEDGER PASSED VALIDATION\n")
    print(f"File: {path}")
    print(f"Asset rows: {len(records)}")
    print(f"Transactions: {len(transactions)}")
    print(f"Official transactions: {len(official_transactions)}")
    print(f"Scenario transactions: {len(scenario_transactions)}")
    print(f"Status rows: {dict(status_counts)}")
    print(f"Blank effective dates: {blank_effective_dates}")

    return 0


if __name__ == "__main__":
    sys.exit(validate_trade_file(TRADE_FILE))