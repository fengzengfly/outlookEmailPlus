from __future__ import annotations

from flask import Blueprint

from outlook_web.controllers import system as system_controller


def create_blueprint() -> Blueprint:
    """创建 system Blueprint"""
    bp = Blueprint("system", __name__)
    bp.add_url_rule("/healthz", view_func=system_controller.healthz, methods=["GET"])
    bp.add_url_rule(
        "/api/system/health",
        view_func=system_controller.api_system_health,
        methods=["GET"],
    )
    bp.add_url_rule(
        "/api/system/diagnostics",
        view_func=system_controller.api_system_diagnostics,
        methods=["GET"],
    )
    bp.add_url_rule(
        "/api/system/upgrade-status",
        view_func=system_controller.api_system_upgrade_status,
        methods=["GET"],
    )
    return bp
