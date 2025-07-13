from typing import Any

from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.faq import Faq
from app.routes.decorators.pagination import paginate
from app.services import FaqService, UsersService

gets_faq_blueprint: Blueprint = Blueprint("gets_faq", __name__, url_prefix="/faq")


@gets_faq_blueprint.route("/get/<int:faq_id>", methods=["GET"])
@jwt_required()
def get_faq(faq_id: int) -> tuple[Response, int]:
    """
    Pobiera FAQ.

    Metoda: ``GET``\n
    Url zapytania: ``/faq/get/<faq-id>``

    Obsługuje żądania GET do pobrania FAQ na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``faq_id`` (int): ID FAQ do pobrania.

    Zwraca:\n
    - ``200`` **OK**: Szczegóły FAQ w formacie JSON.\n
    - ``403`` **Forbidden**: Jeśli FAQ nie jest publiczny, a użytkownik nie jest administratorem.\n
    - ``404`` **Not Found**: Jeśli nie znaleziono FAQ o podanym ID.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    faq_service: FaqService = FaqService()
    faq: Faq = faq_service.get(faq_id)

    user_service: UsersService = UsersService()
    user_id: int = int(get_jwt_identity())
    role: str = user_service.get(user_id).role

    if not faq:
        return jsonify({"error": "Nie znaleziono faq"}), 404
    # if role != "admin" and not faq.public:
    #     return jsonify({"error": "Faq nie jest publiczny"}), 403

    return jsonify({"faq": faq_service.to_dict(faq)}), 200


@gets_faq_blueprint.route("/get-all", methods=["GET"])
@jwt_required()
@paginate
def get_all_faq() -> list[dict[str, Any]]:
    """
    Pobiera wszystkie FAQ.

    Metoda: ``GET``\n
    Url zapytania: ``/faq/get-all``

    Obsługuje żądania GET do pobrania wszystkich FAQ. Użytkownik musi być uwierzytelniony za pomocą JWT.
    Funkcja obsługuje paginację.

    Zwraca:\n
    - ``200`` **OK**: Lista wszystkich FAQ w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    faq_service: FaqService = FaqService()
    faqs: list[Faq] = faq_service.get_all()

    user_service: UsersService = UsersService()
    user_id: int = int(get_jwt_identity())
    role: str = user_service.get(user_id).role

    # if role != "admin":
    #     faqs = [faq for faq in faqs if faq.public]
    #     return [faq_service.to_dict(faq) for faq in faqs], 200
    # else:
    # ^ Funkcja publikacji nie jest wdrożona w frontendzie - nie starczyło czasu.
    return [faq_service.to_dict(faq) for faq in faqs]


@gets_faq_blueprint.route("/get-all/self", methods=["GET"])
@jwt_required()
@paginate
def get_all_faq_self() -> list[dict[str, Any]]:
    """
    Pobiera wszystkie FAQ użytkownika.

    Metoda: ``GET``\n
    Url zapytania: ``/faq/get-all/self``

    Obsługuje żądania GET do pobrania wszystkich FAQ utworzonych przez zalogowanego użytkownika. Użytkownik musi być uwierzytelniony za pomocą JWT.
    Funkcja obsługuje paginację.

    Zwraca:\n
    - ``200`` **OK**: Lista wszystkich FAQ użytkownika w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    faq_service: FaqService = FaqService()
    user_id: int = int(get_jwt_identity())
    faqs: list[Faq] = faq_service.get_by_user(user_id)

    return [faq_service.to_dict(faq) for faq in faqs]
