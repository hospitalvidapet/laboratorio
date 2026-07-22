"""Idempotent database upgrades for installations created by older releases.

The project does not yet use Alembic. This module performs conservative
schema upgrades, creates missing columns, normalizes legacy PostgreSQL data
types and backfills safe defaults without deleting existing records.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import Boolean, Integer, inspect, text

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

    return {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


def _add_column(
    table_name: str,
    column_name: str,
    sql_type: str,
) -> bool:
    """Add a nullable column if it is absent."""
    if table_name not in _table_names():
        return False

    if column_name in _columns(table_name):
        return False

    statement = (
        f"ALTER TABLE {_quote(table_name)} "
        f"ADD COLUMN {_quote(column_name)} {sql_type}"
    )

    with db.engine.begin() as connection:
        connection.execute(text(statement))

    return True


def _backfill(
    table_name: str,
    column_name: str,
    value,
    where_sql: str | None = None,
) -> None:
    """Fill missing values without overwriting existing information."""
    if table_name not in _table_names():
        return

    if column_name not in _columns(table_name):
        return

    condition = (
        where_sql
        or f"{_quote(column_name)} IS NULL"
    )

    statement = (
        f"UPDATE {_quote(table_name)} "
        f"SET {_quote(column_name)} = :value "
        f"WHERE {condition}"
    )

    with db.engine.begin() as connection:
        connection.execute(
            text(statement),
            {"value": value},
        )


def _normalize_boolean_column(
    table_name: str,
    column_name: str,
    changes: list[str],
) -> None:
    """Convert legacy PostgreSQL INTEGER flags to BOOLEAN."""
    if db.engine.dialect.name != "postgresql":
        return

    if table_name not in _table_names():
        return

    if column_name not in _columns(table_name):
        return

    inspector = inspect(db.engine)

    column = next(
        (
            item
            for item in inspector.get_columns(table_name)
            if item["name"] == column_name
        ),
        None,
    )

    if not column:
        return

    column_type = column.get("type")

    is_legacy_integer = (
        isinstance(column_type, Integer)
        and not isinstance(column_type, Boolean)
    )

    if not is_legacy_integer:
        return

    table = _quote(table_name)
    field = _quote(column_name)

    drop_default_sql = f"""
        ALTER TABLE {table}
        ALTER COLUMN {field} DROP DEFAULT
    """

    convert_type_sql = f"""
        ALTER TABLE {table}
        ALTER COLUMN {field} TYPE BOOLEAN
        USING (
            CASE
                WHEN {field} IS NULL THEN NULL
                WHEN {field} = 0 THEN FALSE
                ELSE TRUE
            END
        )
    """

    set_default_sql = f"""
        ALTER TABLE {table}
        ALTER COLUMN {field} SET DEFAULT TRUE
    """

    with db.engine.begin() as connection:
        connection.execute(text(drop_default_sql))
        connection.execute(text(convert_type_sql))
        connection.execute(text(set_default_sql))

    changes.append(
        f"{table_name}.{column_name}: INTEGER→BOOLEAN, DEFAULT TRUE"
    )


def _add_many(
    specs: Iterable[tuple[str, str, str]],
    changes: list[str],
) -> None:
    for table_name, column_name, sql_type in specs:
        if _add_column(
            table_name,
            column_name,
            sql_type,
        ):
            changes.append(
                f"{table_name}.{column_name}"
            )


def upgrade_database() -> list[str]:
    """Apply all known database upgrades."""
    changes: list[str] = []

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

    for table_name, column_name in [
        ("users", "active"),
        ("clinics", "active"),
        ("species", "active"),
        ("exams", "active"),
        ("exam_profiles", "active"),
        ("sample_types", "active"),
    ]:
        _normalize_boolean_column(
            table_name,
            column_name,
            changes,
        )

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
    _backfill(
        "lab_requests",
        "status",
        "Requisição enviada",
    )
    _backfill("lab_requests", "profiles_json", "[]")
    _backfill("lab_requests", "exams_json", "[]")
    _backfill("lab_requests", "samples_json", "[]")

    now = datetime.utcnow()

    _backfill("lab_requests", "created_at", now)
    _backfill("lab_reports", "created_at", now)

    if (
        "users" in _table_names()
        and {"email", "role"}.issubset(_columns("users"))
    ):
        with db.engine.begin() as connection:
            connection.execute(
                text(
                    'UPDATE "users" '
                    'SET "role" = :role '
                    'WHERE LOWER("email") = :email'
                ),
                {
                    "role": "admin",
                    "email": "admin@vidapet.com.br",
                },
            )

    return changes
