import json
from datetime import time

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required

from app.models.station import Station
from app.routes.decorators.adminRequired import admin_required
from app.services.stationService import StationService

create_stations_blueprint: Blueprint = Blueprint("create_stations", __name__, url_prefix="/stations")


@create_stations_blueprint.route("/create", methods=["POST"])
@jwt_required()
@admin_required
def create_station() -> tuple[Response, int]:
    """
    Tworzy nową stację.

    Metoda: ``POST``\n
    Url zapytania: ``/stations/create``

    Obsługuje żądania POST do utworzenia nowej stacji. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Wymagane dane:\n
    - ``name`` (str): Nazwa stacji (min. 3 znaki).\n
    - ``lat`` (float): Szerokość geograficzna (w zakresie od -90 do 90 stopni).\n
    - ``lng`` (float): Długość geograficzna (w zakresie od -180 do 180 stopni).\n
    - ``address`` (str): Adres stacji (min. 5 znaków).\n
    - ``opening_time`` (str): Godzina otwarcia (format: HH:MM).\n
    - ``closing_time`` (str): Godzina zamknięcia (format: HH:MM).\n
    - ``price_per_kwh`` (float): Cena za kWh (musi być większa niż 0).\n
    - ``status`` (str, opcjonalnie): Status stacji (domyślnie "active", dozwolone wartości: "active", "inactive", "maintenance").\n
    - ``image`` (plik, opcjonalnie): Zdjęcie stacji.

    Zwraca:\n
    - ``201`` **Created**: Jeśli stacja została pomyślnie utworzona, zwraca ID stacji i wiadomość potwierdzającą.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił nieoczekiwany błąd podczas tworzenia stacji.
    """

    stations_service: StationService = StationService()

    try:
        station_image = request.files.get('image')
        data = request.form.get("data")
        if not data:
            return jsonify({"error": "Nie przesłano żadnych danych"}), 400

        data = json.loads(data)

        required_fields: list[str] = ["name", "lat", "lng", "address", "opening_time", "closing_time", "price_per_kwh"]

        if not all(field in data and data[field] is not None for field in required_fields):
            return jsonify({
                "error": f"Nieprawidłowe dane. Wymagane pola nie mogą być puste: {', '.join(required_fields)}"
            }), 400

        if not isinstance(data["name"], str) or len(data["name"].strip()) < 3:
            return jsonify({
                "error": "Nazwa stacji musi mieć co najmniej 3 znaki"
            }), 400

        try:
            lat: float = float(data["lat"])
            if not (-90 <= lat <= 90):
                return jsonify({
                    "error": "Szerokość geograficzna musi być w zakresie od -90 do 90 stopni"
                }), 400
        except ValueError:
            return jsonify({
                "error": "Nieprawidłowy format szerokości geograficznej"
            }), 400

        try:
            lng: float = float(data["lng"])
            if not (-180 <= lng <= 180):
                return jsonify({
                    "error": "Długość geograficzna musi być w zakresie od -180 do 180 stopni"
                }), 400
        except ValueError:
            return jsonify({
                "error": "Nieprawidłowy format długości geograficznej"
            }), 400

        if not isinstance(data["address"], str) or len(data["address"].strip()) < 5:
            return jsonify({
                "error": "Adres musi mieć co najmniej 5 znaków"
            }), 400

        status: str = "active"
        if "status" in data and data["status"] is not None:
            valid_statuses: list[str] = ["active", "inactive", "maintenance"]
            if data["status"].strip().lower() not in valid_statuses:
                return jsonify({
                    "error": f"Nieprawidłowy status. Dozwolone wartości: {', '.join(valid_statuses)}"
                }), 400
            status = data["status"].strip().lower()

        try:
            try:
                opening_time: time = stations_service.parse_time(data["opening_time"])
                closing_time: time = stations_service.parse_time(data["closing_time"])
            except ValueError as e:
                return jsonify({"error": str(e)}), 400

            if opening_time == closing_time:
                return jsonify({
                    "error": "Godzina otwarcia nie może być taka sama jak godzina zamknięcia"
                }), 400

        except ValueError:
            return jsonify({
                "error": "Nieprawidłowy format godziny (wymagany format: HH:MM)"
            }), 400

        try:
            price: float = float(data["price_per_kwh"])
            if price <= 0:
                return jsonify({
                    "error": "Cena za kWh musi być większa niż 0"
                }), 400
        except ValueError:
            return jsonify({
                "error": "Nieprawidłowy format ceny"
            }), 400

        station: Station = stations_service.create(
            name=data["name"].strip(),
            lat=float(data["lat"]),
            lng=float(data["lng"]),
            address=data["address"].strip(),
            status=status,
            opening_time=opening_time,
            closing_time=closing_time,
            price_per_kwh=price,
            image_file=station_image
        )

        return jsonify({
            "id": station.id,
            "message": "Stacja została utworzona pomyślnie"
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(e)
        return jsonify({"error": "Wystąpił nieoczekiwany błąd podczas tworzenia stacji"}), 500
