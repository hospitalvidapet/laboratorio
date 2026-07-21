"""Idempotent database upgrades for installations created by older releases.

The project still does not use Alembic. This module performs conservative,
additive upgrades only: it creates missing columns/tables and backfills safe
defaults without deleting existing records.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import inspect, text
from app import db


def _quote(identifier: str) -> str:
    """Quote a trusted internal SQL identifier for PostgreSQL/SQLite."""
    return '"' + identifier.replace('"', '""') + '"'


def _table_names() -> set[str]:
    return set(inspect(db.engine).get_table_names())


def _columns(table_name: str) -> set[str]:
    inspector = inspect(db.engine)
    if table_name not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _add_column(table_name: str, column_name: str, sql_type: str) -> bool:
    """Add a nullable column if it is absent.

    Columns are intentionally added without NOT NULL constraints. Existing rows
    are backfilled immediately afterwards, while SQLAlchemy continues to enforce
    required fields for newly created records.
    """
    if table_name not in _table_names() or column_name in _columns(table_name):
        return False
    statement = (
        f"ALTER TABLE {_quote(table_name)} "
        f"ADD COLUMN {_quote(column_name)} {sql_type}"
    )
    with db.engine.begin() as connection:
        connection.execute(text(statement))
    return True


def _backfill(table_name: str, column_name: str, value, where_sql: str | None = None) -> None:
    if table_name not in _table_names() or column_name not in _columns(table_name):
        return
    condition = where_sql or f"{_quote(column_name)} IS NULL"
    with db.engine.begin() as connection:
        connection.execute(
            text(
                f"UPDATE {_quote(table_name)} "
                f"SET {_quote(column_name)} = :value WHERE {condition}"
            ),
            {"value": value},
        )


def _add_many(specs: Iterable[tuple[str, str, str]], changes: list[str]) -> None:
    for table_name, column_name, sql_type in specs:
        if _add_column(table_name, column_name, sql_type):
            changes.append(f"{table_name}.{column_name}")


def upgrade_database() -> list[str]:
    """Apply all known upgrades and return the columns that were created."""
    changes: list[str] = []

    # Columns introduced across the V3 releases. The most important production
    # fix is users.role, required by login and authorization.
    _add_many(
        [
            ("users", "role", "VARCHAR(30)"),
            ("users", "active", "BOOLEAN"),
            ("clinics", "active", "BOOLEAN"),
            ("species", "active", "BOOLEAN"),
            ("species", "display_order", "INTEGER"),
            ("exam_groups", "display_order", "INTEGER"),
            ("exams", "deadline_hours", "INTEGER"),
            ("exams", "active", "BOOLEAN"),
            ("exams", "group_id", "INTEGER"),
            ("exam_profiles", "active", "BOOLEAN"),
            ("sample_types", "display_order", "INTEGER"),
            ("sample_types", "active", "BOOLEAN"),
            ("lab_requests", "priority", "VARCHAR(30)"),
            ("lab_requests", "status", "VARCHAR(50)"),
            ("lab_requests", "profiles_json", "TEXT"),
            ("lab_requests", "exams_json", "TEXT"),
            ("lab_requests", "samples_json", "TEXT"),
            ("lab_requests", "internal_notes", "TEXT"),
            ("lab_requests", "created_at", "TIMESTAMP"),
            ("lab_results", "method", "VARCHAR(180)"),
            ("lab_results", "observations", "TEXT"),
            ("lab_reports", "created_at", "TIMESTAMP"),
        ],
        changes,
    )

    # Safe defaults for records created before these fields existed.
    _backfill("users", "role", "requisitante")
    _backfill("users", "active", True)
    _backfill("clinics", "active", True)
    _backfill("species", "active", True)
    _backfill("species", "display_order", 999)
    _backfill("exam_groups", "display_order", 999)
    _backfill("exams", "deadline_hours", 24)
    _backfill("exams", "active", True)
    _backfill("exam_profiles", "active", True)
    _backfill("sample_types", "display_order", 999)
    _backfill("sample_types", "active", True)
    _backfill("lab_requests", "priority", "Rotina")
    _backfill("lab_requests", "status", "Requisição enviada")
    _backfill("lab_requests", "profiles_json", "[]")
    _backfill("lab_requests", "exams_json", "[]")
    _backfill("lab_requests", "samples_json", "[]")

    now = datetime.utcnow()
    _backfill("lab_requests", "created_at", now)
    _backfill("lab_reports", "created_at", now)

    # Preserve administrator access in databases created before the role field.
    if "users" in _table_names() and {"email", "role"}.issubset(_columns("users")):
        with db.engine.begin() as connection:
            connection.execute(
                text(
                    'UPDATE "users" SET "role" = :role '
                    'WHERE LOWER("email") = :email'
                ),
                {"role": "admin", "email": "admin@vidapet.com.br"},
            )

    return changes
