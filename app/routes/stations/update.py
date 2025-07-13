from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required
from datetime import datetime

from app.models.station import Station
from app.routes.decorators.adminRequired import admin_required
from app.services import AuditLogsService
from app.services.stationService import StationService
import json

update_stations_blueprint = Blueprint("update_stations", __name__, url_prefix="/stations")


@update_stations_blueprint.route("/update/<int:station_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_station(station_id) -> tuple[Response, int]:
    """
    Aktualizuje stację na podstawie ID.

    Metoda: ``PUT``\n
    Url zapytania: ``/stations/update/<station-id>``

    Obsługuje żądania PUT do aktualizacji stacji na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``station_id`` (int): ID stacji do aktualizacji.

    Wymagane dane:\n
    - ``name`` (str, opcjonalnie): Nazwa stacji.\n
    - ``lat`` (float, opcjonalnie): Szerokość geograficzna.\n
    - ``lng`` (float, opcjonalnie): Długość geograficzna.\n
    - ``address`` (str, opcjonalnie): Adres stacji.\n
    - ``status`` (str, opcjonalnie): Status stacji (dozwolone wartości: "active", "inactive", "maintenance").\n
    - ``opening_time`` (str, opcjonalnie): Godzina otwarcia (format: HH:MM).\n
    - ``closing_time`` (str, opcjonalnie): Godzina zamknięcia (format: HH:MM).\n
    - ``price_per_kwh`` (float, opcjonalnie): Cena za kWh (musi być większa niż 0).

    Zwraca:\n
    - ``200`` **OK**: Jeśli stacja została pomyślnie zaktua lizowana, zwraca szczegóły stacji.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``404`` **Not Found**: Jeśli stacja nie została znaleziona.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił nieoczekiwany błąd podczas aktualizacji stacji.
    """

    stations_service: StationService = StationService()
    audit_logs_service: AuditLogsService = AuditLogsService()

    try:
        station: Station = stations_service.get(station_id)
        if not station:
            return jsonify({"error": "Stacja nie została znaleziona"}), 404

        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"error": "Niepoprawny format danych"}), 400

        allowed_fields: set[str] = {
            "name", "lat", "lng", "address", "status", 
            "opening_time", "closing_time", "price_per_kwh"
        }

        update_fields: set[str] = set(data.keys()) & allowed_fields
        if not update_fields:
            return jsonify({"error": "Brak prawidłowych pól do aktualizacji"}), 400

        if "price_per_kwh" in data:
            try:
                price: float = float(data["price_per_kwh"])
                if price <= 0:
                    return jsonify({"error": "Cena za kWh musi być większa niż 0"}), 400
            except ValueError:
                return jsonify({"error": "Nieprawidłowy format ceny"}), 400

        if "status" in data:
            valid_statuses: list[str] = ["active", "inactive", "maintenance"]
            if data["status"] not in valid_statuses:
                return jsonify({
                    "error": f"Nieprawidłowy status. Dozwolone wartości: {', '.join(valid_statuses)}"
                }), 400

            if data["status"] == "maintenance" or "inactive":
                audit_logs_service.log_station_failure(station_id)

        if "opening_time" in data or "closing_time" in data:
            try:
                if "opening_time" in data:
                    data["opening_time"] = datetime.strptime(data["opening_time"], "%H:%M")
                if "closing_time" in data:
                    data["closing_time"] = datetime.strptime(data["closing_time"], "%H:%M")
            except ValueError:
                return jsonify({"error": "Nieprawidłowy format godziny"}), 400

        updated_station: Station = stations_service.update_station(station_id, **data)
        if not updated_station:
            return jsonify({"error": "Nie udało się zaktualizować stacji"}), 400

        return jsonify(updated_station.to_dict()), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@update_stations_blueprint.route("/<int:station_id>/status", methods=["PATCH"])
@jwt_required()
@admin_required
def update_station_status(station_id) -> tuple[Response, int]:
    """
    Aktualizuje status stacji na podstawie ID.

    Metoda: ``PATCH``\n
    Url zapytania: ``/stations/<station-id>/status``

    Obsługuje żądania PATCH do aktualizacji statusu stacji na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``station_id`` (int): ID stacji do aktualizacji.

    Wymagane dane:\n
    - ``status`` (str): Nowy status stacji (dozwolone wartości: "active", "inactive", "maintenance").

    Zwraca:\n
    - ``200`` **OK**: Jeśli status stacji został pomyślnie zaktualizowany.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``404`` **Not Found**: Jeśli stacja nie została znaleziona.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił nieoczekiwany błąd podczas aktualizacji statusu stacji.
    """

    stations_service: StationService = StationService()
    audit_logs_service: AuditLogsService = AuditLogsService()

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Nie przesłano żadnych danych"}), 400

        if "status" not in data or data["status"] is None:
            return jsonify({"error": "Status jest wymagany"}), 400

        valid_statuses: list[str] = ["active", "inactive", "maintenance"]
        new_status: str = data["status"].strip().lower()
        if new_status not in valid_statuses:
            return jsonify({
                "error": f"Nieprawidłowy status. Dozwolone wartości: {', '.join(valid_statuses)}"
            }), 400

        station: Station = stations_service.get(station_id)
        if not station:
            return jsonify({"error": "Stacja nie została znaleziona"}), 404

        updated_station: Station = stations_service.update_status(station_id, new_status)
        if not updated_station:
            return jsonify({"error": "Nie udało się zaktualizować statusu stacji"}), 400

        if new_status == "inactive" or "maintenance":
            audit_logs_service.log_station_failure(station_id)

        return jsonify({"message": "Status stacji został zaktualizowany pomyślnie"}), 200
    except Exception as e:
        return jsonify({"error": f"Wystąpił nieoczekiwany błąd podczas aktualizacji statusu: {str(e)}"}), 500


@update_stations_blueprint.route("/<int:station_id>/price", methods=["PATCH"])
@jwt_required()
@admin_required
def update_station_price(station_id) -> tuple[Response, int]:
    """
    Aktualizuje cenę za kWh stacji na podstawie ID.

    Metoda: ``PATCH``\n
    Url zapytania: ``/stations/<station-id>/price``

    Obsługuje żądania PATCH do aktualizacji ceny za kWh stacji na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``station_id`` (int): ID stacji do aktualizacji.

    Wymagane dane:\n
    - ``pricePerKWh`` (float): Nowa cena za kWh (musi być większa niż 0).

    Zwraca:\n
    - ``200`` **OK**: Jeśli cena za kWh została pomyślnie zaktualizowana.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``404`` **Not Found**: Jeśli stacja nie została znaleziona.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił nieoczekiwany błąd podczas aktualizacji ceny za kWh.
    """

    stations_service: StationService = StationService()

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Nie przesłano żadnych danych"}), 400

        if "pricePerKWh" not in data or data["pricePerKWh"] is None:
            return jsonify({"error": "Cena jest wymagana"}), 400

        try:
            price: float = float(data["pricePerKWh"])
            if price <= 0:
                return jsonify({
                    "error": "Cena za kWh musi być większa niż 0"
                }), 400
        except ValueError:
            return jsonify({
                "error": "Nieprawidłowy format ceny"
            }), 400

        station: Station = stations_service.update_price(station_id, price)
        if not station:
            return jsonify({"error": "Stacja nie została znaleziona"}), 404

        return jsonify({"message": "Cena została zaktualizowana pomyślnie"}), 200
    except ValueError:
        return jsonify({"error": "Nieprawidłowy format ceny"}), 400
    except Exception as e:
        return jsonify({"error": f"Wystąpił nieoczekiwany błąd podczas aktualizacji ceny: {str(e)}"}), 500


@update_stations_blueprint.route("/<int:station_id>/send-ad", methods=["PUT"])
def send_ad(station_id) -> tuple[Response, int]:
    """
    Wysyła reklamę do stacji na podstawie ID.

    Metoda: ``PUT``\n
    Url zapytania: ``/stations/<station-id>/send-ad``

    Obsługuje żądania PUT do wysyłania reklamy do stacji na podstawie ID.

    Parametry:\n
    - ``station_id`` (int): ID stacji do aktualizacji.

    Wymagane dane:\n
    - ``ad`` (file): image .png

    Zwraca:\n
    - ``200`` **OK**: Jeśli reklama została pomyślnie wysłana.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``404`` **Not Found**: Jeśli stacja nie została znaleziona.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił nieoczekiwany błąd podczas wysyłania reklamy.
    """

    stations_service: StationService = StationService()

    try:
        station_image = request.files.get('file')

        station: Station = stations_service.get(station_id)
        if not station:
            return jsonify({"error": "Stacja nie została znaleziona"}), 404

        if not station_image:
            return jsonify({"error": "Nie przesłano żadnych danych"}), 400
        if not station_image.filename.endswith('.png'):
            return jsonify({"error": "Nieprawidłowy format pliku. Wymagany format: .png"}), 400
        if station_image and station_image.filename:
            station_image.save(f"app/attachments/uploads/stations/{station_id}.png")



        return jsonify({"message": "Reklama została wysłana pomyślnie"}), 200
    except Exception as e:
        return jsonify({"error": f"Wystąpił nieoczekiwany błąd podczas wysyłania reklamy: {str(e)}"}), 500