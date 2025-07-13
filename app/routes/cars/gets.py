import os

from flask import Blueprint, jsonify, Response, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.car import Car
from app.routes.decorators.pagination import paginate
from app.services import UsersService, AttachmentsService
from app.services.carService import CarsService

gets_cars_blueprint: Blueprint = Blueprint("gets_cars", __name__, url_prefix="/cars")


@gets_cars_blueprint.route("/get-all", methods=["GET"])
@jwt_required()
@paginate
def get_all_cars() -> list[dict[str, str | int | float | None]]:
    """
    Pobiera wszystkie samochody.

    Metoda: ``GET``\n
    Url zapytania: ``/cars/get-all``

    Obsługuje żądania GET do pobierania wszystkich samochodów. Użytkownik musi być
    uwierzytelniony za pomocą JWT. Administratorzy mogą przeglądać wszystkie samochody, podczas gdy
    zwykli użytkownicy mogą przeglądać tylko swoje samochody.

    Zwraca:\n
    - ``JSON``: Lista samochodów w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    users_service: UsersService = UsersService()
    user_id: int = int(get_jwt_identity())
    is_admin: bool = users_service.get(user_id).role == 'admin'

    cars: list[Car] = CarsService().get_all() if is_admin else CarsService().get_by_owner(user_id)

    return [
        {
            "id": car.id,
            "owner_id": car.owner_id,
            "plate": car.plate,
            "name": car.name,
            "battery_capacity": str(car.battery_capacity) if car.battery_capacity else None,
            "max_charging_power": str(car.max_charging_power) if car.max_charging_power else None,
            "connector_type": car.connector_type,
            "year": car.year,
            "registered_on": car.registered_on,
            "country_code": car.country_code
        }
        for car in cars
    ]


@gets_cars_blueprint.route("get/<int:car_id>", methods=["GET"])
@jwt_required()
def get_car(car_id) -> dict[str, str | int | float | None] | tuple[Response, int]:
    """
    Pobiera szczegóły samochodu.

    Metoda: ``GET``\n
    Url zapytania: ``/cars/<car-id>``

    Obsługuje żądania GET do pobierania szczegółów konkretnego samochodu. Użytkownik musi być
    uwierzytelniony za pomocą JWT.

    Parametry zapytania:\n
    - ``car_id`` (int): ID samochodu do pobrania.

    Zwraca:\n
    - ``200`` **OK**: Szczegóły samochodu w formacie JSON.\n
    - ``404`` **Not Found**: Jeśli samochód o podanym ID nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    cars_service: CarsService = CarsService()
    car: Car = cars_service.get(car_id)
    if not car:
        return jsonify({"error": "Samochód nie istnieje"}), 404

    car_data = {
        "id": car.id,
        "owner_id": car.owner_id,
        "plate": car.plate,
        "name": car.name,
        "battery_capacity": str(car.battery_capacity) if car.battery_capacity else None,
        "max_charging_power": str(car.max_charging_power) if car.max_charging_power else None,
        "connector_type": car.connector_type,
        "year": car.year,
        "registered_on": car.registered_on,
        "country_code": car.country_code
    }

    return jsonify(car_data), 200


@gets_cars_blueprint.route("get/self", methods=["GET"])
@jwt_required()
@paginate
def get_self_cars() -> list[dict[str, str | int | float | None]]:

    """
    Pobiera swoje samochody użytkownika.

    Obsługuje żądania GET do pobierania samochodów użytkownika. Użytkownik musi być
    uwierzytelniony za pomocą JWT.

    Zwraca:\n
    - ``JSON``: Lista samochodów użytkownika w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    cars_service: CarsService = CarsService()
    user_id: int = int(get_jwt_identity())
    cars: list[Car] = cars_service.get_by_owner(user_id)

    return [
        {
            "id": car.id,
            "owner_id": car.owner_id,
            "plate": car.plate,
            "name": car.name,
            "battery_capacity": str(car.battery_capacity) if car.battery_capacity else None,
            "max_charging_power": str(car.max_charging_power) if car.max_charging_power else None,
            "connector_type": car.connector_type,
            "year": car.year,
            "registered_on": car.registered_on,
            "country_code": car.country_code
        }
        for car in cars
    ]


@gets_cars_blueprint.route("/<int:car_id>/image", methods=["GET"])
@jwt_required()
def get_car_image(car_id):
    """
    Pobiera obraz samochodu.

    Obsługuje żądania GET do pobierania obrazu samochodu. Użytkownik musi być
    uwierzytelniony za pomocą JWT.

    Parametry zapytania:\n
    - ``car_id`` (int): ID samochodu do pobrania obrazu.

    Zwraca:\n
    - ``200`` **OK**: Obraz samochodu.\n
    - ``404`` **Not Found**: Jeśli samochód o podanym ID nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    car: Car = CarsService().get(car_id)

    if not car:
        return jsonify({"error": "Samochód nie istnieje"}), 404

    car_name: str = car.name.lower()
    allowed_brands = {"bmw", "audi", "mercedes", "toyota", "honda", "ford", "tesla"}
    attachment_service: AttachmentsService = AttachmentsService()

    for brand in allowed_brands:
        if brand in car_name:
            image_path = attachment_service.get_file_path(f"attachments/cars/{brand}.png")
            if os.path.exists(image_path):
                return send_file(image_path), 200

    return send_file(attachment_service.get_file_path("attachments/cars/unknown.png")), 200
