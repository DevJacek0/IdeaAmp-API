from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required

from app.routes.decorators.adminRequired import admin_required
from app.services import FaqService

delete_faq_blueprint: Blueprint = Blueprint("delete_faq", __name__, url_prefix="/faq")


@delete_faq_blueprint.route("/delete/<int:faq_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_faq(faq_id) -> tuple[Response, int]:
    """
    Usuwa FAQ.

    Metoda: ``DELETE``\n
    Url zapytania: ``/faq/delete/<faq-id>``

    Obsługuje żądania DELETE do usunięcia FAQ. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``faq_id`` (int): ID FAQ do usunięcia.

    Zwraca:\n
    - ``200`` **OK**: Jeśli FAQ zostało pomyślnie usunięte, zwraca wiadomość potwierdzającą.\n
    - ``404`` **Not Found**: Jeśli nie znaleziono FAQ o podanym ID.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    faq_service: FaqService = FaqService()

    if faq_service.delete(int(faq_id)):
        return jsonify({"success": "Usunięto faq"}), 200
    else:
        return jsonify({"error": "Nie znaleziono faq"}), 404
