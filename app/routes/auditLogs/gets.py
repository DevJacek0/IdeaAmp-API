from typing import Any

from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.auditLog import AuditLog
from app.routes.decorators.pagination import paginate
from app.services import UsersService
from app.services.auditLogService import AuditLogsService

gets_logs_blueprint: Blueprint = Blueprint("gets_logs", __name__, url_prefix="/logs")


@gets_logs_blueprint.route("/get-all", methods=["GET"])
@jwt_required()
@paginate
def get_logs() -> tuple[Response, int] | list[dict[str, Any]] | list[dict[str, Any]]:
    """
    Pobiera logi audytowe.

    Metoda: ``GET``\n
    Url zapytania: ``/logs/get-all``

    Obsługuje żądania GET do pobierania logów audytowych. Użytkownik musi być
    uwierzytelniony za pomocą JWT. Administratorzy mogą przeglądać wszystkie logi, podczas gdy
    zwykli użytkownicy mogą przeglądać tylko swoje logi.

    Parametry zapytania:\n
    - ``id`` (int): ID logu do pobrania.\n
    - ``action`` (str): Filtruje logi po akcji.\n
    - ``user_id`` (int): Filtruje logi po ID użytkownika.

    Zwraca:\n
    - ``JSON``: Lista logów lub pojedynczy log w formacie JSON.\n
    - ``403`` **Forbidden**: Jeśli użytkownik nie ma dostępu do żądanych logów.\n
    - ``404`` **Not Found**: Jeśli log o podanym ID nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    audit_logs_service: AuditLogsService = AuditLogsService()
    users_service: UsersService = UsersService()

    user_id: int = int(get_jwt_identity())
    is_admin: bool = users_service.get(user_id).role == 'admin'

    log_id: int = request.args.get('id', type=int)
    action: str = request.args.get('action', type=str)
    target_user_id: int = request.args.get('user_id', type=int)

    try:
        if log_id:
            log: AuditLog = audit_logs_service.get(log_id)
            if not log:
                return jsonify({"error": "Log nie został znaleziony"}), 404
            if not is_admin and log.user_id != user_id:
                return jsonify({"error": "Brak dostępu do tego logu"}), 403

            return [{
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "details": log.details,
                "created_on": log.created_on
            }]

        if action:
            logs: list[AuditLog] = audit_logs_service.get_by_action(action)
        elif target_user_id:
            if not is_admin and target_user_id != user_id:
                return jsonify({"error": "Brak dostępu do logów tego użytkownika"}), 403

            logs: list[AuditLog] = audit_logs_service.get_by_user(target_user_id)
        else:
            logs: list[AuditLog] = audit_logs_service.get_all() if is_admin else audit_logs_service.get_by_user(user_id)

        if not is_admin:
            logs = [log for log in logs if log.user_id == user_id]

        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "details": log.details,
                "created_on": log.created_on
            }
            for log in logs
        ]

    except Exception as e:
        return jsonify({"error": str(e)}), 500