"""Small, idempotent database upgrades for installations created by older releases.

This project does not yet use Alembic. These upgrades only ADD nullable columns and
backfill safe defaults, so existing records are preserved.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import inspect, text
from app import db


def _columns(table_name: str) -> set[str]:
    inspector = inspect(db.engine)
    if table_name not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _add_column(table_name: str, column_name: str, sql_type: str) -> bool:
    if column_name in _columns(table_name):
        return False
    with db.engine.begin() as connection:
        connection.execute(text(
            f'ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}'
        ))
    return True


def upgrade_database() -> list[str]:
    """Apply all known upgrades and return a list of performed changes."""
    changes: list[str] = []

    if _add_column("lab_results", "method", "VARCHAR(180)"):
        changes.append("lab_results.method")

    if _add_column("lab_requests", "created_at", "TIMESTAMP"):
        changes.append("lab_requests.created_at")

    if _add_column("lab_reports", "created_at", "TIMESTAMP"):
        changes.append("lab_reports.created_at")

    # Older rows may have NULL after ADD COLUMN. Backfill them so the UI always
    # shows a date and ordering remains deterministic.
    now = datetime.utcnow()
    with db.engine.begin() as connection:
        if "created_at" in _columns("lab_requests"):
            connection.execute(
                text("UPDATE lab_requests SET created_at = :now WHERE created_at IS NULL"),
                {"now": now},
            )
        if "created_at" in _columns("lab_reports"):
            connection.execute(
                text("UPDATE lab_reports SET created_at = :now WHERE created_at IS NULL"),
                {"now": now},
            )

    return changes
