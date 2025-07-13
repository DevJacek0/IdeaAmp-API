from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from datetime import datetime

from app.models.discount import Discount
from app.routes.decorators.adminRequired import admin_required
from app.services.discountService import DiscountService

create_discounts_blueprint: Blueprint = Blueprint("create_discounts", __name__, url_prefix="/discounts")


@create_discounts_blueprint.route("/create", methods=["POST"])
@jwt_required()
@admin_required
def create_discount() -> tuple[Response, int]:
    """
    Tworzy nową zniżkę.

    Metoda: ``POST``\n
    Url zapytania: ``/discounts/create``

    Obsługuje żądania POST do tworzenia nowej zniżki. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Dane żądania:\n
    - ``code`` (str): Kod zniżki.\n
    - ``value`` (float): Wartość zniżki (w procentach).\n
    - ``expiry_on`` (int, opcjonalnie): Data wygaśnięcia zniżki jako timestamp.\n
    - ``max_uses`` (int, opcjonalnie): Maksymalna liczba użyć zniżki.

    Zwraca:\n
    - ``201`` **Created**: Jeśli zniżka została pomyślnie utworzona, zwraca szczegóły zniżki.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne lub kod zniżki już istnieje.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    discount_service: DiscountService = DiscountService()
    try:
        data = request.get_json()

        required_fields: list[str] = ["code", "value"]
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": f"Nieprawidłowe dane żądania. Wymagane pola: {', '.join(required_fields)}"}), 400

        code: str = data["code"].strip()
        value: float = float(data["value"])
        expiry_on: str | None = data["expiry_on"] if "expiry_on" in data and data["expiry_on"] else None
        max_uses: int = int(data["max_uses"]) if "max_uses" in data and data["max_uses"] else None

        if value <= 0 or value > 100:
            return jsonify({"error": "Wartość zniżki musi być między 0 a 100"}), 400

        if discount_service.get_by_code(code):
            return jsonify({"error": "Kod zniżki już istnieje"}), 400

        discount: Discount = discount_service.create_discount(code, value, expiry_on, max_uses)

        return jsonify({
            "id": discount.id,
            "code": discount.code,
            "value": str(discount.value),
            "expiry_on": discount.expiry_on if discount.expiry_on else None,
            "max_uses": discount.max_uses,
            "usage_count": discount.usage_count
        }), 201

    except ValueError as e:
        return jsonify({"error": "Nieprawidłowy format daty dla expiry_on. Użyj formatu ISO (RRRR-MM-DDTHH:MM:SS)"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
