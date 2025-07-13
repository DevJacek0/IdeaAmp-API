import time
from typing import Any

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from decimal import Decimal
from datetime import datetime

from app.models.user import User
from app.routes.decorators.adminRequired import admin_required
from app.services import AuditLogsService
from app.services.userService import UsersService

update_users_blueprint: Blueprint = Blueprint('update_users', __name__, url_prefix="/users")


@update_users_blueprint.route("/update/<int:user_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_user(user_id) -> tuple[Response, int]:
    """
    Aktualizuje dane użytkownika na podstawie ID.

    Metoda: ``PUT``\n
    Url zapytania: ``/users/update/<user-id>``

    Obsługuje żądania PUT do aktualizacji danych użytkownika na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``user_id`` (int): ID użytkownika do aktualizacji.

    Dozwolone dane:\n
    - ``first_name`` (str): Imię użytkownika.\n
    - ``last_name`` (str): Nazwisko użytkownika.\n
    - ``email`` (str): Adres e-mail użytkownika.\n
    - ``phone_number`` (str): Numer telefonu użytkownika.\n
    - ``address_line1`` (str): Adres użytkownika.\n
    - ``city`` (str): Miasto użytkownika.\n
    - ``postal_code`` (str): Kod pocztowy użytkownika.\n
    - ``country`` (str): Kraj użytkownika.\n
    - ``date_of_birth`` (str): Data urodzenia użytkownika (format: YYYY-MM-DD).\n
    - ``gender`` (str): Płeć użytkownika.\n
    - ``role`` (str): Rola użytkownika (tylko dla administratorów).\n
    - ``balance`` (float): Saldo użytkownika (tylko dla administratorów).\n
    - ``status`` (str): Status użytkownika (tylko dla administratorów).\n
    - ``two_factor_enabled`` (bool): Czy weryfikacja dwuetapowa jest włączona (tylko dla administratorów).\n
    - ``avatar_id`` (int): ID awatara użytkownika (tylko dla administratorów). \n
    - ``password`` (str): Hasło użytkownika (tylko dla administratorów).\n

    Zwraca:\n
    - ``200`` **OK**: Jeśli dane użytkownika zostały pomyślnie zaktualizowane.\n
    - ``400`` **Bad Request**: Jeśli brakuje wymaganych danych lub dane są nieprawidłowe.\n
    - ``403`` **Forbidden**: Jeśli użytkownik nie ma uprawnień do aktualizacji danych.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    audit_logs_service: AuditLogsService = AuditLogsService()

    user_data = request.get_json()
    if not isinstance(user_data, dict):
        return jsonify({"error": "Niepoprawny format danych"}), 400

    allowed_fields: set[str] = {
        "first_name", "last_name", "password", "email", "role", "balance",
        "phone_number", "address_line1", "city", "postal_code", "country",
        "date_of_birth", "gender", "avatar_id", "status", "two_factor_enabled"
    }

    update_fields: set[str] = set(user_data.keys()) & allowed_fields
    if not update_fields:
        return jsonify({"error": "Brak prawidłowych pól do aktualizacji"}), 400

    if "date_of_birth" in user_data and user_data["date_of_birth"] == "":
        update_fields.remove("date_of_birth")
        del user_data["date_of_birth"]

    if "balance" in user_data:
        try:
            user_data["balance"] = float(user_data["balance"])
            if user_data["balance"] < 0:
                return jsonify({"error": "Balance nie może być ujemny"}), 400
        except ValueError:
            return jsonify({"error": "Balance musi być liczbą"}), 400

    if "status" in user_data and user_data["status"] not in ["active", "inactive", "suspended"]:
        return jsonify({"error": "Nieprawidłowy status użytkownika"}), 400

    if "role" in user_data and user_data["role"] not in ["admin", "client"]:
        return jsonify({"error": "Nieprawidłowa rola użytkownika"}), 400

    if "gender" in user_data and user_data["gender"] not in ["male", "female", "other"]:
        return jsonify({"error": "Nieprawidłowa wartość dla pola gender"}), 400

    if "date_of_birth" in user_data:
        try:
            user_data["date_of_birth"] = datetime.strptime(user_data["date_of_birth"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Nieprawidłowy format daty urodzenia (wymagany format: YYYY-MM-DD)"}), 400

    try:
        current_user_data: User = users_service.get(user_id)
        if not current_user_data:
            return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

        changes: dict[str, Any] = {}
        for field in update_fields:
            old_value = getattr(current_user_data, field, None)
            new_value = user_data[field]
            if old_value != new_value:
                if isinstance(old_value, Decimal):
                    old_value = float(old_value)
                if isinstance(new_value, Decimal):
                    new_value = float(new_value)
                if field == "date_of_birth":
                    new_value = new_value.strftime("%Y-%m-%d")
                changes[field] = new_value

        if changes:
            updated_user: User = users_service.update(user_id, **user_data)
            if not updated_user:
                return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

            audit_logs_service.log_action(
                user_id=get_jwt_identity(),
                action="UPDATE_USER",
                details={
                    "updated_user_id": user_id,
                    "changes": changes,
                    "modified_by": get_jwt_identity()
                }
            )

            return jsonify(serialize_user(updated_user)), 200
        else:
            return jsonify(serialize_user(current_user_data)), 200

    except Exception as e:
        return jsonify({"error": f"Błąd podczas aktualizacji: {str(e)}"}), 500


@update_users_blueprint.route("/update/self", methods=["PUT"])
@jwt_required()
def update_self() -> tuple[Response, int]:
    """
    Aktualizuje dane zalogowanego użytkownika.

    Metoda: ``PUT``\n
    Url zapytania: ``/users/update/self``

    Obsługuje żądania PUT do aktualizacji danych zalogowanego użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Wymagane dane:\n
    - ``first_name`` (str): Imię użytkownika.\n
    - ``last_name`` (str): Nazwisko użytkownika.\n
    - ``email`` (str): Adres e-mail użytkownika.\n
    - ``phone_number`` (str): Numer telefonu użytkownika.\n
    - ``address_line1`` (str): Adres użytkownika.\n
    - ``city`` (str): Miasto użytkownika.\n
    - ``postal_code`` (str): Kod pocztowy użytkownika.\n
    - ``country`` (str): Kraj użytkownika.\n
    - ``date_of_birth`` (str): Data urodzenia użytkownika (format: YYYY-MM-DD).\n
    - ``gender`` (str): Płeć użytkownika.

    Zwraca:\n
    - ``200`` **OK**: Jeśli dane użytkownika zostały pomyślnie zaktualizowane.\n
    - ``400`` **Bad Request**: Jeśli brakuje wymaganych danych lub dane są nieprawidłowe.\n
    - ``403`` **Forbidden**: Jeśli użytkownik nie ma uprawnień do aktualizacji danych.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    audit_logs_service: AuditLogsService = AuditLogsService()
    current_user_id: int = int(get_jwt_identity())

    user_data = request.get_json()
    if not isinstance(user_data, dict):
        return jsonify({"error": "Niepoprawny format danych"}), 400

    allowed_fields: set[str] = {
        "first_name", "last_name", "email", "phone_number",
        "address_line1", "city", "postal_code", "country",
        "date_of_birth", "gender"
    }

    update_fields: set[str] = set(user_data.keys()) & allowed_fields
    if not update_fields:
        return jsonify({"error": "Brak prawidłowych pól do aktualizacji"}), 400

    restricted_fields: set[str] = {"role", "balance", "password", "status", "two_factor_enabled", "avatar_id"}
    if any(field in user_data for field in restricted_fields):
        return jsonify({"error": "Brak uprawnień do modyfikacji niektórych pól"}), 403

    if "date_of_birth" in user_data and user_data["date_of_birth"] == "":
        update_fields.remove("date_of_birth")
        del user_data["date_of_birth"]

    if "balance" in user_data:
        try:
            user_data["balance"] = float(user_data["balance"])
            if user_data["balance"] < 0:
                return jsonify({"error": "Balance nie może być ujemny"}), 400
        except ValueError:
            return jsonify({"error": "Balance musi być liczbą"}), 400

    if "status" in user_data and user_data["status"] not in ["active", "inactive", "suspended"]:
        return jsonify({"error": "Nieprawidłowy status użytkownika"}), 400

    if "role" in user_data and user_data["role"] not in ["admin", "client"]:
        return jsonify({"error": "Nieprawidłowa rola użytkownika"}), 400

    if "two_factor_enabled" in user_data and user_data["two_factor_enabled"] not in [True, False]:
        return jsonify({"error": "Nieprawidłowa wartość dla pola two_factor_enabled"}), 400

    if "gender" in user_data and user_data["gender"] not in ["male", "female", "other"]:
        return jsonify({"error": "Nieprawidłowa wartość dla pola gender"}), 400

    if "date_of_birth" in user_data:
        try:
            user_data["date_of_birth"] = datetime.strptime(user_data["date_of_birth"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Nieprawidłowy format daty urodzenia (wymagany format: YYYY-MM-DD)"}), 400

    try:
        current_user_data: User = users_service.get(current_user_id)
        if not current_user_data:
            return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

        changes: dict[str, Any] = {}
        for field in update_fields:
            old_value = getattr(current_user_data, field, None)
            new_value = user_data[field]
            if old_value != new_value:
                if isinstance(old_value, Decimal):
                    old_value = float(old_value)
                if isinstance(new_value, Decimal):
                    new_value = float(new_value)
                if field == "date_of_birth":
                    new_value = new_value.strftime("%Y-%m-%d")
                changes[field] = new_value

        if changes:
            updated_user: User = users_service.update(current_user_id, **user_data)
            if not updated_user:
                return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

            audit_logs_service.log_action(
                user_id=current_user_id,
                action="UPDATE_USER_SELF",
                details={
                    "changes": changes
                }
            )

            return jsonify(serialize_user(updated_user)), 200
        else:
            return jsonify(serialize_user(current_user_data)), 200

    except Exception as e:
        return jsonify({"error": f"Błąd podczas aktualizacji: {str(e)}"}), 500


def serialize_user(user: User) -> dict[str, int | str | float | bool | None]:
    """
    Formatuje dane użytkownika.

    Formatuje dane użytkownika do formatu JSON.

    Parametry:\n
    - ``user`` (User): Obiekt użytkownika do sformatowania.

    Zwraca:\n
    - **dict[str, int | str | float | bool | None]**: Sformatowane dane użytkownika.
    """

    user_dict: dict[str, int | str | float | bool | None] = {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role,
        "balance": float(user.balance) if user.balance else None,
        "points": float(user.points) if user.points else None,
        "phone_number": user.phone_number,
        "address_line1": user.address_line1,
        "city": user.city,
        "postal_code": user.postal_code,
        "country": user.country,
        "date_of_birth": user.date_of_birth if user.date_of_birth else None,
        "gender": user.gender,
        "avatar_id": user.avatar_id,
        "status": user.status,
        "two_factor_enabled": user.two_factor_enabled
    }
    return {k: v for k, v in user_dict.items()}