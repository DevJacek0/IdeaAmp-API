from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.routes.decorators.adminRequired import admin_required
from app.services import UsersService
from app.services.discountService import DiscountService

delete_discounts_blueprint = Blueprint("delete_discounts", __name__, url_prefix="/discounts")


@delete_discounts_blueprint.route("/<int:discount_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_discount(discount_id) -> tuple[Response, int]:
    """
    Usuwa zniżkę.

    Metoda: ``DELETE``\n
    Url zapytania: ``/discounts/<discount-id>``

    Obsługuje żądania DELETE do usunięcia zniżki. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``discount_id`` (int): ID zniżki do usunięcia.

    Zwraca:\n
    - ``200`` **OK**: Jeśli zniżka została pomyślnie usunięta, zwraca wiadomość potwierdzającą.\n
    - ``404`` **Not Found**: Jeśli nie znaleziono zniżki o podanym ID.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    discount_service: DiscountService = DiscountService()
    try:
        if discount_service.delete_discount(discount_id):
            return jsonify({"message": "Zniżka została pomyślnie usunięta"}), 200
        return jsonify({"error": "Nie znaleziono zniżki"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
