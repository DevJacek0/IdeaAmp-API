from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required

from app.services.discountService import DiscountService

apply_discounts_blueprint: Blueprint = Blueprint("apply_discounts", __name__, url_prefix="/discounts")


@apply_discounts_blueprint.route("/apply", methods=["POST"])
@jwt_required()
def apply_discount() -> tuple[Response, int]:
    """
    Zastosowuje zniżkę.

    Metoda: ``POST``\n
    Url zapytania: ``/discounts/apply``

    Obsługuje żądania POST do zastosowania zniżki. Użytkownik musi być uwierzytelniony za pomocą JWT.
    Wymagane pola to: ``amount`` i ``code``.

    Dane żądania:\n
    - ``amount`` (float): Kwota, do której ma być zastosowana zniżka.\n
    - ``code`` (str): Kod zniżki.

    Zwraca:\n
    - ``200`` **OK**: Jeśli zniżka została pomyślnie zastosowana, zwraca oryginalną i końcową kwotę oraz wiadomość.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne lub kwota jest mniejsza lub równa 0.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    discount_service: DiscountService = DiscountService()
    try:
        data = request.get_json()

        required_fields: list[str] = ["amount", "code"]
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": f"Nieprawidłowe dane żądania. Wymagane pola: {', '.join(required_fields)}"}), 400

        amount: float = float(data["amount"])
        code: str = data["code"].strip()

        if amount <= 0:
            return jsonify({"error": "Kwota musi być większa niż 0"}), 400

        final_amount, message, status = discount_service.apply_discount(amount, code)

        return jsonify({
            "original_amount": str(amount),
            "final_amount": str(final_amount),
            "message": message
        }), 200 if status == discount_service.DiscountStatus.SUCCESS else 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500
