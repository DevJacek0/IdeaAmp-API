import json
from typing import Any

from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.auditLog import AuditLog
from app.models.user import User
from app.routes.decorators.adminRequired import admin_required
from app.routes.decorators.pagination import paginate
from app.services.userService import UsersService
from app.services.auditLogService import AuditLogsService

login_history_blueprint: Blueprint = Blueprint("login_history", __name__, url_prefix="/users")


@login_history_blueprint.route("/login-history", methods=["GET"])
@jwt_required()
@paginate
def get_own_login_history() -> list[dict[str, Any]] | tuple[Response, int]:
    """
    Pobiera historię logowań zalogowanego użytkownika.

    Metoda: ``GET``\n
    Url zapytania: ``/users/login-history``

    Obsługuje żądania GET do pobrania historii logowań zalogowanego użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Zwraca:\n
    - ``200`` **OK**: Lista historii logowań w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    user_id: int = int(get_jwt_identity())
    audit_logs: AuditLogsService = AuditLogsService()
    
    try:
        logs: list[AuditLog] = audit_logs.get_login_history(user_id)
        return [format_login_entry(log) for log in logs]
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@login_history_blueprint.route("/login-history/<int:user_id>", methods=["GET"])
@jwt_required()
@admin_required
@paginate
def get_user_login_history(user_id) -> list[dict[str, Any]] | tuple[Response, int]:
    """
    Pobiera historię logowań użytkownika na podstawie ID.

    Metoda: ``GET``\n
    Url zapytania: ``/users/login-history/<user-id>``

    Obsługuje żądania GET do pobrania historii logowań użytkownika na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT i posiadać uprawnienia administratora.

    Parametry:\n
    - ``user_id`` (int): ID użytkownika, którego historia logowań ma zostać pobrana.

    Zwraca:\n
    - ``200`` **OK**: Lista historii logowań w formacie JSON.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    try:
        user: User = users_service.get(user_id)

        if not user:
            return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

        audit_logs: AuditLogsService  = AuditLogsService()
        logs: list[AuditLog] = audit_logs.get_login_history(user_id)

        return [{
            **format_login_entry(log),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        } for log in logs]
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@login_history_blueprint.route("/login-history/get-all", methods=["GET"])
@jwt_required()
@admin_required
@paginate
def get_all_login_history() -> list[dict[str, Any]] | tuple[Response, int]:
    """
    Pobiera historię logowań wszystkich użytkowników.

    Metoda: ``GET``\n
    Url zapytania: ``/users/login-history/get-all``

    Obsługuje żądania GET do pobrania historii logowań wszystkich użytkowników. Użytkownik musi być uwierzytelniony za pomocą JWT i posiadać uprawnienia administratora.

    Zwraca:\n
    - ``200`` **OK**: Lista historii logowań w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    audit_logs: AuditLogsService = AuditLogsService()
    users_service: UsersService = UsersService()
    
    try:
        logs: list[AuditLog] = audit_logs.get_login_history()

        user_details: dict[int, dict[str, int | str]] = {}
        for log in logs:
            if log.user_id not in user_details:
                user: User = users_service.get(log.user_id)
                if user:
                    user_details[log.user_id] = {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name
                    }

        return [{
            **format_login_entry(log),
            "user": user_details.get(log.user_id, {
                "id": log.user_id,
                "email": "Unknown",
                "first_name": "Unknown",
                "last_name": "Unknown"
            })
        } for log in logs]
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def format_login_entry(log: AuditLog) -> dict[str, int | str | None]:
    """
    Formatuje dane logowania.

    Formatuje dane logowania do formatu JSON.

    Parametry:\n
    - ``log`` (AuditLog): Obiekt logowania do sformatowania.

    Zwraca:\n
    - **dict[str, int | str | None]**: Sformatowane dane logowania.
    """

    details: str | dict = log.details or {}

    if isinstance(details, str):
        try:
            details = json.loads(details)
        except json.JSONDecodeError:
            details = {}

    return {
        "id": log.id,
        "user_id": log.user_id,
        "timestamp": log.created_on,
        "ip_address": details.get("ip_address"),
        "user_agent": details.get("user_agent"),
        "action": log.action
    }