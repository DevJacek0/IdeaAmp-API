from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.car import Car
from app.services.carService import CarsService

create_cars_blueprint: Blueprint = Blueprint("create_cars", __name__, url_prefix="/cars")


@create_cars_blueprint.route("/create", methods=["POST"])
@jwt_required()
def create_car() -> tuple[Response, int]:
    """
    Rejestruje nowy samochód.

    Metoda: ``POST``\n
    Url zapytania: ``/cars/create``

    Obsługuje żądania POST do rejestracji nowego samochodu w bazie danych. Użytkownik musi być
    uwierzytelniony za pomocą JWT. Wymagane pola to: ``plate``, ``name``, ``battery_capacity``,
    ``max_charging_power``, ``connector_type``, ``year``, ``country_code``.

    Dane żądania:\n
    - ``plate`` (str): Numer rejestracyjny samochodu.\n
    - ``name`` (str): Nazwa samochodu.\n
    - ``battery_capacity`` (float): Pojemność baterii samochodu.\n
    - ``max_charging_power`` (float): Maksymalna moc ładowania samochodu.\n
    - ``connector_type`` (str): Typ złącza samochodu.\n
    - ``year`` (int): Rok produkcji samochodu.\n
    - ``country_code`` (str): Kod kraju rejestracji samochodu.

    Zwraca:\n
    - ``201`` **Created**: Jeśli samochód został pomyślnie utworzony.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne lub samochód z podanym numerem rejestracyjnym już istnieje.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    cars_service: CarsService = CarsService()
    try:
        data = request.get_json()

        required_fields: list[str] = ["plate", "name", "battery_capacity", "max_charging_power", "connector_type",
                           "year", "country_code"]

        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": f"Nieprawidłowe dane żądania. Wymagane pola: {', '.join(required_fields)}"}), 400

        owner_id: int = int(get_jwt_identity())
        plate: str = data["plate"].strip().upper()
        name: str  = data["name"].strip()
        battery_capacity: float = data["battery_capacity"]
        max_charging_power: float = data["max_charging_power"]
        connector_type: str = data["connector_type"]
        year: int = data["year"]
        country_code: str = data["country_code"]

        if cars_service.plate_exists(plate):
            return jsonify({"error": "Samochód z podanym numerem rejestracyjnym już istnieje"}), 400

        car: Car = cars_service.create(owner_id, plate, name, battery_capacity, max_charging_power, connector_type,
                                       country_code, year)

        return jsonify({
            "id": car.id,
            "owner_id": car.owner_id,
            "plate": car.plate,
            "name": car.name,
            "battery_capacity": str(car.battery_capacity),
            "max_charging_power": str(car.max_charging_power),
            "connector_type": car.connector_type,
            "year": car.year,
            "country_code": car.country_code,
            "registered_on": car.registered_on
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
