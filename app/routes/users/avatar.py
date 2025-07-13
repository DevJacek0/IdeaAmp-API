import os

from flask import Blueprint, request, jsonify, send_file, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.datastructures import FileStorage

from app.models.attachment import Attachment
from app.models.user import User
from app.routes.decorators.adminRequired import admin_required
from app.services.userService import UsersService
from app.services.attachmentService import AttachmentsService
from app.services import AuditLogsService

avatar_users_blueprint: Blueprint = Blueprint('avatar_users', __name__, url_prefix="/users")


@avatar_users_blueprint.route("/avatar", methods=["POST"])
@jwt_required()
def upload_avatar() -> tuple[Response, int]:
    """
    Przesyła nowy avatar użytkownika.

    Metoda: ``POST``\n
    Url zapytania: ``/users/avatar``

    Obsługuje żądania POST do przesyłania nowego avatara użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Wymagane dane:\n
    - ``avatar`` (plik): Plik avatara do przesłania.

    Zwraca:\n
    - ``200`` **OK**: Jeśli avatar został pomyślnie zaktualizowany, zwraca ID nowego avatara.\n
    - ``400`` **Bad Request**: Jeśli brakuje pliku w żądaniu lub plik jest nieprawidłowy.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    attachments_service: AttachmentsService = AttachmentsService()
    audit_logs_service: AuditLogsService = AuditLogsService()

    try:
        if 'avatar' not in request.files:
            return jsonify({"error": "Brak pliku w żądaniu"}), 400

        file: FileStorage = request.files['avatar']
        if file.filename == '':
            return jsonify({"error": "Nie wybrano pliku"}), 400

        user_id: int = int(get_jwt_identity())
        user: User = users_service.get(user_id)

        old_avatar_id: int = user.avatar_id
        if old_avatar_id:
            attachments_service.delete_file(old_avatar_id)

        attachment: Attachment = attachments_service.save_file(file)
        if not attachment:
            return jsonify({"error": "Nieprawidłowy format pliku"}), 400

        users_service.update(user_id, avatar_id=attachment.id)

        audit_logs_service.log_action(
            user_id=user_id,
            action="UPDATE_AVATAR",
            details={
                "old_avatar_id": old_avatar_id,
                "new_avatar_id": attachment.id,
                "file_path": attachment.path
            }
        )

        return jsonify({
            "message": "Avatar został zaktualizowany",
            "avatar_id": attachment.id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@avatar_users_blueprint.route("/avatar/<int:user_id>", methods=["POST"])
@jwt_required()
@admin_required
def admin_update_user_avatar(user_id) -> tuple[Response, int]:
    """
    Aktualizuje avatar dowolnego użytkownika.

    Metoda: ``POST``\n
    Url zapytania: ``/users/avatar/<user-id>``

    Obsługuje żądania POST do aktualizacji avatara użytkownika przez administratora. Użytkownik musi być uwierzytelniony za pomocą JWT i posiadać uprawnienia administratora.

    Parametry:\n
    - ``user_id`` (int): ID użytkownika, którego avatar ma zostać zaktualizowany.

    Wymagane dane:\n
    - ``avatar`` (plik): Plik avatara do przesłania.

    Zwraca:\n
    - ``200`` **OK**: Jeśli avatar został pomyślnie zaktualizowany, zwraca ID nowego avatara.\n
    - ``400`` **Bad Request**: Jeśli brakuje pliku w żądaniu, plik jest nieprawidłowy lub użytkownik nie istnieje.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie istnieje.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    attachments_service: AttachmentsService = AttachmentsService()
    audit_logs_service: AuditLogsService = AuditLogsService()

    try:
        if 'avatar' not in request.files:
            return jsonify({"error": "Brak pliku w żądaniu"}), 400

        file = request.files['avatar']
        if file.filename == '':
            return jsonify({"error": "Nie wybrano pliku"}), 400

        admin_id: int = int(get_jwt_identity())
        user: User = users_service.get(user_id)

        if not user:
            return jsonify({"error": "Użytkownik nie istnieje"}), 404

        old_avatar_id: int = user.avatar_id
        if old_avatar_id:
            attachments_service.delete_file(old_avatar_id)

        attachment: Attachment = attachments_service.save_file(file)
        if not attachment:
            return jsonify({"error": "Nieprawidłowy format pliku"}), 400

        users_service.update(user_id, avatar_id=attachment.id)

        audit_logs_service.log_action(
            user_id=admin_id,
            action="ADMIN_UPDATE_USER_AVATAR",
            details={
                "target_user_id": user_id,
                "old_avatar_id": old_avatar_id,
                "new_avatar_id": attachment.id,
                "file_path": attachment.path
            }
        )

        return jsonify({
            "message": f"Avatar użytkownika (ID: {user_id}) został zaktualizowany",
            "avatar_id": attachment.id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@avatar_users_blueprint.route("/avatar/<int:user_id>", methods=["GET"])
def get_avatar(user_id) -> tuple[Response, int]:
    """
    Pobiera avatar użytkownika.

    Metoda: ``GET``\n
    Url zapytania: ``/users/avatar/<user-id>``

    Obsługuje żądania GET do pobrania własnego avatara użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Zwraca:\n
    - ``200`` **OK**: Plik avatara.\n
    - ``404`` **Not Found**: Jeśli avatar lub plik avatara nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    attachments_service: AttachmentsService = AttachmentsService()

    try:
        user: User = users_service.get(user_id)
        if not user or not user.avatar_id:
            return jsonify({"error": "Avatar nie istnieje"}), 404

        attachment: Attachment = attachments_service.get(user.avatar_id)
        if not attachment:
            return jsonify({"error": "Plik avatara nie istnieje"}), 404

        full_path = attachments_service.get_file_path(
            os.path.join(attachments_service.UPLOAD_FOLDER, attachment.path.lstrip("/"))
        )

        if not os.path.exists(full_path):
            return jsonify({"error": "Plik avatara nie istnieje"}), 404

        return send_file(full_path), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@avatar_users_blueprint.route("/avatar/self", methods=["GET"])
@jwt_required()
def get_own_avatar() -> tuple[Response, int]:
    """
    Pobiera własny avatar użytkownika.

    Metoda: ``GET``\n
    Url zapytania: ``/users/avatar/self``

    Obsługuje żądania GET do pobrania własnego avatara użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Zwraca:\n
    - ``200`` **OK**: Plik avatara.\n
    - ``404`` **Not Found**: Jeśli avatar lub plik avatara nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    attachments_service: AttachmentsService = AttachmentsService()

    try:
        user_id: int = int(get_jwt_identity())
        user: User = users_service.get(user_id)

        if not user or not user.avatar_id:
            return jsonify({"error": "Avatar nie istnieje"}), 404

        attachment: Attachment = attachments_service.get(user.avatar_id)
        if not attachment:
            return jsonify({"error": "Plik avatara nie istnieje"}), 404

        full_path = attachments_service.get_file_path(
            os.path.join(attachments_service.UPLOAD_FOLDER, attachment.path.lstrip("/"))
        )

        if not os.path.exists(full_path):
            return jsonify({"error": "Plik avatara nie istnieje"}), 404

        return send_file(full_path), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
