from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.services import AuditLogsService
from app.services.userService import UsersService

delete_users_blueprint: Blueprint = Blueprint('delete_users', __name__, url_prefix="/users")


@delete_users_blueprint.route('/delete/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id) -> tuple[Response, int]:
    """
    Usuwa użytkownika.

    Metoda: ``DELETE``\n
    Url zapytania: ``/users/delete/<user-id>``

    Obsługuje żądania DELETE do usunięcia użytkownika na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``user_id`` (int): ID użytkownika do usunięcia.

    Zwraca:\n
    - ``200`` **OK**: Jeśli użytkownik został pomyślnie usunięty.\n
    - ``403`` **Forbidden**: Jeśli użytkownik nie ma uprawnień do usunięcia tego użytkownika.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    audit_logs_service: AuditLogsService = AuditLogsService()

    try:
        current_user_id: int = int(get_jwt_identity())
        current_user: User = users_service.get(current_user_id)

        if not current_user:
            return jsonify({"error": "Użytkownik nie znaleziony"}), 404

        user_to_delete: User = users_service.get(user_id)
        if not user_to_delete:
            return jsonify({"error": "Użytkownik do usunęcia nie znaleziony"}), 404

        if current_user.role == "admin":
            users_service.delete(user_id)
            audit_logs_service.log_action(
                user_id=current_user.id,
                action="DELETE_USER",
                details={"deleted_user_id": user_id, "by_role": "admin"}
            )
            return jsonify({"message": "Użytkownik został usunięty"}), 200
        elif current_user.role == "client":
            if current_user.id != user_id:
                return jsonify({"error": "Brak permisji do usunięcia tego użytkownika"}), 403
            users_service.delete(user_id)

            audit_logs_service.log_action(
                user_id=current_user.id,
                action="DELETE_USER",
                details={"deleted_user_id": user_id, "by_role": "client"}
            )
            return jsonify({"message": "Użytkownik został usunięty"}), 200
        else:
            return jsonify({"error": "Brak permisji"}), 403

    except Exception as e:
        return jsonify({"error": str(e)}), 500
