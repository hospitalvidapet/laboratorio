def _normalize_boolean_column(
    table_name: str,
    column_name: str,
    changes: list[str],
) -> None:
    """Converte flags INTEGER antigas em BOOLEAN no PostgreSQL.

    A migração:
    1. remove o DEFAULT incompatível;
    2. converte os valores 0/1 para FALSE/TRUE;
    3. restaura DEFAULT TRUE;
    4. não altera SQLite.
    """
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

    if db.engine.dialect.name != "postgresql":
        return

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
        f"{table_name}.{column_name}: "
        "INTEGER→BOOLEAN, DEFAULT TRUE"
    )
