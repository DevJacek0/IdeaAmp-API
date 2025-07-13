from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mail import Message
import random

from app.models.user import User
from app.services import AuditLogsService
from app.services.userService import UsersService
from app import mail

two_factor_users_blueprint: Blueprint = Blueprint('two_factor_users', __name__, url_prefix="/users")


@two_factor_users_blueprint.route("/two-factor", methods=["POST"])
@jwt_required()
def toggle_two_factor() -> tuple[Response, int]:
    """
    Włącza lub wyłącza weryfikację dwuetapową.

    Metoda: ``POST``\n
    Url zapytania: ``/users/two-factor``

    Obsługuje żądania POST do włączenia lub wyłączenia weryfikacji dwuetapowej. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Wymagane dane:\n
    - ``enable`` (bool): Czy włączyć weryfikację dwuetapową.

    Zwraca:\n
    - ``200`` **OK**: Jeśli operacja zakończyła się sukcesem.\n
    - ``400`` **Bad Request**: Jeśli brakuje wymaganych danych lub weryfikacja dwuetapowa jest już w żądanym stanie.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    audit_logs_service: AuditLogsService = AuditLogsService()
    current_user_id: int = int(get_jwt_identity())

    user: User = users_service.get(current_user_id)
    if not user:
        return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

    request_data = request.get_json()
    enable: str = request_data.get("enable")

    if enable is None:
        return jsonify({"error": "Parametr 'enable' jest wymagany"}), 400

    if enable == user.two_factor_enabled:
        status: str = "włączona" if enable else "wyłączona"
        return jsonify({"message": f"Weryfikacja dwuetapowa jest już {status}"}), 400

    if enable:
        verification_code: int = random.randint(100000, 999999)
        users_service.set_2fa_code(user.email, verification_code)

        msg: Message = Message("Kod weryfikacyjny 2FA", recipients=[user.email])
        msg.body = f"Twój kod weryfikacyjny do włączenia 2FA to: {verification_code}"
        mail.send(msg)

        return jsonify({
            "message": "Kod weryfikacyjny został wysłany na Twój adres email",
            "requires_verification": True
        }), 200
    else:
        users_service.update(current_user_id, two_factor_enabled=False)
        audit_logs_service.log_action(
            user_id=current_user_id,
            action="DISABLE_2FA",
            details={"user_id": current_user_id}
        )
        return jsonify({"message": "Weryfikacja dwuetapowa została wyłączona"}), 200


@two_factor_users_blueprint.route("/two-factor/verify", methods=["POST"])
@jwt_required()
def verify_two_factor() -> tuple[Response, int]:
    """
    Weryfikuje kod weryfikacyjny 2FA.

    Metoda: ``POST``\n
    Url zapytania: ``/users/two-factor/verify``

    Obsługuje żądania POST do weryfikacji kodu weryfikacyjnego 2FA. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Wymagane dane:\n
    - ``code`` (str): Kod weryfikacyjny 2FA.

    Zwraca:\n
    - ``200`` **OK**: Jeśli kod weryfikacyjny jest poprawny i weryfikacja dwuetapowa została włączona.\n
    - ``400`` **Bad Request**: Jeśli brakuje kodu weryfikacyjnego lub jest on nieprawidłowy.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    audit_logs_service: AuditLogsService = AuditLogsService()
    current_user_id: int = int(get_jwt_identity())

    user: User = users_service.get(current_user_id)
    if not user:
        return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

    request_data = request.get_json()
    code: str = request_data.get("code")

    if not code:
        return jsonify({"error": "Kod weryfikacyjny jest wymagany"}), 400

    stored_code: str = users_service.get_2fa_code(user.email)
    if not stored_code:
        return jsonify({"error": "Kod weryfikacyjny wygasł lub jest nieprawidłowy"}), 400

    if str(stored_code) != str(code):
        return jsonify({"error": "Nieprawidłowy kod weryfikacyjny"}), 400

    users_service.update(current_user_id, two_factor_enabled=True)
    users_service.delete_2fa_code(user.email)

    audit_logs_service.log_action(
        user_id=current_user_id,
        action="ENABLE_2FA",
        details={"user_id": current_user_id}
    )

    return jsonify({"message": "Weryfikacja dwuetapowa została włączona"}), 200
