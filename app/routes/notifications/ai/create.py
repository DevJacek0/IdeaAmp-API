import random

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.car import Car
from app.services import CarsService
from app.services.notificationService import NotificationService

create_notifications_ai_blueprint: Blueprint = Blueprint('notifications_ai', __name__, url_prefix="/notifications/ai")


@create_notifications_ai_blueprint.route("/generate", methods=["POST"])
@jwt_required()
def create() -> tuple[Response, int]:
    """
    Generuje powiadomienie AI.

    Metoda: ``POST``\n
    Url zapytania: ``/notifications/ai/generate``

    Obsługuje żądania POST do generowania powiadomienia AI na podstawie ID samochodu. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``car_id`` (int, opcjonalnie): ID samochodu do generowania powiadomienia. Jeśli nie podano, wybierany jest losowy samochód użytkownika.

    Zwraca:\n
    - ``200`` **OK**: Jeśli powiadomienie zostało pomyślnie wygenerowane, zwraca treść powiadomienia.\n
    - ``404`` **Not Found**: Jeśli nie znaleziono samochodu.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd podczas tworzenia powiadomienia AI.
    """

    user_id: int = int(get_jwt_identity())

    car_id = request.args.get("car_id")
    cars_service: CarsService = CarsService()

    if not car_id:
        user_cars: list[Car] = cars_service.get_by_owner(user_id)
        car: Car = user_cars[random.randint(0, len(user_cars) - 1)]
    else:
        car: Car = cars_service.get(int(car_id))

    if not car:
        return jsonify({"error": "Nie znaleziono samochodu"}), 404

    notification_service: NotificationService = NotificationService()
    notification: str | bool = notification_service.generate_notification(int(car.id))

    if not notification:
        return jsonify({"error": "Błąd podczas tworzenia powiadomienia AI"}), 500

    return jsonify({"notification": notification}), 200