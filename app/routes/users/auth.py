from datetime import datetime, timezone, timedelta
import random

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from werkzeug.security import check_password_hash
from flask_mail import Message

from app.models.user import User
from app.services.userService import UsersService
from app.services.auditLogService import AuditLogsService
from app import mail

auth_user_blueprint: Blueprint = Blueprint('auth_users', __name__, url_prefix="/users")


@auth_user_blueprint.route("/auth", methods=["POST"])
def authenticate() -> tuple[Response, int]:
    """
    Uwierzytelnia użytkownika.

    Metoda: ``POST``\n
    Url zapytania: ``/users/auth``

    Obsługuje żądania POST do uwierzytelniania użytkownika. Wymaga podania adresu email i hasła. Jeśli użytkownik ma włączone uwierzytelnianie dwuskładnikowe, wymaga również kodu weryfikacyjnego.

    Wymagane dane:\n
    - ``email`` (str): Adres email użytkownika.\n
    - ``password`` (str): Hasło użytkownika.\n
    - ``verification_code`` (str | int, opcjonalnie): Kod weryfikacyjny dwuskładnikowy.

    Zwraca:\n
    - ``200`` **OK**: Jeśli uwierzytelnianie się powiedzie, zwraca token dostępu i token odświeżający.\n
    - ``400`` **Bad Request**: Jeśli brakuje danych uwierzytelniających.\n
    - ``401`` **Unauthorized**: Jeśli dane uwierzytelniające są nieprawidłowe lub kod weryfikacyjny jest nieprawidłowy.
    """

    users_service: UsersService = UsersService()
    audit_logs: AuditLogsService = AuditLogsService()
    data = request.get_json()
    email: str = data.get("email")
    password: str = data.get("password")
    verification_code: str | int = data.get("verification_code")

    if not email or not password:
        return jsonify({"error": "Brak danych uwierzytelniających"}), 400

    user: User = users_service.authenticate(email, password)
    if not user:
        potential_user: User = users_service.get_by_email(email)
        if potential_user:
            audit_logs.log_login(
                user_id=potential_user.id,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
                success=False
            )
        return jsonify({"error": "Nieprawidłowe dane uwierzytelniające"}), 401

    if user.two_factor_enabled:
        if not verification_code:
            verification_code = random.randint(100000, 999999)
            users_service.set_2fa_code(user.email, verification_code)

            msg: Message = Message("Kod weryfikacyjny logowania", recipients=[user.email])
            msg.body = f"Twój kod weryfikacyjny do logowania to: {verification_code}"
            mail.send(msg)

            return jsonify({
                "requires_2fa": True,
                "message": "Kod weryfikacyjny został wysłany na Twój adres email"
            }), 200
        else:
            if not users_service.verify_2fa(user.email, verification_code):
                audit_logs.log_login(
                    user_id=user.id,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string,
                    success=False
                )
                return jsonify({"error": "Nieprawidłowy kod weryfikacyjny"}), 401
            users_service.delete_2fa_code(user.email)

    token: str = create_access_token(identity=str(user.id))

    audit_logs.log_login(
        user_id=user.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
        success=True
    )

    return jsonify({
        "token": token
    }), 200


@auth_user_blueprint.route("/validate-token", methods=["GET"])
@jwt_required()
def validate_token() -> tuple[Response, int]:
    """
    Waliduje token dostępu.

    Metoda: ``GET``\n
    Url zapytania: ``/users/validate-token``

    Obsługuje żądania GET do walidacji tokenu dostępu. Użytkownik musi być uwierzytelniony za pomocą tokenu dostępu.

    Zwraca:\n
    - ``200`` **OK**: Jeśli token jest ważny, zwraca informacje o ważności tokenu i ID użytkownika.\n
    """

    jwt = get_jwt()
    now: datetime = datetime.now(timezone.utc)
    expiration: datetime = datetime.fromtimestamp(jwt["exp"], timezone.utc)
    time_left: timedelta = expiration - now

    return jsonify({
        "valid": True,
        "expires_in": int(time_left.total_seconds()),
        "user_id": get_jwt_identity()
    }), 200
