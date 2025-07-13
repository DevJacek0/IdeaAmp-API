from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required

from app.models.port import Port
from app.models.station import Station
from app.routes.decorators.adminRequired import admin_required
from app.services import StationService
from app.services.portService import PortService

create_ports_blueprint: Blueprint = Blueprint("create_ports", __name__)


@create_ports_blueprint.route("/stations/<int:station_id>/ports/create", methods=["POST"])
@jwt_required()
@admin_required
def create_port(station_id) -> tuple[Response, int]:
    """
    Tworzy nowy port.

    Metoda: ``POST``\n
    Url zapytania: ``/stations/<station-id>/ports/create``

    Obsługuje żądania POST do tworzenia nowego portu na podstawie ID stacji. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``station_id`` (int): ID stacji, do której należy port.

    Dane żądania:\n
    - ``max_power`` (float): Maksymalna moc portu.\n
    - ``connector_type`` (str): Typ złącza portu.\n
    - ``status`` (str, opcjonalnie): Status portu (domyślnie "available").

    Zwraca:\n
    - ``201`` **Created**: Jeśli port został pomyślnie utworzony, zwraca szczegóły portu.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    ports_service: PortService = PortService()
    stations_service: StationService = StationService()

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Nie przesłano żadnych danych"}), 400

        required_fields: list[str] = ["max_power", "connector_type"]
        if not all(field in data and data[field] is not None for field in required_fields):
            return jsonify({
                "error": f"Nieprawidłowe dane. Wymagane pola nie mogą być puste: {', '.join(required_fields)}"
            }), 400

        station: Station = stations_service.get(station_id)
        if not station:
            return jsonify({"error": "Nie znaleziono stacji o podanym ID"}), 404

        try:
            max_power: float = float(data["max_power"])
            if max_power <= 0:
                return jsonify({
                    "error": "Maksymalna moc musi być większa niż 0"
                }), 400
        except ValueError:
            return jsonify({
                "error": "Nieprawidłowy format mocy"
            }), 400

        valid_types: list[str] = ["Type1", "Type2", "CCS", "CHAdeMO", "Tesla NACS"]
        connector_type: str = data["connector_type"]
        if connector_type not in valid_types:
            return jsonify({
                "error": f"Nieprawidłowy typ złącza. Dozwolone wartości: {', '.join(valid_types)}"
            }), 400

        status: str = "available"
        if "status" in data and data["status"] is not None:
            valid_statuses: list[str] = ["available", "inuse", "faulty", "maintenance"]
            status = data["status"].lower()
            if status not in valid_statuses:
                return jsonify({
                    "error": f"Nieprawidłowy status. Dozwolone wartości: {', '.join(valid_statuses)}"
                }), 400

        port: Port = ports_service.create(
            station_id=station_id,
            max_power=max_power,
            connector_type=connector_type,
            status=("InUse" if status.lower() == "inuse" else status.capitalize())
        )

        return jsonify({
            "id": port.id,
            "message": "Port został utworzony pomyślnie"
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(e)
        return jsonify({"error": "Wystąpił nieoczekiwany błąd podczas tworzenia portu"}), 500
