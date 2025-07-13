from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.pointThreshold import PointThreshold
from app.routes.decorators.adminRequired import admin_required
from app.routes.decorators.pagination import paginate
from app.services import UsersService
from app.services.pointThresholdService import PointThresholdService
from app.services.discountService import DiscountService
import random
import string
from datetime import datetime, timedelta

points_blueprint: Blueprint = Blueprint('points', __name__, url_prefix="/points")

"""
Punktyfikacja nie została wdrożona do frontendu - nie starczyło czasu.
"""


@points_blueprint.route("/thresholds/get-all", methods=["GET"])
@jwt_required()
@paginate
def get_thresholds() -> list[dict[str, int | str | float]] | tuple[Response, int]:
    """
    Pobiera wszystkie progi punktowe.

    Metoda: ``GET``\n
    Url zapytania: ``/points/thresholds/get-all``

    Obsługuje żądania GET do pobrania wszystkich dostępnych progów punktowych. Użytkownik musi być uwierzytelniony za pomocą JWT.
    Funkcja obsługuje paginację.

    Zwraca:\n
    - ``200`` **OK**: Lista wszystkich progów punktowych w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    try:
        service: PointThresholdService = PointThresholdService()
        thresholds: list[PointThreshold] = service.get_available_thresholds()

        return [
            {
                "id": t.id,
                "points_required": t.points_required,
                "discount_value": float(t.discount_value),
                "description": t.description,
                "created_on": t.created_on
            }
            for t in thresholds
        ]
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@points_blueprint.route("/thresholds/create", methods=["POST"])
@jwt_required()
@admin_required
def create_threshold() -> tuple[Response, int]:
    """
    Tworzy nowy próg punktowy.

    Metoda: ``POST``\n
    Url zapytania: ``/points/thresholds/create``

    Obsługuje żądania POST do tworzenia nowego progu punktowego. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Dane żądania:\n
    - ``points_required`` (int): Wymagana liczba punktów.\n
    - ``discount_value`` (float): Wartość rabatu.\n
    - ``description`` (str, opcjonalnie): Opis progu punktowego.

    Zwraca:\n
    - ``201`` **Created**: Jeśli próg punktowy został pomyślnie utworzony, zwraca szczegóły progu punktowego.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    try:
        data = request.get_json()
        required_fields: list[str] = ["points_required", "discount_value"]

        if not all(field in data for field in required_fields):
            return jsonify({"error": "Brak wymaganych pól"}), 400

        service: PointThresholdService = PointThresholdService()
        threshold: PointThreshold = service.create_threshold(
            points_required=int(data["points_required"]),
            discount_value=float(data["discount_value"]),
            description=data.get("description")
        )

        if not threshold:
            return jsonify({"error": "Nie udało się utworzyć progu punktowego"}), 500

        return jsonify({
            "id": threshold.id,
            "points_required": threshold.points_required,
            "discount_value": float(threshold.discount_value),
            "description": threshold.description,
            "created_on": threshold.created_on
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@points_blueprint.route("/get/self", methods=["GET"])
@jwt_required()
def get_points_balance() -> tuple[Response, int]:
    """
    Pobiera saldo punktów użytkownika.

    Metoda: ``GET``\n
    Url zapytania: ``/points/get/self``

    Obsługuje żądania GET do pobrania salda punktów zalogowanego użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Zwraca:\n
    - ``200`` **OK**: Saldo punktów użytkownika w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    try:
        user_id: int = int(get_jwt_identity())

        users_service: UsersService = UsersService()
        points: int = users_service.get_user_points(user_id)

        return jsonify({
            "points": points
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@points_blueprint.route("/exchange", methods=["POST"])
@jwt_required()
def exchange_points() -> tuple[Response, int]:
    """
    Wymienia punkty na kod rabatowy.

    Metoda: ``POST``\n
    Url zapytania: ``/points/exchange``

    Obsługuje żądania POST do wymiany punktów na kod rabatowy na podstawie ID progu punktowego. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Dane żądania:\n
    - ``threshold_id`` (int): ID progu punktowego.

    Zwraca:\n
    - ``200`` **OK**: Jeśli punkty zostały pomyślnie wymienione na kod rabatowy, zwraca szczegóły kodu rabatowego.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne lub użytkownik nie ma wystarczającej liczby punktów.\n
    - ``404`` **Not Found**: Jeśli próg punktowy nie istnieje.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    try:
        data = request.get_json()
        threshold_id: int = int(data.get('threshold_id'))

        if not threshold_id:
            return jsonify({"error": "Brak ID progu punktowego"}), 400

        user_id: int = int(get_jwt_identity())
        users_service: UsersService = UsersService()
        threshold_service: PointThresholdService = PointThresholdService()
        discount_service: DiscountService = DiscountService()

        threshold: PointThreshold = threshold_service.get(threshold_id)
        if not threshold:
            return jsonify({"error": "Próg punktowy nie istnieje"}), 404

        user_points: int = users_service.get_user_points(user_id)
        if user_points < threshold.points_required:
            return jsonify({
                "error": "Niewystarczająca liczba punktów",
                "required": threshold.points_required,
                "current": user_points
            }), 400

        discount_code: str = generate_discount_code()
        expiry_date: int = int((datetime.utcnow() + timedelta(days=30)).timestamp() * 1000)

        try:
            discount = discount_service.create_discount(
                code=discount_code,
                value=float(threshold.discount_value),
                expiry_on=expiry_date,
                max_uses=1
            )

            if not users_service.deduct_points(user_id, threshold.points_required):
                discount_service.delete_discount(discount.id)
                return jsonify({"error": "Nie udało się wymienić punktów"}), 500

            return jsonify({
                "message": "Pomyślnie wymieniono punkty na kod rabatowy",
                "discount_code": discount.code,
                "discount_value": float(discount.value),
                "expiry_on": discount.expiry_on,
                "remaining_points": user_points - threshold.points_required
            }), 200
        except Exception as e:
            return jsonify({"error": f"Błąd podczas tworzenia kodu rabatowego: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@points_blueprint.route("/thresholds/<int:threshold_id>/delete", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_threshold(threshold_id) -> tuple[Response, int]:
    """
    Usuwa próg punktowy.

    Metoda: ``DELETE``\n
    Url zapytania: ``/points/thresholds/<threshold-id>/delete``

    Obsługuje żądania DELETE do usunięcia progu punktowego na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``threshold_id`` (int): ID progu punktowego do usunięcia.

    Zwraca:\n
    - ``200`` **OK**: Jeśli próg punktowy został pomyślnie usunięty, zwraca wiadomość potwierdzającą.\n
    - ``404`` **Not Found**: Jeśli próg punktowy nie istnieje.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    try:
        service: PointThresholdService = PointThresholdService()

        if not service.delete_threshold(threshold_id):
            return jsonify({"error": "Próg punktowy nie istnieje"}), 404

        return jsonify({"message": "Próg punktowy został usunięty"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@points_blueprint.route("/thresholds/<int:threshold_id>/deactivate", methods=["POST"])
@jwt_required()
@admin_required
def deactivate_threshold(threshold_id) -> tuple[Response, int]:
    """
    Dezaktywuje próg punktowy.

    Metoda: ``POST``\n
    Url zapytania: ``/points/thresholds/<threshold-id>/deactivate``

    Obsługuje żądania POST do dezaktywacji progu punktowego na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``threshold_id`` (int): ID progu punktowego do dezaktywacji.

    Zwraca:\n
    - ``200`` **OK**: Jeśli próg punktowy został pomyślnie dezaktywowany, zwraca wiadomość potwierdzającą.\n
    - ``404`` **Not Found**: Jeśli próg punktowy nie istnieje.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    try:
        service: PointThresholdService = PointThresholdService()

        if not service.deactivate_threshold(threshold_id):
            return jsonify({"error": "Próg punktowy nie istnieje"}), 404

        return jsonify({"message": "Próg punktowy został dezaktywowany"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def generate_discount_code(length: int = 8) -> str:
    """Generuje unikalny kod rabatowy"""

    code: str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    discount_service: DiscountService = DiscountService()
    while discount_service.get_by_code(code):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    return code
