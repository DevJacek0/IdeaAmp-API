import time
from typing import Any

from flask import Blueprint, jsonify, Response, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.routes.decorators.adminRequired import admin_required
from app.routes.decorators.pagination import paginate
from app.services.userService import UsersService

gets_users_blueprint: Blueprint = Blueprint("gets_users", __name__, url_prefix="/users")


@gets_users_blueprint.route("/get-all", methods=["GET"])
@jwt_required()
@admin_required
@paginate
def get_all_users() -> list[dict[str, Any]]:
    """
    Pobiera wszystkich użytkowników.

    Metoda: ``GET``\n
    Url zapytania: ``/users/get-all``

    Obsługuje żądania GET do pobrania wszystkich użytkowników. Użytkownik musi być uwierzytelniony za pomocą JWT i posiadać uprawnienia administratora.

    Zwraca:\n
    - ``200`` **OK**: Lista wszystkich użytkowników w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    user_service: UsersService = UsersService()
    users: list[User] = user_service.get_all()
    return [format_user_data(user, include_private=True) for user in users]


@gets_users_blueprint.route("/get/self", methods=["GET"])
@jwt_required()
def get_self() -> tuple[Response, int]:
    """
    Pobiera dane zalogowanego użytkownika.

    Metoda: ``GET``\n
    Url zapytania: ``/users/get/self``

    Obsługuje żądania GET do pobrania danych zalogowanego użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Zwraca:\n
    - ``200`` **OK**: Dane zalogowanego użytkownika w formacie JSON.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    user_id: int = int(get_jwt_identity())
    user: User = users_service.get(user_id)

    if not user:
        return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

    return jsonify(format_user_data(user, include_private=True)), 200


@gets_users_blueprint.route("/get/<int:user_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_user(user_id) -> tuple[Response, int]:
    """
    Pobiera dane użytkownika na podstawie ID.

    Metoda: ``GET``\n
    Url zapytania: ``/users/get/<user-id>``

    Obsługuje żądania GET do pobrania danych użytkownika na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT.
    Wymaga uprawnień administratora.

    Parametry:\n
    - ``user_id`` (int): ID użytkownika do pobrania.

    Zwraca:\n
    - ``200`` **OK**: Dane użytkownika w formacie JSON.\n
    - ``403`` **Forbidden**: Jeśli użytkownik nie ma uprawnień do sprawdzenia tego użytkownika.\n
    - ``404`` **Not Found**: Jeśli użytkownik nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()

    user: User = users_service.get(user_id)
    if not user:
        return jsonify({"error": "Użytkownik nie został znaleziony"}), 404

    return jsonify(format_user_data(user, include_private=True)), 200


def format_user_data(user: Any, include_private: bool = False) -> dict[str, Any]:
    """
    Formatuje dane użytkownika.

    Formatuje dane użytkownika do formatu JSON. Jeśli ``include_private`` jest ustawione na True, zawiera również prywatne dane użytkownika.

    Parametry:\n
    - ``user`` (Any): Obiekt użytkownika do sformatowania.\n
    - ``include_private`` (bool, opcjonalnie): Czy zawierać prywatne dane użytkownika (domyślnie False).

    Zwraca:\n
    - **dict[str, Any]**: Sformatowane dane użytkownika.
    """

    user_data: dict[str, str | int | bool | None] = {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "registered_on": user.registered_on if user.registered_on else None,
        "address_line1": user.address_line1,
        "city": user.city,
        "postal_code": user.postal_code,
        "country": user.country,
        "date_of_birth": user.date_of_birth if user.date_of_birth else None,
        "gender": user.gender,
        "two_factor_enabled": user.two_factor_enabled,
        "points": user.points
    }

    if include_private:
        user_data.update({
            "role": user.role,
            "status": user.status,
            "balance": float(user.balance) if user.balance else 0.00
        })

    return user_data