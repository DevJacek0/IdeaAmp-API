from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.faq import Faq
from app.routes.decorators.adminRequired import admin_required
from app.services import FaqService

create_faq_blueprint: Blueprint = Blueprint("create_faq", __name__, url_prefix="/faq")


@create_faq_blueprint.route("/create", methods=["POST"])
@jwt_required()
@admin_required
def create() -> tuple[Response, int]:
    """
    Tworzy nowe FAQ.

    Metoda: ``POST``\n
    Url zapytania: ``/faq/create``

    Obsługuje żądania POST do tworzenia nowego FAQ. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Dane żądania:\n
    - ``question`` (str): Pytanie FAQ.\n
    - ``answer`` (str): Odpowiedź na pytanie FAQ.

    Zwraca:\n
    - ``200`` **OK**: Jeśli FAQ zostało pomyślnie utworzone, zwraca szczegóły FAQ.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne lub pytanie już istnieje.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    faq_service: FaqService = FaqService()
    question: str = request.json["question"]
    answer: str = request.json["answer"]

    if "question" not in request.json or "answer" not in request.json:
        return jsonify({"error": "Brak odpowiedzi lub pytania"}), 400

    if not isinstance(question, str) or not isinstance(answer, str):
        return jsonify({"error": "Pytanie i odpowiedź muszą być typu string"}), 400


    if faq_service.get_by_question(question):
        return jsonify({"error": "Pytanie już istnieje"}), 400

    faq: Faq = faq_service.create(user_id=(get_jwt_identity()), question=question, answer=answer, public=False)
    return_faq: Faq = faq_service.get(faq.id)

    return jsonify({"faq": faq_service.to_dict(return_faq)}), 200


@create_faq_blueprint.route("/add-question", methods=["POST"])
@jwt_required()
def add_question() -> tuple[Response, int]:
    """
    Dodaje nowe pytanie do FAQ.

    Metoda: ``POST``\n
    Url zapytania: ``/faq/add-question``

    Obsługuje żądania POST do dodania nowego pytania do FAQ. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Dane żądania:\n
    - ``question`` (str): Pytanie FAQ.

    Zwraca:\n
    - ``200`` **OK**: Jeśli pytanie zostało pomyślnie dodane, zwraca szczegóły FAQ.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    faq_service: FaqService = FaqService()
    question: str = request.json["question"]

    if "question" not in request.json:
        return jsonify({"error": "Brak odpowiedzi lub pytania"}), 400

    if not isinstance(question, str):
        return jsonify({"error": "Pytanie musi być typu string"}), 400

    faq: Faq = faq_service.add_question(user_id=(get_jwt_identity()), question=question)
    return_faq: Faq = faq_service.get(faq.id)

    return jsonify({"faq": faq_service.to_dict(return_faq)}), 200


@create_faq_blueprint.route("/add-answer/<int:faq_id>", methods=["POST"])
@jwt_required()
@admin_required
def add_answer(faq_id) -> tuple[Response, int]:
    """
    Dodaje odpowiedź do istniejącego pytania FAQ.

    Metoda: ``POST``\n
    Url zapytania: ``/faq/add-answer/<faq-id``

    Obsługuje żądania POST do dodania odpowiedzi do istniejącego pytania FAQ. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``faq_id`` (int): ID pytania FAQ do aktualizacji.

    Dane żądania:\n
    - ``answer`` (str): Odpowiedź na pytanie FAQ.

    Zwraca:\n
    - ``200`` **OK**: Jeśli odpowiedź została pomyślnie dodana, zwraca szczegóły FAQ.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne lub pytanie nie istnieje.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    faq_service: FaqService = FaqService()
    answer: str = request.json["answer"]

    faq: Faq = faq_service.get(faq_id)

    if not faq:
        return jsonify({"error": "Pytanie nie istnieje"}), 400

    if "answer" not in request.json:
        return jsonify({"error": "Brak odpowiedzi"}), 400


    if not isinstance(answer, str):
        return jsonify({"error": "Pytanie musi być typu string"}), 400

    faq: Faq = faq_service.add_answer(faq_id, answer)
    return_faq: Faq = faq_service.get(faq.id)

    return jsonify({"faq": faq_service.to_dict(return_faq)}), 200
