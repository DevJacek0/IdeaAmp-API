from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from datetime import datetime

from app.models.discount import Discount
from app.routes.decorators.adminRequired import admin_required
from app.services.discountService import DiscountService

update_discounts_blueprint: Blueprint = Blueprint("update_discounts", __name__, url_prefix="/discounts")


@update_discounts_blueprint.route("/update/<int:discount_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_discount(discount_id) -> tuple[Response, int]:
    """
    Aktualizuje zniżkę.

    Metoda: ``PUT``\n
    Url zapytania: ``/discounts/update/<discount-id>``

    Obsługuje żądania PUT do aktualizacji zniżki na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``discount_id`` (int): ID zniżki do aktualizacji.

    Dane żądania:\n
    - ``code`` (str, opcjonalnie): Nowy kod zniżki.\n
    - ``value`` (float, opcjonalnie): Nowa wartość zniżki (w procentach).\n
    - ``expiry_on`` (str, opcjonalnie): Nowa data wygaśnięcia zniżki w formacie ISO (RRRR-MM-DDTHH:MM:SS).\n
    - ``max_uses`` (int, opcjonalnie): Nowa maksymalna liczba użyć zniżki.

    Zwraca:\n
    - ``200`` **OK**: Jeśli zniżka została pomyślnie zaktualizowana, zwraca szczegóły zniżki.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne lub kod zniżki już istnieje.\n
    - ``404`` **Not Found**: Jeśli nie znaleziono zniżki o podanym ID.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    discount_service: DiscountService = DiscountService()
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Nie przesłano żadnych danych do aktualizacji"}), 400

        updates: dict[str, str | float] = {}

        if "code" in data:
            code: str = data["code"].strip()
            existing_discount: Discount = discount_service.get_by_code(code)
            if existing_discount and existing_discount.id != discount_id:
                return jsonify({"error": "Kod zniżki już istnieje"}), 400
            updates["code"] = code

        if "value" in data:
            value: float = float(data["value"])
            if value <= 0 or value > 100:
                return jsonify({"error": "Wartość zniżki musi być między 0 a 100"}), 400
            updates["value"] = value

        if "expiry_on" in data:
            updates["expiry_on"] = data["expiry_on"]

        if "max_uses" in data:
            max_uses: int = int(data["max_uses"]) if data["max_uses"] else None
            updates["max_uses"] = max_uses

        updated_discount: Discount = discount_service.update_discount(discount_id, **updates)

        if not updated_discount:
            return jsonify({"error": "Nie znaleziono zniżki"}), 404

        return jsonify({
            "id": updated_discount.id,
            "code": updated_discount.code,
            "value": str(updated_discount.value),
            "expiry_on": updated_discount.expiry_on if updated_discount.expiry_on else None,
            "max_uses": updated_discount.max_uses,
            "usage_count": updated_discount.usage_count
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
