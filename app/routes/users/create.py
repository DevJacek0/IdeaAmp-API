from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import create_access_token, create_refresh_token

from app.models.user import User
from app.services import AuditLogsService
from app.services.userService import UsersService

create_users_blueprint: Blueprint = Blueprint("create_users", __name__, url_prefix="/users")


@create_users_blueprint.route("/create", methods=["POST"])
def create_user() -> tuple[Response, int]:
    """
    Tworzy nowego użytkownika.

    Metoda: ``POST``\n
    Url zapytania: ``/users/create``

    Obsługuje żądania POST do tworzenia nowego użytkownika. Wymaga podania imienia, nazwiska, adresu email i hasła.

    Wymagane dane:\n
    - ``first_name`` (str): Imię użytkownika.\n
    - ``last_name`` (str): Nazwisko użytkownika.\n
    - ``email`` (str): Adres email użytkownika.\n
    - ``password`` (str): Hasło użytkownika.

    Opcjonalne dane:\n
    - ``role`` (str, opcjonalnie): Rola użytkownika (domyślnie "client").\n
    - ``phone_number`` (str, opcjonalnie): Numer telefonu użytkownika.\n
    - ``address_line1`` (str, opcjonalnie): Adres użytkownika.\n
    - ``city`` (str, opcjonalnie): Miasto użytkownika.\n
    - ``postal_code`` (str, opcjonalnie): Kod pocztowy użytkownika.\n
    - ``country`` (str, opcjonalnie): Kraj użytkownika.\n
    - ``date_of_birth`` (str, opcjonalnie): Data urodzenia użytkownika.\n
    - ``gender`` (str, opcjonalnie): Płeć użytkownika.

    Zwraca:\n
    - ``201`` **Created**: Jeśli użytkownik został pomyślnie utworzony, zwraca szczegóły użytkownika oraz token dostępu.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne lub adres email już istnieje.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił nieoczekiwany błąd podczas tworzenia użytkownika.
    """

    users_service: UsersService = UsersService()
    audit_logs_service: AuditLogsService = AuditLogsService()
    try:
        data = request.get_json()

        required_fields: list[str] = ["first_name", "last_name", "email", "password"]
        validation_errors: dict[str, str] = {}
        if not data:
            return jsonify({"error": "Niepoprawne dane żądania"}), 400

        for field in required_fields:
            value = data.get(field, "").strip() if isinstance(data.get(field), str) else data.get(field)
            if not value:
                validation_errors[field] = "Pole nie może być puste"
            elif field == "email" and not isinstance(value, str):
                validation_errors[field] = "Email musi być tekstem"
            elif field == "password" and not isinstance(value, str):
                validation_errors[field] = "Hasło musi być tekstem"

        if validation_errors:
            return jsonify({
                "error": validation_errors
            }), 400

        user_data: dict[str, str] = {
            "first_name": data["first_name"].strip(),
            "last_name": data["last_name"].strip(),
            "email": data["email"].strip().lower(),
            "password": data["password"],
            "role": data.get("role", "client"),
            "status": "active"
        }

        optional_fields: list[str] = [
            "phone_number", "address_line1", "city", "postal_code", "country",
            "date_of_birth", "gender", "phone_number"
        ]

        for field in optional_fields:
            if field in data:
                user_data[field] = data[field]

        if users_service.email_exists(user_data["email"]):
            return jsonify({"error": "Email już istnieje"}), 400

        user: User = users_service.create(**user_data)
        access_token: str = create_access_token(identity=str(user.id))

        audit_logs_service.log_action(
            user_id=user.id,
            action="CREATE_USER",
            details={
                "created_user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "role": user.role
            }
        )

        return jsonify({
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role,
            "token": access_token
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
