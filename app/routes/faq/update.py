from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required

from app.models.faq import Faq
from app.routes.decorators.adminRequired import admin_required
from app.services import FaqService

update_faq_blueprint: Blueprint = Blueprint("update_faq", __name__, url_prefix="/faq")


@update_faq_blueprint.route("/update/<int:faq_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update(faq_id) -> tuple[Response, int]:
    """
    Aktualizuje pytanie FAQ.

    Metoda: ``PUT``\n
    Url zapytania: ``/faq/update/<faq-id>``

    Obsługuje żądania PUT do aktualizacji pytania FAQ na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``faq_id`` (int): ID pytania FAQ do aktualizacji.

    Dane żądania:\n
    - ``question`` (str, opcjonalnie): Nowe pytanie FAQ.\n
    - ``answer`` (str, opcjonalnie): Nowa odpowiedź na pytanie FAQ.\n
    - ``public`` (bool, opcjonalnie): Czy pytanie FAQ jest publiczne.

    Zwraca:\n
    - ``200`` **OK**: Jeśli pytanie FAQ zostało pomyślnie zaktualizowane, zwraca szczegóły FAQ.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne lub pytanie FAQ nie istnieje.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    data = request.get_json()
    faq_service: FaqService = FaqService()
    faq: Faq = faq_service.get(int(faq_id))

    if not faq:
        return jsonify({"error": "Pytanie nie istnieje"}), 400

    if not any(key in data for key in ['question', 'answer', 'public']):
        return jsonify({"error": "Nie przesłano żadnych danych do aktualizacji"}), 400

    question: str = data.get('question', faq.question)
    answer: str = data.get('answer', faq.answer)
    public: str = data.get('public', faq.public)

    if 'question' in data:
        if not isinstance(question, str):
            return jsonify({"error": "Pytanie musi być typu string"}), 400

    if 'answer' in data:
        if not isinstance(answer, str):
            return jsonify({"error": "Odpowiedź musi być typu string"}), 400

    if 'public' in data:
        if not isinstance(public, bool):
            return jsonify({"error": "Pole public musi być typu bool"}), 400
        if public == faq.public:
            return jsonify({"error": "Pole public nie zostało zmienione"}), 400

    faq_service.update(int(faq_id), question, answer, public)
    return_faq: Faq = faq_service.get(faq.id)
    return jsonify({"faq": faq_service.to_dict(return_faq)}), 200


@update_faq_blueprint.route("/publish/<int:faq_id>", methods=["PUT"])
@jwt_required()
@admin_required
def publish(faq_id) -> tuple[Response, int]:
    """
    Publikuje pytanie FAQ.

    Metoda: ``PUT``\n
    Url zapytania: ``/faq/publish/<faq-id>``

    Obsługuje żądania PUT do publikacji pytania FAQ na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``faq_id`` (int): ID pytania FAQ do publikacji.

    Zwraca:\n
    - ``200`` **OK**: Jeśli pytanie FAQ zostało pomyślnie opublikowane, zwraca szczegóły FAQ.\n
    - ``400`` **Bad Request**: Jeśli pytanie FAQ jest już opublikowane lub nie istnieje.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    faq_service: FaqService = FaqService()
    faq: Faq = faq_service.get(int(faq_id))

    if not faq:
        return jsonify({"error": "Pytanie nie istnieje"}), 400

    if faq.public:
        return jsonify({"error": "Pytanie jest już opublikowane"}), 400

    faq_service.publish(int(faq_id))
    return_faq: Faq = faq_service.get(faq.id)
    return jsonify({"faq": faq_service.to_dict(return_faq)}), 200
