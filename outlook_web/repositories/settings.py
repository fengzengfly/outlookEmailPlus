from __future__ import annotations

from typing import Dict

from outlook_web import config
from outlook_web.db import get_db


def get_setting(key: str, default: str = "") -> str:
    """获取设置值"""
    db = get_db()
    cursor = db.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> bool:
    """设置值"""
    db = get_db()
    try:
        db.execute(
            """
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (key, value),
        )
        db.commit()
        return True
    except Exception:
        return False


def get_all_settings() -> Dict[str, str]:
    """获取所有设置"""
    db = get_db()
    cursor = db.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    return {row["key"]: row["value"] for row in rows}


def get_login_password() -> str:
    """获取登录密码（优先从数据库读取）"""
    password = get_setting("login_password")
    return password if password else config.get_login_password_default()


def get_gptmail_api_key() -> str:
    """获取 GPTMail API Key（优先从数据库读取）"""
    api_key = get_setting("gptmail_api_key")
    return api_key if api_key else config.get_gptmail_api_key_default()
