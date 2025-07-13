from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required

from app.models.port import Port
from app.services.portService import PortService

gets_ports_blueprint: Blueprint = Blueprint("gets_ports", __name__)


@gets_ports_blueprint.route("/stations/<int:station_id>/ports", methods=["GET"])
def get_station_ports(station_id) -> tuple[Response, int]:
    """
    Pobiera porty stacji.

    Metoda: ``GET``\n
    Url zapytania: ``/stations/<station-id>/ports``

    Obsługuje żądania GET do pobrania portów na podstawie ID stacji. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``station_id`` (int): ID stacji, której porty mają zostać pobrane.

    Parametry zapytania:\n
    - ``status`` (str, opcjonalnie): Status portu ("available", "inuse", "faulty", "maintenance").\n
    - ``connector_type`` (str, opcjonalnie): Typ złącza portu ("type1", "type2", "ccs", "chademo", "tesla_nacs").

    Zwraca:\n
    - ``200`` **OK**: Lista portów w formacie JSON.\n
    - ``400`` **Bad Request**: Jeśli parametry zapytania są niepoprawne.\n
    - ``404`` **Not Found**: Jeśli stacja nie została znaleziona.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    ports_service: PortService = PortService()

    try:
        status: str = request.args.get('status')
        connector_type: str = request.args.get('connector_type')

        ports: list[Port] = ports_service.get_by_station(station_id)
        if ports is None:
            return jsonify({"error": "Stacja nie została znaleziona"}), 404

        if status:
            valid_statuses: list[str] = ["available", "inuse", "faulty", "maintenance"]
            status = status.lower()
            if status not in valid_statuses:
                return jsonify({
                    "error": f"Nieprawidłowy status. Dozwolone wartości: {', '.join(valid_statuses)}"
                }), 400
            ports = [p for p in ports if p.status.lower() == status]

        if connector_type:
            valid_types: list[str] = ["type1", "type2", "ccs", "chademo", "tesla_nacs"]
            connector_type = connector_type.lower()
            if connector_type not in valid_types:
                return jsonify({
                    "error": f"Nieprawidłowy typ złącza. Dozwolone wartości: {', '.join(valid_types)}"
                }), 400
            ports = [p for p in ports if p.connector_type.lower() == connector_type]

        return jsonify({
            "items": [
                {
                    "id": port.id,
                    "station_id": port.station_id,
                    "max_power": float(port.max_power),
                    "connector_type": port.connector_type.lower(),
                    "status": port.status.lower()
                }
                for port in ports
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gets_ports_blueprint.route("/ports/<int:port_id>", methods=["GET"])
def get_port(port_id) -> tuple[Response, int]:
    """
    Pobiera szczegóły portu.

    Metoda: ``GET``\n
    Url zapytania: ``/ports/<port-id>``

    Obsługuje żądania GET do pobrania szczegółów portu na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``port_id`` (int): ID portu do pobrania.

    Zwraca:\n
    - ``200`` **OK**: Szczegóły portu w formacie JSON.\n
    - ``404`` **Not Found**: Jeśli port nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    ports_service: PortService = PortService()

    try:
        port: Port = ports_service.get(port_id)
        if not port:
            return jsonify({"error": "Port nie został znaleziony"}), 404

        return jsonify({
            "id": port.id,
            "station_id": port.station_id,
            "max_power": float(port.max_power),
            "connector_type": port.connector_type,
            "status": port.status
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
