"""Vexmera PostgreSQL DB-API compatibility shim.

When TURSO_DATABASE_URL contains a PostgreSQL URL, this module exposes the
small DB-API surface expected by app.store while translating Vexmera's legacy
SQLite SQL dialect to PostgreSQL.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime
from typing import Any


def _sql(sql: str) -> str:
    statement = sql.strip()
    if statement.upper() == "BEGIN IMMEDIATE":
        return "BEGIN"

    statement = statement.replace("datetime('now','-20 minutes')", "CURRENT_TIMESTAMP - INTERVAL '20 minutes'")
    statement = statement.replace("datetime('now','+5 minutes')", "CURRENT_TIMESTAMP + INTERVAL '5 minutes'")
    statement = statement.replace("datetime('now','start of month')", "date_trunc('month', CURRENT_TIMESTAMP)")
    statement = statement.replace("datetime('now','start of day')", "date_trunc('day', CURRENT_TIMESTAMP)")
    statement = statement.replace("datetime(run_after)", "run_after")
    statement = statement.replace(" COLLATE NOCASE", "")

    replace_member = statement.upper().startswith("INSERT OR REPLACE INTO WORKSPACE_MEMBERS")
    ignore_insert = statement.upper().startswith("INSERT OR IGNORE INTO ")
    if replace_member:
        statement = re.sub(r"(?i)^INSERT\s+OR\s+REPLACE\s+INTO", "INSERT INTO", statement, count=1)
    elif ignore_insert:
        statement = re.sub(r"(?i)^INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", statement, count=1)

    statement = statement.replace("date('now', ?)", "(CURRENT_DATE + CAST(? AS interval))")
    statement = statement.replace("?", "%s")

    if replace_member:
        statement += " ON CONFLICT(workspace_id,user_id) DO UPDATE SET role=EXCLUDED.role"
    elif ignore_insert:
        statement += " ON CONFLICT DO NOTHING"
    return statement


def _value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


class Cursor:
    def __init__(self, cursor: Any):
        self._cursor = cursor

    @property
    def rowcount(self) -> int:
        return int(self._cursor.rowcount or 0)

    @property
    def description(self):
        desc = self._cursor.description
        if not desc:
            return None
        return [(getattr(col, "name", None) or col[0], None, None, None, None, None, None) for col in desc]

    def fetchone(self):
        row = self._cursor.fetchone()
        return None if row is None else tuple(_value(v) for v in row)

    def fetchall(self):
        return [tuple(_value(v) for v in row) for row in self._cursor.fetchall()]

    def __iter__(self):
        for row in self._cursor:
            yield tuple(_value(v) for v in row)


class Connection:
    def __init__(self, connection: Any, integrity_error: type[Exception]):
        self._connection = connection
        self._integrity_error = integrity_error

    def execute(self, sql: str, params=()):
        try:
            return Cursor(self._connection.execute(_sql(sql), params))
        except self._integrity_error as exc:
            raise sqlite3.IntegrityError(str(exc)) from exc

    def cursor(self):
        return Cursor(self._connection.cursor())

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


def connect(url: str, auth_token: str | None = None):
    if not url.startswith(("postgresql://", "postgres://")):
        raise RuntimeError("This Vexmera deployment expects a PostgreSQL DATABASE_URL")
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("PostgreSQL support requires psycopg") from exc
    connection = psycopg.connect(url)
    return Connection(connection, psycopg.IntegrityError)
