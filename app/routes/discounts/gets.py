from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.discount import Discount
from app.routes.decorators.adminRequired import admin_required
from app.routes.decorators.pagination import paginate
from app.services.discountService import DiscountService

gets_discounts_blueprint: Blueprint = Blueprint("gets_discounts", __name__, url_prefix="/discounts")


@gets_discounts_blueprint.route("/get-all", methods=["GET"])
@jwt_required()
@admin_required
@paginate
def get_all_discounts() -> list[dict[str, str | int]]:
    """
    Pobiera wszystkie zniżki.

    Metoda: ``GET``\n
    Url zapytania: ``/discounts/get-all``

    Obsługuje żądania GET do pobrania wszystkich zniżek. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora. Funkcja obsługuje paginację.

    Zwraca:\n
    - ``200`` **OK**: Lista wszystkich zniżek w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    discount_service: DiscountService = DiscountService()
    discounts: list[Discount] = discount_service.get_all()

    return [
        {
            "id": discount.id,
            "code": discount.code,
            "value": str(discount.value),
            "expiry_on": discount.expiry_on if discount.expiry_on else None,
            "max_uses": discount.max_uses,
            "usage_count": discount.usage_count
        }
        for discount in discounts
    ]


@gets_discounts_blueprint.route("/<int:discount_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_discount(discount_id) -> tuple[Response, int]:
    """
    Pobiera zniżkę.

    Metoda: ``GET``\n
    Url zapytania: ``/discounts/<discount-id>``

    Obsługuje żądania GET do pobrania zniżki na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``discount_id`` (int): ID zniżki do pobrania.

    Zwraca:\n
    - ``200`` **OK**: Szczegóły zniżki w formacie JSON.\n
    - ``404`` **Not Found**: Jeśli nie znaleziono zniżki o podanym ID.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    discount_service: DiscountService = DiscountService()
    discount: Discount = discount_service.get(discount_id)

    if not discount:
        return jsonify({"error": "Nie znaleziono zniżki"}), 404

    return jsonify({
        "id": discount.id,
        "code": discount.code,
        "value": str(discount.value),
        "expiry_on": discount.expiry_on if discount.expiry_on else None,
        "max_uses": discount.max_uses,
        "usage_count": discount.usage_count
    }), 200
