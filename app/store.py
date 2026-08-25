from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class _DBRow(Mapping[str, Any]):
    """Small sqlite3.Row-compatible mapping for remote DB-API drivers."""

    def __init__(self, columns: list[str], values: tuple[Any, ...] | list[Any]):
        self._columns = columns
        self._values = tuple(values)
        self._index = {name: i for i, name in enumerate(columns)}

    def __getitem__(self, key: str | int) -> Any:
        if isinstance(key, int):
            return self._values[key]
        return self._values[self._index[key]]

    def __iter__(self) -> Iterator[str]:
        return iter(self._columns)

    def __len__(self) -> int:
        return len(self._columns)


class _CursorAdapter:
    def __init__(self, cursor: Any):
        self._cursor = cursor

    @property
    def rowcount(self) -> int:
        return int(getattr(self._cursor, "rowcount", -1) or 0)

    @property
    def lastrowid(self) -> int:
        return int(getattr(self._cursor, "lastrowid", 0) or 0)

    @property
    def description(self) -> Any:
        return getattr(self._cursor, "description", None)

    def _wrap(self, row: Any) -> Any:
        if row is None or isinstance(row, Mapping):
            return row
        desc = self.description or []
        columns = [str(item[0]) for item in desc]
        return _DBRow(columns, row) if columns else row

    def fetchone(self) -> Any:
        return self._wrap(self._cursor.fetchone())

    def fetchall(self) -> list[Any]:
        return [self._wrap(row) for row in self._cursor.fetchall()]

    def __iter__(self):
        for row in self._cursor:
            yield self._wrap(row)


class _RemoteConnectionAdapter:
    """Makes a standard DB-API connection behave like the sqlite3 surface used by Vezmora."""

    def __init__(self, connection: Any):
        self._connection = connection

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> _CursorAdapter:
        return _CursorAdapter(self._connection.execute(sql, params))

    def cursor(self) -> _CursorAdapter:
        return _CursorAdapter(self._connection.cursor())

    def executescript(self, script: str) -> None:
        method = getattr(self._connection, "executescript", None)
        if callable(method):
            method(script)
            return
        buffer = ""
        for line in script.splitlines(keepends=True):
            buffer += line
            if sqlite3.complete_statement(buffer):
                statement = buffer.strip()
                if statement:
                    self.execute(statement)
                buffer = ""
        if buffer.strip():
            self.execute(buffer)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        rollback = getattr(self._connection, "rollback", None)
        if callable(rollback):
            rollback()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            self.close()
        return False


def storage_backend() -> str:
    return "turso" if os.getenv("TURSO_DATABASE_URL") else "sqlite"


def _db_path() -> Path:
    configured = os.getenv("VEZMORA_DB_PATH")
    if configured:
        path = Path(configured).expanduser()
    else:
        data_dir = Path(os.getenv("VEZMORA_DATA_DIR", str(Path(__file__).resolve().parent.parent))).expanduser()
        path = data_dir / ".vezmora.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


DB_PATH = _db_path()


def _connect() -> Any:
    turso_url = os.getenv("TURSO_DATABASE_URL")
    if turso_url:
        try:
            import turso_serverless
        except ImportError as exc:
            raise RuntimeError("TURSO_DATABASE_URL is configured but turso_serverless is not installed") from exc
        connection = turso_serverless.connect(
            turso_url,
            auth_token=os.getenv("TURSO_AUTH_TOKEN") or None,
        )
        return _RemoteConnectionAdapter(connection)

    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def _insert_id(con: Any, sql: str, params: tuple[Any, ...] | list[Any]) -> int:
    """Return an inserted primary key without relying on remote lastrowid semantics."""
    statement = sql.rstrip().rstrip(";") + " RETURNING id"
    row = con.execute(statement, params).fetchone()
    if not row:
        raise RuntimeError("Insert did not return an id")
    return int(row["id"] if isinstance(row, Mapping) else row[0])


def init_db() -> None:
    with _connect() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS workspaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS workspace_members (
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                role TEXT NOT NULL DEFAULT 'owner',
                PRIMARY KEY(workspace_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS company_profiles (
                workspace_id INTEGER PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
                profile_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                kind TEXT NOT NULL,
                company_name TEXT NOT NULL,
                language TEXT NOT NULL,
                input_json TEXT NOT NULL,
                output_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS kpis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                metric_date TEXT NOT NULL,
                impressions INTEGER NOT NULL DEFAULT 0,
                clicks INTEGER NOT NULL DEFAULT 0,
                leads INTEGER NOT NULL DEFAULT 0,
                conversions INTEGER NOT NULL DEFAULT 0,
                spend_sek REAL NOT NULL DEFAULT 0,
                revenue_sek REAL NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_kpis_workspace_date ON kpis(workspace_id, metric_date);
            CREATE TABLE IF NOT EXISTS competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                url TEXT,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS competitor_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                competitor_id INTEGER NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
                content_hash TEXT NOT NULL,
                title TEXT,
                excerpt TEXT NOT NULL DEFAULT '',
                http_status INTEGER,
                changed INTEGER NOT NULL DEFAULT 0,
                checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_snapshots_competitor ON competitor_snapshots(competitor_id, id DESC);
            CREATE TABLE IF NOT EXISTS connectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                provider TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'disconnected',
                external_id TEXT,
                account_label TEXT,
                secret_blob TEXT,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(workspace_id, provider)
            );
            CREATE TABLE IF NOT EXISTS oauth_states (
                state TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                provider TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL DEFAULT '',
                is_read INTEGER NOT NULL DEFAULT 0,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_notifications_workspace ON notifications(workspace_id, id DESC);
            CREATE TABLE IF NOT EXISTS approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                action_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                provider TEXT,
                risk_level TEXT NOT NULL DEFAULT 'medium',
                payload_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'pending',
                review_note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_approvals_workspace ON approvals(workspace_id, status, id DESC);
            CREATE TABLE IF NOT EXISTS daily_brief_settings (
                workspace_id INTEGER PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
                enabled INTEGER NOT NULL DEFAULT 0,
                hour INTEGER NOT NULL DEFAULT 8,
                timezone TEXT NOT NULL DEFAULT 'Europe/Stockholm',
                last_run_date TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        columns = {row["name"] for row in con.execute("PRAGMA table_info(runs)").fetchall()}
        if "workspace_id" not in columns:
            con.execute("ALTER TABLE runs ADD COLUMN workspace_id INTEGER")
        if "user_id" not in columns:
            con.execute("ALTER TABLE runs ADD COLUMN user_id INTEGER")
        kpi_columns = {row["name"] for row in con.execute("PRAGMA table_info(kpis)").fetchall()}
        if "currency" not in kpi_columns:
            con.execute("ALTER TABLE kpis ADD COLUMN currency TEXT NOT NULL DEFAULT 'SEK'")
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS workspace_settings (
                workspace_id INTEGER PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
                base_currency TEXT NOT NULL DEFAULT 'SEK',
                plan TEXT NOT NULL DEFAULT 'starter',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS fx_rates (
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                quote_currency TEXT NOT NULL,
                rate_to_base REAL NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(workspace_id, quote_currency)
            );
            CREATE TABLE IF NOT EXISTS campaign_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                provider TEXT NOT NULL,
                external_campaign_id TEXT NOT NULL,
                campaign_name TEXT NOT NULL,
                metric_date TEXT NOT NULL,
                impressions INTEGER NOT NULL DEFAULT 0,
                clicks INTEGER NOT NULL DEFAULT 0,
                conversions REAL NOT NULL DEFAULT 0,
                spend REAL NOT NULL DEFAULT 0,
                revenue REAL NOT NULL DEFAULT 0,
                currency TEXT NOT NULL DEFAULT 'SEK',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(workspace_id, provider, external_campaign_id, metric_date)
            );
            CREATE INDEX IF NOT EXISTS idx_campaign_metrics_workspace_date ON campaign_metrics(workspace_id, metric_date DESC);
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                fingerprint TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                detected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(workspace_id, fingerprint)
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'queued',
                attempts INTEGER NOT NULL DEFAULT 0,
                run_after TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                locked_at TEXT,
                finished_at TEXT,
                result_json TEXT,
                error_text TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs(status, run_after, id);
            CREATE TABLE IF NOT EXISTS execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                approval_id INTEGER NOT NULL REFERENCES approvals(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                provider TEXT NOT NULL,
                action_type TEXT NOT NULL,
                request_json TEXT NOT NULL DEFAULT '{}',
                result_json TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS workspace_invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                email TEXT NOT NULL COLLATE NOCASE,
                role TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                invited_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                expires_at TEXT NOT NULL,
                accepted_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS usage_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                kind TEXT NOT NULL,
                units INTEGER NOT NULL DEFAULT 1,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_usage_workspace_created ON usage_events(workspace_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS onboarding_profiles (
                workspace_id INTEGER PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
                data_json TEXT NOT NULL DEFAULT '{}',
                completed_at TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS email_outbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
                recipient TEXT NOT NULL,
                subject TEXT NOT NULL,
                body_text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'queued',
                error_text TEXT,
                sent_at TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_email_outbox_status ON email_outbox(status, id);
            CREATE TABLE IF NOT EXISTS beta_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                score INTEGER NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS billing_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
                provider_event_id TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        ws_columns = {row["name"] for row in con.execute("PRAGMA table_info(workspace_settings)").fetchall()}
        additions = {
            "autopilot_mode": "TEXT NOT NULL DEFAULT 'suggest'",
            "autopilot_daily_spend_cap": "REAL NOT NULL DEFAULT 0",
            "autopilot_max_budget_change_pct": "REAL NOT NULL DEFAULT 15",
            "autopilot_allowed_actions_json": "TEXT NOT NULL DEFAULT '[]'",
            "stripe_customer_id": "TEXT",
            "stripe_subscription_id": "TEXT",
            "billing_status": "TEXT NOT NULL DEFAULT 'trialing'",
            "trial_ends_at": "TEXT",
        }
        for column, definition in additions.items():
            if column not in ws_columns:
                con.execute(f"ALTER TABLE workspace_settings ADD COLUMN {column} {definition}")


def create_user(email: str, password_salt: str, password_hash: str, workspace_name: str) -> tuple[int, int]:
    with _connect() as con:
        user_id = _insert_id(con, "INSERT INTO users(email, password_salt, password_hash) VALUES (?, ?, ?)", (email.strip().lower(), password_salt, password_hash))
        workspace_id = _insert_id(con, "INSERT INTO workspaces(owner_user_id, name) VALUES (?, ?)", (user_id, workspace_name))
        con.execute("INSERT INTO workspace_members(workspace_id, user_id, role) VALUES (?, ?, 'owner')", (workspace_id, user_id))
        return user_id, workspace_id


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with _connect() as con:
        row = con.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip(),)).fetchone()
    return dict(row) if row else None


def create_session(user_id: int, token_hash: str, expires_at: str) -> None:
    with _connect() as con:
        con.execute("INSERT INTO sessions(user_id, token_hash, expires_at) VALUES (?, ?, ?)", (user_id, token_hash, expires_at))


def revoke_session(token_hash: str) -> None:
    with _connect() as con:
        con.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))


def get_session_user(token_hash: str) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as con:
        row = con.execute("""SELECT u.id, u.email, s.expires_at FROM sessions s JOIN users u ON u.id=s.user_id
               WHERE s.token_hash=? AND s.expires_at>?""", (token_hash, now)).fetchone()
    return dict(row) if row else None


def list_workspaces(user_id: int) -> list[dict[str, Any]]:
    with _connect() as con:
        rows = con.execute("""SELECT w.id, w.name, wm.role, w.created_at FROM workspace_members wm
               JOIN workspaces w ON w.id=wm.workspace_id WHERE wm.user_id=? ORDER BY w.id""", (user_id,)).fetchall()
    return [dict(r) for r in rows]


def create_workspace(user_id: int, name: str) -> int:
    with _connect() as con:
        workspace_id = _insert_id(con, "INSERT INTO workspaces(owner_user_id,name) VALUES(?,?)", (user_id, name))
        con.execute("INSERT INTO workspace_members(workspace_id,user_id,role) VALUES(?,?,'owner')", (workspace_id, user_id))
        return workspace_id


def user_has_workspace(user_id: int, workspace_id: int) -> bool:
    with _connect() as con:
        row = con.execute("SELECT 1 FROM workspace_members WHERE user_id=? AND workspace_id=?", (user_id, workspace_id)).fetchone()
    return bool(row)


def save_company_profile(workspace_id: int, profile: dict[str, Any]) -> None:
    with _connect() as con:
        con.execute("""INSERT INTO company_profiles(workspace_id, profile_json, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(workspace_id) DO UPDATE SET profile_json=excluded.profile_json, updated_at=CURRENT_TIMESTAMP""", (workspace_id, json.dumps(profile, ensure_ascii=False)))


def get_company_profile(workspace_id: int) -> dict[str, Any] | None:
    with _connect() as con:
        row = con.execute("SELECT profile_json FROM company_profiles WHERE workspace_id=?", (workspace_id,)).fetchone()
    return json.loads(row["profile_json"]) if row else None


def save_run(kind: str, company_name: str, language: str, payload: dict[str, Any], output: str, workspace_id: int | None = None, user_id: int | None = None) -> int:
    with _connect() as con:
        return _insert_id(con, "INSERT INTO runs(workspace_id,user_id,kind,company_name,language,input_json,output_text) VALUES (?, ?, ?, ?, ?, ?, ?)", (workspace_id, user_id, kind, company_name, language, json.dumps(payload, ensure_ascii=False), output))


def recent_runs(limit: int = 10, workspace_id: int | None = None) -> list[dict[str, Any]]:
    with _connect() as con:
        if workspace_id is None:
            rows = con.execute("SELECT id,kind,company_name,language,output_text,created_at FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        else:
            rows = con.execute("SELECT id,kind,company_name,language,output_text,created_at FROM runs WHERE workspace_id=? ORDER BY id DESC LIMIT ?", (workspace_id, limit)).fetchall()
    return [dict(r) for r in rows]


def latest_run(workspace_id: int, kind: str) -> dict[str, Any] | None:
    with _connect() as con:
        row = con.execute("SELECT id,kind,company_name,language,output_text,created_at FROM runs WHERE workspace_id=? AND kind=? ORDER BY id DESC LIMIT 1", (workspace_id, kind)).fetchone()
    return dict(row) if row else None


def add_kpi(workspace_id: int, data: dict[str, Any]) -> int:
    with _connect() as con:
        return _insert_id(con, """INSERT INTO kpis(workspace_id,metric_date,impressions,clicks,leads,conversions,spend_sek,revenue_sek,source,currency)
               VALUES(?,?,?,?,?,?,?,?,?,?)""", (workspace_id, str(data["date"]), data["impressions"], data["clicks"], data["leads"], data["conversions"], data["spend_sek"], data["revenue_sek"], data["source"], data.get("currency","SEK").upper()))


def upsert_kpi(workspace_id: int, data: dict[str, Any]) -> int:
    metric_date = str(data["date"])
    source = str(data["source"])
    with _connect() as con:
        con.execute("DELETE FROM kpis WHERE workspace_id=? AND metric_date=? AND source=?", (workspace_id, metric_date, source))
        return _insert_id(con, """INSERT INTO kpis(workspace_id,metric_date,impressions,clicks,leads,conversions,spend_sek,revenue_sek,source,currency)
               VALUES(?,?,?,?,?,?,?,?,?,?)""", (workspace_id, metric_date, data.get("impressions", 0), data.get("clicks", 0), data.get("leads", 0), data.get("conversions", 0), data.get("spend_sek", 0), data.get("revenue_sek", 0), source, data.get("currency","SEK").upper()))


def list_kpis(workspace_id: int, limit: int = 90) -> list[dict[str, Any]]:
    with _connect() as con:
        rows = con.execute("SELECT * FROM kpis WHERE workspace_id=? ORDER BY metric_date DESC,id DESC LIMIT ?", (workspace_id, limit)).fetchall()
    return [dict(r) for r in rows]


def delete_kpi(workspace_id: int, kpi_id: int) -> None:
    with _connect() as con:
        con.execute("DELETE FROM kpis WHERE id=? AND workspace_id=?", (kpi_id, workspace_id))


def dashboard_summary(workspace_id: int) -> dict[str, Any]:
    rows = list_kpis(workspace_id, 3650)
    totals: dict[str, Any] = {"impressions": 0, "clicks": 0, "leads": 0, "conversions": 0, "spend_sek": 0.0, "revenue_sek": 0.0}
    for row in rows:
        for key in list(totals):
            totals[key] += row[key] or 0
    clicks, spend, revenue = totals["clicks"], totals["spend_sek"], totals["revenue_sek"]
    totals["ctr"] = (clicks / totals["impressions"] * 100) if totals["impressions"] else 0
    totals["cpc"] = (spend / clicks) if clicks else 0
    totals["roas"] = (revenue / spend) if spend else 0
    totals["cpl"] = (spend / totals["leads"]) if totals["leads"] else 0
    totals["rows"] = len(rows)
    return totals


def add_competitor(workspace_id: int, name: str, url: str | None, notes: str) -> int:
    with _connect() as con:
        return _insert_id(con, "INSERT INTO competitors(workspace_id,name,url,notes) VALUES(?,?,?,?)", (workspace_id, name, url, notes))


def list_competitors(workspace_id: int) -> list[dict[str, Any]]:
    with _connect() as con:
        rows = con.execute("""SELECT c.*, s.checked_at AS last_checked_at, s.changed AS last_changed, s.http_status AS last_http_status
               FROM competitors c LEFT JOIN competitor_snapshots s ON s.id=(
                 SELECT id FROM competitor_snapshots WHERE competitor_id=c.id ORDER BY id DESC LIMIT 1
               ) WHERE c.workspace_id=? ORDER BY c.id DESC""", (workspace_id,)).fetchall()
    return [dict(r) for r in rows]


def delete_competitor(workspace_id: int, competitor_id: int) -> None:
    with _connect() as con:
        con.execute("DELETE FROM competitors WHERE id=? AND workspace_id=?", (competitor_id, workspace_id))


def get_competitor(workspace_id: int, competitor_id: int) -> dict[str, Any] | None:
    with _connect() as con:
        row = con.execute("SELECT * FROM competitors WHERE id=? AND workspace_id=?", (competitor_id, workspace_id)).fetchone()
    return dict(row) if row else None


def latest_competitor_snapshot(competitor_id: int) -> dict[str, Any] | None:
    with _connect() as con:
        row = con.execute("SELECT * FROM competitor_snapshots WHERE competitor_id=? ORDER BY id DESC LIMIT 1", (competitor_id,)).fetchone()
    return dict(row) if row else None


def add_competitor_snapshot(workspace_id: int, competitor_id: int, content_hash: str, title: str | None, excerpt: str, http_status: int | None, changed: bool) -> int:
    with _connect() as con:
        return _insert_id(con, "INSERT INTO competitor_snapshots(workspace_id,competitor_id,content_hash,title,excerpt,http_status,changed) VALUES(?,?,?,?,?,?,?)", (workspace_id, competitor_id, content_hash, title, excerpt, http_status, int(changed)))


def recent_competitor_changes(workspace_id: int, limit: int = 20) -> list[dict[str, Any]]:
    with _connect() as con:
        rows = con.execute("""SELECT s.id,s.competitor_id,c.name,c.url,s.title,s.excerpt,s.http_status,s.checked_at
               FROM competitor_snapshots s JOIN competitors c ON c.id=s.competitor_id
               WHERE s.workspace_id=? AND s.changed=1 ORDER BY s.id DESC LIMIT ?""", (workspace_id, limit)).fetchall()
    return [dict(r) for r in rows]


def save_connector(workspace_id: int, provider: str, status: str, external_id: str | None, account_label: str | None, secret_blob: str | None, metadata: dict[str, Any]) -> None:
    with _connect() as con:
        con.execute("""INSERT INTO connectors(workspace_id,provider,status,external_id,account_label,secret_blob,metadata_json,updated_at)
               VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(workspace_id,provider) DO UPDATE SET
                 status=excluded.status, external_id=excluded.external_id, account_label=excluded.account_label,
                 secret_blob=COALESCE(excluded.secret_blob,connectors.secret_blob), metadata_json=excluded.metadata_json, updated_at=CURRENT_TIMESTAMP""", (workspace_id, provider, status, external_id, account_label, secret_blob, json.dumps(metadata)))


def get_connectors(workspace_id: int, include_secret: bool = False) -> list[dict[str, Any]]:
    fields = "provider,status,external_id,account_label,metadata_json,updated_at" + (",secret_blob" if include_secret else "")
    with _connect() as con:
        rows = con.execute(f"SELECT {fields} FROM connectors WHERE workspace_id=?", (workspace_id,)).fetchall()
    result = []
    for r in rows:
        item = dict(r)
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        result.append(item)
    return result


def get_connector(workspace_id: int, provider: str, include_secret: bool = False) -> dict[str, Any] | None:
    rows = get_connectors(workspace_id, include_secret=include_secret)
    return next((r for r in rows if r["provider"] == provider), None)


def update_connector_metadata(workspace_id: int, provider: str, updates: dict[str, Any]) -> None:
    current = get_connector(workspace_id, provider, include_secret=True)
    if not current:
        save_connector(workspace_id, provider, "disconnected", None, None, None, updates)
        return
    metadata = dict(current.get("metadata") or {})
    metadata.update({k: v for k, v in updates.items() if v not in (None, "")})
    save_connector(workspace_id, provider, current["status"], current.get("external_id"), current.get("account_label"), current.get("secret_blob"), metadata)


def save_oauth_state(state: str, user_id: int, workspace_id: int, provider: str) -> None:
    with _connect() as con:
        con.execute("INSERT INTO oauth_states(state,user_id,workspace_id,provider) VALUES(?,?,?,?)", (state, user_id, workspace_id, provider))


def consume_oauth_state(state: str, provider: str) -> dict[str, Any] | None:
    with _connect() as con:
        row = con.execute("SELECT * FROM oauth_states WHERE state=? AND provider=? AND created_at >= datetime('now','-20 minutes')", (state, provider)).fetchone()
        con.execute("DELETE FROM oauth_states WHERE state=?", (state,))
    return dict(row) if row else None


def add_notification(workspace_id: int, kind: str, title: str, body: str = "", metadata: dict[str, Any] | None = None) -> int:
    with _connect() as con:
        return _insert_id(con, "INSERT INTO notifications(workspace_id,kind,title,body,metadata_json) VALUES(?,?,?,?,?)", (workspace_id, kind, title, body, json.dumps(metadata or {}, ensure_ascii=False)))


def list_notifications(workspace_id: int, limit: int = 50, unread_only: bool = False) -> list[dict[str, Any]]:
    sql = "SELECT * FROM notifications WHERE workspace_id=?"
    params: list[Any] = [workspace_id]
    if unread_only:
        sql += " AND is_read=0"
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with _connect() as con:
        rows = con.execute(sql, tuple(params)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
        result.append(item)
    return result


def mark_notification_read(workspace_id: int, notification_id: int) -> None:
    with _connect() as con:
        con.execute("UPDATE notifications SET is_read=1 WHERE id=? AND workspace_id=?", (notification_id, workspace_id))


def create_approval(workspace_id: int, created_by: int | None, action_type: str, title: str, description: str, provider: str | None, risk_level: str, payload: dict[str, Any] | None = None) -> int:
    with _connect() as con:
        return _insert_id(con, """INSERT INTO approvals(workspace_id,created_by,action_type,title,description,provider,risk_level,payload_json)
               VALUES(?,?,?,?,?,?,?,?)""", (workspace_id, created_by, action_type, title, description, provider, risk_level, json.dumps(payload or {}, ensure_ascii=False)))


def list_approvals(workspace_id: int, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    sql = "SELECT * FROM approvals WHERE workspace_id=?"
    params: list[Any] = [workspace_id]
    if status:
        sql += " AND status=?"
        params.append(status)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with _connect() as con:
        rows = con.execute(sql, tuple(params)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item.pop("payload_json") or "{}")
        result.append(item)
    return result


def decide_approval(workspace_id: int, approval_id: int, reviewed_by: int, status: str, note: str = "") -> bool:
    if status not in {"approved", "rejected"}:
        raise ValueError("Invalid approval status")
    with _connect() as con:
        cur = con.execute("""UPDATE approvals SET status=?, reviewed_by=?, review_note=?, reviewed_at=CURRENT_TIMESTAMP
               WHERE id=? AND workspace_id=? AND status='pending'""", (status, reviewed_by, note, approval_id, workspace_id))
        return cur.rowcount > 0


def get_daily_brief_settings(workspace_id: int) -> dict[str, Any]:
    with _connect() as con:
        row = con.execute("SELECT * FROM daily_brief_settings WHERE workspace_id=?", (workspace_id,)).fetchone()
    if not row:
        return {"workspace_id": workspace_id, "enabled": 0, "hour": 8, "timezone": "Europe/Stockholm", "last_run_date": None}
    return dict(row)


def save_daily_brief_settings(workspace_id: int, enabled: bool, hour: int, timezone_name: str) -> None:
    with _connect() as con:
        con.execute("""INSERT INTO daily_brief_settings(workspace_id,enabled,hour,timezone,updated_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(workspace_id) DO UPDATE SET enabled=excluded.enabled,hour=excluded.hour,timezone=excluded.timezone,updated_at=CURRENT_TIMESTAMP""", (workspace_id, int(enabled), hour, timezone_name))


def mark_daily_brief_run(workspace_id: int, run_date: str) -> None:
    with _connect() as con:
        con.execute("UPDATE daily_brief_settings SET last_run_date=?,updated_at=CURRENT_TIMESTAMP WHERE workspace_id=?", (run_date, workspace_id))


def list_enabled_brief_settings() -> list[dict[str, Any]]:
    with _connect() as con:
        rows = con.execute("SELECT * FROM daily_brief_settings WHERE enabled=1").fetchall()
    return [dict(r) for r in rows]


def get_workspace_role(user_id: int, workspace_id: int) -> str | None:
    with _connect() as con:
        row = con.execute("SELECT role FROM workspace_members WHERE workspace_id=? AND user_id=?", (workspace_id, user_id)).fetchone()
    return str(row["role"]) if row else None


def list_workspace_members(workspace_id: int) -> list[dict[str, Any]]:
    with _connect() as con:
        rows = con.execute("""SELECT u.id,u.email,wm.role,wm.workspace_id
               FROM workspace_members wm JOIN users u ON u.id=wm.user_id
               WHERE wm.workspace_id=?
               ORDER BY CASE wm.role WHEN 'owner' THEN 0 WHEN 'admin' THEN 1 WHEN 'marketer' THEN 2 ELSE 3 END, u.email""", (workspace_id,)).fetchall()
    return [dict(r) for r in rows]


def add_workspace_member(workspace_id: int, user_id: int, role: str) -> None:
    with _connect() as con:
        con.execute("INSERT OR REPLACE INTO workspace_members(workspace_id,user_id,role) VALUES(?,?,?)", (workspace_id,user_id,role))


def create_workspace_invite(workspace_id: int, email: str, role: str, token_hash: str, invited_by: int, expires_at: str) -> int:
    with _connect() as con:
        return _insert_id(con, "INSERT INTO workspace_invites(workspace_id,email,role,token_hash,invited_by,expires_at) VALUES(?,?,?,?,?,?)", (workspace_id,email.lower().strip(),role,token_hash,invited_by,expires_at))


def consume_workspace_invite(token_hash: str, email: str) -> dict[str, Any] | None:
    now=datetime.now(timezone.utc).isoformat()
    with _connect() as con:
        row=con.execute("SELECT * FROM workspace_invites WHERE token_hash=? AND email=? COLLATE NOCASE AND accepted_at IS NULL AND expires_at>?", (token_hash,email.strip(),now)).fetchone()
        if not row:
            return None
        con.execute("UPDATE workspace_invites SET accepted_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
        return dict(row)


def get_workspace_settings(workspace_id: int) -> dict[str, Any]:
    with _connect() as con:
        con.execute("INSERT OR IGNORE INTO workspace_settings(workspace_id) VALUES(?)", (workspace_id,))
        row=con.execute("SELECT * FROM workspace_settings WHERE workspace_id=?", (workspace_id,)).fetchone()
    return dict(row)


def save_workspace_settings(workspace_id: int, base_currency: str) -> None:
    currency=base_currency.upper()
    with _connect() as con:
        con.execute("INSERT INTO workspace_settings(workspace_id,base_currency) VALUES(?,?) ON CONFLICT(workspace_id) DO UPDATE SET base_currency=excluded.base_currency,updated_at=CURRENT_TIMESTAMP", (workspace_id,currency))


def set_workspace_plan(workspace_id: int, plan: str) -> None:
    with _connect() as con:
        con.execute("INSERT INTO workspace_settings(workspace_id,plan) VALUES(?,?) ON CONFLICT(workspace_id) DO UPDATE SET plan=excluded.plan,updated_at=CURRENT_TIMESTAMP", (workspace_id,plan))


def upsert_fx_rate(workspace_id: int, quote_currency: str, rate_to_base: float) -> None:
    with _connect() as con:
        con.execute("INSERT INTO fx_rates(workspace_id,quote_currency,rate_to_base) VALUES(?,?,?) ON CONFLICT(workspace_id,quote_currency) DO UPDATE SET rate_to_base=excluded.rate_to_base,updated_at=CURRENT_TIMESTAMP", (workspace_id,quote_currency.upper(),rate_to_base))


def list_fx_rates(workspace_id: int) -> list[dict[str, Any]]:
    with _connect() as con:
        rows=con.execute("SELECT * FROM fx_rates WHERE workspace_id=? ORDER BY quote_currency", (workspace_id,)).fetchall()
    return [dict(r) for r in rows]


def get_fx_rate(workspace_id: int, quote_currency: str) -> float | None:
    base=get_workspace_settings(workspace_id)["base_currency"]
    q=quote_currency.upper()
    if q==base:
        return 1.0
    with _connect() as con:
        row=con.execute("SELECT rate_to_base FROM fx_rates WHERE workspace_id=? AND quote_currency=?", (workspace_id,q)).fetchone()
    return float(row["rate_to_base"]) if row else None


def upsert_campaign_metric(workspace_id: int, data: dict[str, Any]) -> int:
    with _connect() as con:
        con.execute("""INSERT INTO campaign_metrics(workspace_id,provider,external_campaign_id,campaign_name,metric_date,impressions,clicks,conversions,spend,revenue,currency)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(workspace_id,provider,external_campaign_id,metric_date) DO UPDATE SET
               campaign_name=excluded.campaign_name,impressions=excluded.impressions,clicks=excluded.clicks,
               conversions=excluded.conversions,spend=excluded.spend,revenue=excluded.revenue,currency=excluded.currency,created_at=CURRENT_TIMESTAMP""", (workspace_id,data["provider"],str(data["external_campaign_id"]),data.get("campaign_name") or str(data["external_campaign_id"]),data["date"],int(data.get("impressions",0)),int(data.get("clicks",0)),float(data.get("conversions",0)),float(data.get("spend",0)),float(data.get("revenue",0)),data.get("currency","SEK").upper()))
        row=con.execute("SELECT id FROM campaign_metrics WHERE workspace_id=? AND provider=? AND external_campaign_id=? AND metric_date=?", (workspace_id,data["provider"],str(data["external_campaign_id"]),data["date"])).fetchone()
        return int(row["id"])


def list_campaign_metrics(workspace_id: int, limit: int = 300) -> list[dict[str, Any]]:
    with _connect() as con:
        rows=con.execute("SELECT * FROM campaign_metrics WHERE workspace_id=? ORDER BY metric_date DESC,id DESC LIMIT ?", (workspace_id,limit)).fetchall()
    return [dict(r) for r in rows]


def campaign_summary(workspace_id: int, days: int = 30) -> list[dict[str, Any]]:
    with _connect() as con:
        rows=con.execute("""SELECT provider,external_campaign_id,campaign_name,currency,SUM(impressions) impressions,SUM(clicks) clicks,SUM(conversions) conversions,SUM(spend) spend,SUM(revenue) revenue
               FROM campaign_metrics WHERE workspace_id=? AND metric_date>=date('now', ?)
               GROUP BY provider,external_campaign_id,campaign_name,currency ORDER BY spend DESC""", (workspace_id,f'-{max(days-1,0)} day')).fetchall()
    result=[]
    for r in rows:
        d=dict(r)
        d["ctr"]=(100*d["clicks"]/d["impressions"]) if d["impressions"] else 0
        d["roas"]=(d["revenue"]/d["spend"]) if d["spend"] else 0
        result.append(d)
    return result


def save_anomaly(workspace_id: int, fingerprint: str, severity: str, title: str, body: str, metadata: dict[str, Any]) -> bool:
    with _connect() as con:
        cur=con.execute("INSERT OR IGNORE INTO anomalies(workspace_id,fingerprint,severity,title,body,metadata_json) VALUES(?,?,?,?,?,?)", (workspace_id,fingerprint,severity,title,body,json.dumps(metadata)))
        return cur.rowcount>0


def list_anomalies(workspace_id: int, limit: int=50) -> list[dict[str, Any]]:
    with _connect() as con:
        rows=con.execute("SELECT * FROM anomalies WHERE workspace_id=? ORDER BY id DESC LIMIT ?", (workspace_id,limit)).fetchall()
    out=[]
    for r in rows:
        d=dict(r); d["metadata"]=json.loads(d.pop("metadata_json") or "{}"); out.append(d)
    return out


def enqueue_job(workspace_id: int, kind: str, payload: dict[str, Any] | None=None, run_after: str | None=None) -> int:
    with _connect() as con:
        return _insert_id(con, "INSERT INTO jobs(workspace_id,kind,payload_json,run_after) VALUES(?,?,?,COALESCE(?,CURRENT_TIMESTAMP))", (workspace_id,kind,json.dumps(payload or {}),run_after))


def claim_job() -> dict[str, Any] | None:
    with _connect() as con:
        con.execute("BEGIN IMMEDIATE")
        row=con.execute("SELECT * FROM jobs WHERE status='queued' AND datetime(run_after)<=CURRENT_TIMESTAMP ORDER BY id LIMIT 1").fetchone()
        if not row:
            return None
        con.execute("UPDATE jobs SET status='running',locked_at=CURRENT_TIMESTAMP,attempts=attempts+1 WHERE id=? AND status='queued'", (row["id"],))
        got=con.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone()
    d=dict(got); d["payload"]=json.loads(d.pop("payload_json") or "{}"); return d


def finish_job(job_id: int, result: dict[str, Any]) -> None:
    with _connect() as con:
        con.execute("UPDATE jobs SET status='done',finished_at=CURRENT_TIMESTAMP,result_json=?,error_text=NULL WHERE id=?", (json.dumps(result),job_id))


def fail_job(job_id: int, error: str, retry: bool=False) -> None:
    with _connect() as con:
        if retry:
            con.execute("UPDATE jobs SET status='queued',run_after=datetime('now','+5 minutes'),locked_at=NULL,error_text=? WHERE id=?", (error[:1000],job_id))
        else:
            con.execute("UPDATE jobs SET status='failed',finished_at=CURRENT_TIMESTAMP,error_text=? WHERE id=?", (error[:1000],job_id))


def list_jobs(workspace_id: int, limit: int=50) -> list[dict[str, Any]]:
    with _connect() as con:
        rows=con.execute("SELECT * FROM jobs WHERE workspace_id=? ORDER BY id DESC LIMIT ?", (workspace_id,limit)).fetchall()
    out=[]
    for r in rows:
        d=dict(r); d["payload"]=json.loads(d.pop("payload_json") or "{}"); d["result"]=json.loads(d.pop("result_json") or "null") if d.get("result_json") else None; out.append(d)
    return out


def get_approval(workspace_id: int, approval_id: int) -> dict[str, Any] | None:
    with _connect() as con:
        row=con.execute("SELECT * FROM approvals WHERE workspace_id=? AND id=?", (workspace_id,approval_id)).fetchone()
    if not row:
        return None
    d=dict(row); d["payload"]=json.loads(d.pop("payload_json") or "{}"); return d


def set_approval_execution_status(workspace_id: int, approval_id: int, status: str) -> None:
    with _connect() as con:
        con.execute("UPDATE approvals SET status=? WHERE workspace_id=? AND id=?", (status,workspace_id,approval_id))


def log_execution(workspace_id: int, approval_id: int, user_id: int | None, provider: str, action_type: str, request: dict[str, Any], result: dict[str, Any], status: str) -> int:
    with _connect() as con:
        return _insert_id(con, "INSERT INTO execution_log(workspace_id,approval_id,user_id,provider,action_type,request_json,result_json,status) VALUES(?,?,?,?,?,?,?,?)", (workspace_id,approval_id,user_id,provider,action_type,json.dumps(request),json.dumps(result),status))


def list_executions(workspace_id: int, limit: int=50) -> list[dict[str, Any]]:
    with _connect() as con:
        rows=con.execute("SELECT * FROM execution_log WHERE workspace_id=? ORDER BY id DESC LIMIT ?", (workspace_id,limit)).fetchall()
    out=[]
    for r in rows:
        d=dict(r); d["request"]=json.loads(d.pop("request_json") or "{}"); d["result"]=json.loads(d.pop("result_json") or "{}"); out.append(d)
    return out


def record_usage(workspace_id: int, kind: str, units: int=1, metadata: dict[str, Any] | None=None) -> None:
    with _connect() as con:
        con.execute("INSERT INTO usage_events(workspace_id,kind,units,metadata_json) VALUES(?,?,?,?)", (workspace_id,kind,units,json.dumps(metadata or {})))


def usage_summary(workspace_id: int) -> dict[str, int]:
    with _connect() as con:
        rows=con.execute("SELECT kind,SUM(units) units FROM usage_events WHERE workspace_id=? AND created_at>=datetime('now','start of month') GROUP BY kind", (workspace_id,)).fetchall()
    return {r["kind"]: int(r["units"] or 0) for r in rows}


def get_onboarding_profile(workspace_id: int) -> dict[str, Any]:
    with _connect() as con:
        row = con.execute("SELECT * FROM onboarding_profiles WHERE workspace_id=?", (workspace_id,)).fetchone()
    if not row:
        return {"workspace_id": workspace_id, "data": {}, "completed": False, "completed_at": None}
    data = dict(row)
    return {"workspace_id": workspace_id,"data": json.loads(data.get("data_json") or "{}"),"completed": bool(data.get("completed_at")),"completed_at": data.get("completed_at"),"updated_at": data.get("updated_at")}


def save_onboarding_profile(workspace_id: int, data: dict[str, Any], complete: bool = False) -> None:
    completed_at = datetime.now(timezone.utc).isoformat() if complete else None
    with _connect() as con:
        existing = con.execute("SELECT completed_at FROM onboarding_profiles WHERE workspace_id=?", (workspace_id,)).fetchone()
        if existing and existing["completed_at"]:
            completed_at = existing["completed_at"]
        con.execute("""INSERT INTO onboarding_profiles(workspace_id,data_json,completed_at,updated_at)
               VALUES(?,?,?,CURRENT_TIMESTAMP)
               ON CONFLICT(workspace_id) DO UPDATE SET
                 data_json=excluded.data_json,
                 completed_at=COALESCE(onboarding_profiles.completed_at, excluded.completed_at),
                 updated_at=CURRENT_TIMESTAMP""", (workspace_id, json.dumps(data, ensure_ascii=False), completed_at))


def save_autopilot_settings(workspace_id: int, mode: str, daily_spend_cap: float, max_budget_change_pct: float, allowed_actions: list[str]) -> None:
    with _connect() as con:
        con.execute("""INSERT INTO workspace_settings(workspace_id,autopilot_mode,autopilot_daily_spend_cap,autopilot_max_budget_change_pct,autopilot_allowed_actions_json)
               VALUES(?,?,?,?,?)
               ON CONFLICT(workspace_id) DO UPDATE SET
                 autopilot_mode=excluded.autopilot_mode,
                 autopilot_daily_spend_cap=excluded.autopilot_daily_spend_cap,
                 autopilot_max_budget_change_pct=excluded.autopilot_max_budget_change_pct,
                 autopilot_allowed_actions_json=excluded.autopilot_allowed_actions_json,
                 updated_at=CURRENT_TIMESTAMP""", (workspace_id, mode, daily_spend_cap, max_budget_change_pct, json.dumps(allowed_actions)))


def get_autopilot_settings(workspace_id: int) -> dict[str, Any]:
    settings = get_workspace_settings(workspace_id)
    raw = settings.get("autopilot_allowed_actions_json") or "[]"
    try:
        allowed = json.loads(raw)
    except json.JSONDecodeError:
        allowed = []
    return {"mode": settings.get("autopilot_mode") or "suggest","daily_spend_cap": float(settings.get("autopilot_daily_spend_cap") or 0),"max_budget_change_pct": float(settings.get("autopilot_max_budget_change_pct") or 15),"allowed_actions": allowed}


def set_workspace_billing(workspace_id: int, *, plan: str | None = None, customer_id: str | None = None, subscription_id: str | None = None, billing_status: str | None = None, trial_ends_at: str | None = None) -> None:
    current = get_workspace_settings(workspace_id)
    with _connect() as con:
        con.execute("""INSERT INTO workspace_settings(workspace_id,plan,stripe_customer_id,stripe_subscription_id,billing_status,trial_ends_at)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(workspace_id) DO UPDATE SET
                 plan=excluded.plan,
                 stripe_customer_id=excluded.stripe_customer_id,
                 stripe_subscription_id=excluded.stripe_subscription_id,
                 billing_status=excluded.billing_status,
                 trial_ends_at=excluded.trial_ends_at,
                 updated_at=CURRENT_TIMESTAMP""", (workspace_id,plan or current.get("plan") or "starter",customer_id if customer_id is not None else current.get("stripe_customer_id"),subscription_id if subscription_id is not None else current.get("stripe_subscription_id"),billing_status if billing_status is not None else current.get("billing_status") or "trialing",trial_ends_at if trial_ends_at is not None else current.get("trial_ends_at")))


def workspace_id_by_stripe_customer(customer_id: str) -> int | None:
    with _connect() as con:
        row = con.execute("SELECT workspace_id FROM workspace_settings WHERE stripe_customer_id=?", (customer_id,)).fetchone()
    return int(row["workspace_id"]) if row else None


def record_billing_event(workspace_id: int | None, provider_event_id: str, event_type: str, payload: dict[str, Any]) -> bool:
    with _connect() as con:
        cur = con.execute("INSERT OR IGNORE INTO billing_events(workspace_id,provider_event_id,event_type,payload_json) VALUES(?,?,?,?)", (workspace_id, provider_event_id, event_type, json.dumps(payload)))
        return cur.rowcount > 0


def create_password_reset(user_id: int, token_hash: str, expires_at: str) -> int:
    with _connect() as con:
        con.execute("UPDATE password_reset_tokens SET used_at=CURRENT_TIMESTAMP WHERE user_id=? AND used_at IS NULL", (user_id,))
        return _insert_id(con, "INSERT INTO password_reset_tokens(user_id,token_hash,expires_at) VALUES(?,?,?)", (user_id, token_hash, expires_at))


def consume_password_reset(token_hash: str) -> int | None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as con:
        row = con.execute("SELECT * FROM password_reset_tokens WHERE token_hash=? AND used_at IS NULL AND expires_at>?", (token_hash, now)).fetchone()
        if not row:
            return None
        con.execute("UPDATE password_reset_tokens SET used_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
        return int(row["user_id"])


def update_user_password(user_id: int, password_salt: str, password_hash: str) -> None:
    with _connect() as con:
        con.execute("UPDATE users SET password_salt=?,password_hash=? WHERE id=?", (password_salt, password_hash, user_id))
        con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))


def queue_email(workspace_id: int | None, recipient: str, subject: str, body_text: str) -> int:
    with _connect() as con:
        return _insert_id(con, "INSERT INTO email_outbox(workspace_id,recipient,subject,body_text) VALUES(?,?,?,?)", (workspace_id, recipient.strip().lower(), subject, body_text))


def claim_email() -> dict[str, Any] | None:
    with _connect() as con:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute("SELECT * FROM email_outbox WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
        if not row:
            return None
        con.execute("UPDATE email_outbox SET status='sending' WHERE id=? AND status='queued'", (row["id"],))
        got = con.execute("SELECT * FROM email_outbox WHERE id=?", (row["id"],)).fetchone()
    return dict(got) if got else None


def finish_email(email_id: int, error: str | None = None) -> None:
    with _connect() as con:
        if error:
            con.execute("UPDATE email_outbox SET status='failed',error_text=? WHERE id=?", (error[:1000], email_id))
        else:
            con.execute("UPDATE email_outbox SET status='sent',sent_at=CURRENT_TIMESTAMP,error_text=NULL WHERE id=?", (email_id,))


def add_beta_feedback(workspace_id: int, user_id: int | None, score: int, category: str, message: str) -> int:
    with _connect() as con:
        return _insert_id(con, "INSERT INTO beta_feedback(workspace_id,user_id,score,category,message) VALUES(?,?,?,?,?)", (workspace_id, user_id, score, category, message))


def list_beta_feedback(workspace_id: int, limit: int = 100) -> list[dict[str, Any]]:
    with _connect() as con:
        rows = con.execute("SELECT * FROM beta_feedback WHERE workspace_id=? ORDER BY id DESC LIMIT ?", (workspace_id, limit)).fetchall()
    return [dict(r) for r in rows]


def workspace_daily_execution_spend(workspace_id: int) -> float:
    total = 0.0
    with _connect() as con:
        rows = con.execute("SELECT request_json FROM execution_log WHERE workspace_id=? AND status='executed' AND created_at>=datetime('now','start of day')", (workspace_id,)).fetchall()
    for row in rows:
        try:
            payload = json.loads(row["request_json"] or "{}")
        except json.JSONDecodeError:
            continue
        for key in ("daily_budget", "budget", "amount"):
            if key in payload:
                try:
                    total += max(0.0, float(payload[key]))
                except (TypeError, ValueError):
                    pass
                break
    return total


def list_autopilot_workspaces() -> list[int]:
    with _connect() as con:
        rows = con.execute("SELECT workspace_id FROM workspace_settings WHERE autopilot_mode='autopilot'").fetchall()
    return [int(r["workspace_id"]) for r in rows]
