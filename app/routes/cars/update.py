from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.car import Car
from app.services import UsersService
from app.services.carService import CarsService

update_cars_blueprint: Blueprint = Blueprint('update_cars', __name__, url_prefix="/cars")


@update_cars_blueprint.route("/update/<int:car_id>", methods=["PUT"])
@jwt_required()
def update_car(car_id) -> tuple[Response, int]:
    """
    Aktualizuje dane samochodu.

    Metoda: ``PUT``\n
    Url zapytania: ``/cars/update/<car-id>``

    Obsługuje żądania PUT do aktualizacji danych samochodu. Użytkownik musi być
    uwierzytelniony za pomocą JWT. Administratorzy mogą aktualizować dowolne samochody, podczas gdy
    zwykli użytkownicy mogą aktualizować tylko swoje samochody.

    Parametry zapytania:\n
    - ``car_id`` (int): ID samochodu do aktualizacji.

    Dane żądania:\n
    - ``plate`` (str, opcjonalnie): Nowy numer rejestracyjny samochodu.\n
    - ``name`` (str, opcjonalnie): Nowa nazwa samochodu.\n
    - ``battery_capacity`` (float, opcjonalnie): Nowa pojemność baterii samochodu.\n
    - ``max_charging_power`` (float, opcjonalnie): Nowa maksymalna moc ładowania samochodu.\n
    - ``connector_type`` (str, opcjonalnie): Nowy typ złącza samochodu.\n
    - ``year`` (int, opcjonalnie): Nowy rok produkcji samochodu.\n
    - ``country_code`` (str, opcjonalnie): Nowy kod kraju rejestracji samochodu.

    Zwraca:\n
    - ``200`` **OK**: Zaktualizowane dane samochodu w formacie JSON.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``403`` **Forbidden**: Jeśli użytkownik nie ma uprawnień do aktualizacji tego samochodu.\n
    - ``404`` **Not Found**: Jeśli samochód o podanym ID nie został znaleziony.\n
    - ``409`` **Conflict**: Jeśli podany numer rejestracyjny jest już zajęty przez inny samochód.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    cars_service: CarsService = CarsService()
    users_service: UsersService = UsersService()
    user_id: int = int(get_jwt_identity())
    is_admin: bool = users_service.get(user_id).role == 'admin'

    car: Car = cars_service.get(car_id)
    if not car:
        return jsonify({"error": "Samochód nie został znaleziony"}), 404
    if not is_admin and car.owner_id != user_id:
        return jsonify({"error": "Brak uprawnień"}), 403

    car_data = request.get_json()
    if not isinstance(car_data, dict):
        return jsonify({"error": "Niepoprawny format danych"}), 400

    if "plate" in car_data:
        existing_car: Car = cars_service.get_by_plate(car_data["plate"])
        if existing_car and existing_car.id != car_id:
            return jsonify({"error": "Podany numer rejestracyjny jest już zajęty przez inny samochód"}), 409

    allowed_fields: set[str] = {"plate", "name", "battery_capacity", "max_charging_power", "connector_type", "year",
                      "country_code"}
    if not any(field in car_data for field in allowed_fields):
        return jsonify({"error": "Brak prawidłowych pol do aktualizacji"}), 400

    try:
        if "year" in car_data:
            car_data["year"] = int(car_data["year"])

        if "battery_capacity" in car_data:
            car_data["battery_capacity"] = float(car_data["battery_capacity"])

        if "max_charging_power" in car_data:
            car_data["max_charging_power"] = float(car_data["max_charging_power"])
    except ValueError:
        return jsonify({"error": "Niepoprawny format danych"}), 400

    updated_car: Car = cars_service.update(car_id, **car_data)
    return jsonify({
        "message": "Samochód został zaktualizowany" if is_admin else "Twój samochód został zaktualizowany"
    }), 200
