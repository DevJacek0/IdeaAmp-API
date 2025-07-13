from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Message

from app.models.user import User
from app.services import AuditLogsService
from app.services.userService import UsersService
import random
from app import mail

password_users_blueprint: Blueprint = Blueprint('password_users', __name__, url_prefix="/users")


@password_users_blueprint.route("/change-password", methods=["PATCH"])
@jwt_required()
def change_password() -> tuple[Response, int]:
    """
    Zmienia hasło użytkownika.

    Metoda: ``PATCH``\n
    Url zapytania: ``/users/change-password``

    Obsługuje żądania PATCH do zmiany hasła użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Wymagane dane:\n
    - ``id`` (int, w parametrze zapytania): ID użytkownika, którego hasło ma zostać zmienione.\n
    - ``old_password`` (str, w ciele zapytania): Stare hasło użytkownika (wymagane, jeśli użytkownik zmienia własne hasło).\n
    - ``new_password`` (str, w ciele zapytania): Nowe hasło użytkownika.

    Zwraca:\n
    - ``200`` **OK**: Jeśli hasło zostało pomyślnie zmienione.\n
    - ``400`` **Bad Request**: Jeśli brakuje wymaganych danych lub stare hasło jest nieprawidłowe.\n
    - ``403`` **Forbidden**: Jeśli użytkownik nie ma uprawnień do zmiany hasła.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    current_user_id: int = int(get_jwt_identity())
    audit_logs_service: AuditLogsService = AuditLogsService()

    user_id : int= request.args.get("id", type=int)
    if not user_id:
        return jsonify({"error": "ID użytkownika jest wymagane"}), 400

    user: User = users_service.get(current_user_id)
    if not user:
        return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

    if user_id != current_user_id and user.role != "admin":
        return jsonify({"error": "Brak uprawnień"}), 403

    request_data = request.get_json()
    if not isinstance(request_data, dict) or "new_password" not in request_data:
        return jsonify({"error": "Nowe hasło jest wymagane"}), 400

    if user_id == current_user_id:
        if "old_password" not in request_data:
            return jsonify({"error": "Stare hasło jest wymagane"}), 400
        if not check_password_hash(user.password, request_data["old_password"]):
            return jsonify({"error": "Stare hasło jest nieprawidłowe"}), 400

    new_hashed_password: str = generate_password_hash(request_data["new_password"])
    success: bool = users_service.change_password(user_id, new_hashed_password)

    if not success:
        return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

    audit_logs_service.log_action(
        user_id=current_user_id,
        action="CHANGE_PASSWORD",
        details={"user_id": user_id}
    )
    return jsonify({"message": "Hasło zostało zmienione pomyślnie"}), 200


@password_users_blueprint.route("/request-reset", methods=["POST"])
def request_password_reset() -> tuple[Response, int]:
    """
    Wysyła kod resetu hasła na adres e-mail użytkownika.

    Metoda: ``POST``\n
    Url zapytania: ``/users/request-reset``

    Obsługuje żądania POST do wysłania kodu resetu hasła na adres e-mail użytkownika.

    Wymagane dane:\n
    - ``email`` (str, w ciele zapytania): Adres e-mail użytkownika.

    Zwraca:\n
    - ``200`` **OK**: Jeśli kod resetu hasła został pomyślnie wysłany.\n
    - ``400`` **Bad Request**: Jeśli brakuje adresu e-mail.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    audit_logs_service: AuditLogsService = AuditLogsService()
    request_data = request.get_json()
    email: str = request_data.get("email")

    if not request_data or not email or email is None:
        return jsonify({"error": "Adres e-mail jest wymagany"}), 400

    user: User = next((u for u in users_service.get_all() if str(u.email) == str(email)), None)
    if not user:
        return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

    reset_code: int = random.randint(10000, 99999)
    users_service.set_reset_code(user.email, reset_code)

    msg: Message = Message("Kod resetu hasła", recipients=[user.email])
    msg.body = f"Twój kod do resetu hasła to: {reset_code}"
    mail.send(msg)

    audit_logs_service.log_action(
        user_id=user.id,
        action="REQUEST_PASSWORD_RESET",
        details={"email": user.email, "reset_code": reset_code}
    )

    return jsonify({"message": "Kod resetu hasła został wysłany na adres e-mail"}), 200


@password_users_blueprint.route("/confirm-reset", methods=["POST"])
def confirm_password_reset() -> tuple[Response, int]:
    """
    Resetuje hasło użytkownika na podstawie kodu resetu.

    Metoda: ``POST``\n
    Url zapytania: ``/users/confirm-reset``

    Obsługuje żądania POST do resetowania hasła użytkownika na podstawie kodu resetu.

    Wymagane dane:\n
    - ``email`` (str, w ciele zapytania): Adres e-mail użytkownika.\n
    - ``code`` (str, w ciele zapytania): Kod resetu hasła.\n
    - ``new_password`` (str, w ciele zapytania): Nowe hasło użytkownika.

    Zwraca:\n
    - ``200`` **OK**: Jeśli hasło zostało pomyślnie zresetowane.\n
    - ``400`` **Bad Request**: Jeśli brakuje wymaganych danych lub kod resetu jest nieprawidłowy.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    audit_logs_service: AuditLogsService = AuditLogsService()

    request_data = request.get_json()
    email: str = request_data["email"]
    code: str = request_data["code"]
    new_password: str = request_data["new_password"]

    if not(request_data and email and code and new_password) or any(v is None for v in [email, code, new_password]):
        return jsonify({"error": "Adres e-mail, kod i nowe hasło są wymagane"}), 400

    stored_code = users_service.get_reset_code(email)

    if not stored_code:
        return jsonify({"error": "Nieprawidłowy lub wygasły kod resetu"}), 400

    if str(stored_code) != str(code):
        return jsonify({"error": "Nieprawidłowy kod resetu"}), 400

    user: User = users_service.get_by_email(email)
    if not user:
        return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

    success: bool = users_service.change_password(user.id, str(new_password))

    if not success:
        return jsonify({"error": "Nie udało się  zresetować hasła"}), 500

    users_service.delete_reset_code(email)
    audit_logs_service.log_action(
        user_id=user.id,
        action="RESET_PASSWORD",
        details={"email": email}
    )

    return jsonify({"message": f"Hasło zostało pomyślnie zresetowane"}), 200
