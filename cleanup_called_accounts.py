#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path


def resolve_db_path(explicit_path: str | None) -> Path:
    if explicit_path:
        return Path(explicit_path).expanduser().resolve()
    env_path = os.getenv("DATABASE_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    return Path("data/outlook_accounts.db").resolve()


def fetch_success_called_accounts(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT a.id, a.email, a.provider, a.account_type, a.pool_status,
               COUNT(l.id) AS success_complete_count
        FROM accounts a
        JOIN account_claim_logs l ON l.account_id = a.id
        WHERE l.action = 'complete' AND l.result = 'success'
        GROUP BY a.id, a.email, a.provider, a.account_type, a.pool_status
        ORDER BY a.id
        """
    ).fetchall()


def fetch_counts(conn: sqlite3.Connection) -> dict[str, int]:
    row = conn.execute(
        """
        SELECT
            (SELECT COUNT(*)
             FROM accounts a
             WHERE EXISTS (
                 SELECT 1
                 FROM account_claim_logs l
                 WHERE l.account_id = a.id
                   AND l.action = 'complete'
                   AND l.result = 'success'
             )) AS accounts_count,
            (SELECT COUNT(*)
             FROM account_claim_logs l
             WHERE EXISTS (
                 SELECT 1
                 FROM accounts a
                 WHERE a.id = l.account_id
                   AND EXISTS (
                       SELECT 1
                       FROM account_claim_logs s
                       WHERE s.account_id = a.id
                         AND s.action = 'complete'
                         AND s.result = 'success'
                   )
             )) AS claim_logs_count,
            (SELECT COUNT(*)
             FROM account_project_usage u
             WHERE EXISTS (
                 SELECT 1
                 FROM account_claim_logs l
                 WHERE l.account_id = u.account_id
                   AND l.action = 'complete'
                   AND l.result = 'success'
             )) AS usage_count
        """
    ).fetchone()
    return {
        "accounts_count": int(row[0] or 0),
        "claim_logs_count": int(row[1] or 0),
        "usage_count": int(row[2] or 0),
    }


def delete_called_accounts(conn: sqlite3.Connection) -> dict[str, int]:
    counts = fetch_counts(conn)
    conn.execute("BEGIN")
    try:
        conn.execute(
            """
            CREATE TEMP TABLE success_account_ids AS
            SELECT DISTINCT account_id
            FROM account_claim_logs
            WHERE action = 'complete'
              AND result = 'success'
              AND account_id IS NOT NULL
            """
        )
        conn.execute(
            """
            DELETE FROM account_project_usage
            WHERE account_id IN (SELECT account_id FROM success_account_ids)
            """
        )
        conn.execute(
            """
            DELETE FROM account_claim_logs
            WHERE account_id IN (SELECT account_id FROM success_account_ids)
            """
        )
        conn.execute(
            """
            DELETE FROM accounts
            WHERE id IN (SELECT account_id FROM success_account_ids)
            """
        )
        conn.execute("DROP TABLE success_account_ids")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return counts


def print_preview(rows: list[sqlite3.Row], counts: dict[str, int]) -> None:
    print(f"命中邮箱数: {counts['accounts_count']}")
    print(f"关联 claim 日志数: {counts['claim_logs_count']}")
    print(f"关联 usage 记录数: {counts['usage_count']}")
    print()
    if not rows:
        print("没有找到任何有 complete(success) 记录的邮箱。")
        return

    print("将删除以下邮箱：")
    for row in rows:
        print(
            f"- id={row['id']} email={row['email']} provider={row['provider'] or ''} "
            f"type={row['account_type'] or ''} pool_status={row['pool_status'] or ''} "
            f"success_completes={row['success_complete_count']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="删除所有有 complete(success) 记录的邮箱账号，以及相关 usage / claim log 数据。"
    )
    parser.add_argument(
        "--db",
        help="SQLite 数据库路径；默认取 DATABASE_PATH，否则使用 data/outlook_accounts.db",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="真正执行删除；默认仅预览",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="执行删除时跳过二次确认",
    )
    args = parser.parse_args()

    db_path = resolve_db_path(args.db)
    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}", file=sys.stderr)
        return 1

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = fetch_success_called_accounts(conn)
        counts = fetch_counts(conn)
        print(f"数据库: {db_path}")
        print_preview(rows, counts)

        if not args.apply:
            print()
            print("当前为预览模式；如需执行删除，请加 --apply")
            return 0

        if counts["accounts_count"] == 0:
            print()
            print("没有需要删除的数据。")
            return 0

        if not args.yes:
            print()
            answer = input("确认删除以上邮箱及关联记录？输入 yes 继续: ").strip()
            if answer != "yes":
                print("已取消。")
                return 0

        deleted = delete_called_accounts(conn)
        print()
        print("删除完成：")
        print(f"- 删除邮箱: {deleted['accounts_count']}")
        print(f"- 删除 claim 日志: {deleted['claim_logs_count']}")
        print(f"- 删除 usage 记录: {deleted['usage_count']}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
