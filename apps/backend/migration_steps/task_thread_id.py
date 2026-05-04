from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.engine import Connection


def _table_columns(conn: Connection, table_name: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return {str(row[1]) for row in rows}


def _table_indexes(conn: Connection, table_name: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA index_list({table_name})")).fetchall()
    return {str(row[1]) for row in rows}


def _has_thread_id_uniqueness(conn: Connection) -> bool:
    indexes = conn.execute(text("PRAGMA index_list(check_in_tasks)")).fetchall()
    for row in indexes:
        is_unique = bool(row[2])
        if not is_unique:
            continue
        index_name = str(row[1])
        columns = conn.execute(text(f"PRAGMA index_info({index_name})")).fetchall()
        column_names = [str(column[2]) for column in columns]
        if column_names == ["user_id", "thread_id"]:
            return True
    return False


def _extract_thread_id(payload_config: str | None) -> str | None:
    if not payload_config:
        return None
    try:
        payload = json.loads(payload_config)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    thread_id = payload.get("ThreadId")
    value = str(thread_id).strip() if thread_id is not None else ""
    return value or None


def apply(conn: Connection) -> None:
    columns = _table_columns(conn, "check_in_tasks")

    if "thread_id" not in columns:
        conn.execute(text("ALTER TABLE check_in_tasks ADD COLUMN thread_id VARCHAR(100)"))
        conn.commit()

    full_rows = conn.execute(
        text("SELECT id, user_id, payload_config FROM check_in_tasks")
    ).fetchall()
    invalid_ids: list[int] = []
    seen: dict[tuple[int, str], int] = {}
    duplicate_ids: list[int] = []

    for row in full_rows:
        thread_id = _extract_thread_id(row.payload_config)
        if not thread_id:
            invalid_ids.append(row.id)
            continue
        key = (row.user_id, thread_id)
        if key in seen:
            duplicate_ids.append(row.id)
        else:
            seen[key] = row.id

    if invalid_ids or duplicate_ids:
        messages = []
        if invalid_ids:
            messages.append(f"payload_config 缺少有效 ThreadId 的任务: {invalid_ids}")
        if duplicate_ids:
            messages.append(f"同用户 ThreadId 重复的任务: {duplicate_ids}")
        raise RuntimeError("；".join(messages))

    rows = conn.execute(text("SELECT id, payload_config FROM check_in_tasks")).fetchall()
    for row in rows:
        thread_id = _extract_thread_id(row.payload_config)
        if thread_id:
            conn.execute(
                text("UPDATE check_in_tasks SET thread_id = :thread_id WHERE id = :id"),
                {"thread_id": thread_id, "id": row.id},
            )
    conn.commit()

    indexes = _table_indexes(conn, "check_in_tasks")
    if "ix_task_user_thread_id_unique" not in indexes and not _has_thread_id_uniqueness(conn):
        conn.execute(
            text(
                "CREATE UNIQUE INDEX ix_task_user_thread_id_unique "
                "ON check_in_tasks (user_id, thread_id)"
            )
        )
        conn.commit()
