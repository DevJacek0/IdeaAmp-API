from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required

from app.models.port import Port
from app.routes.decorators.adminRequired import admin_required
from app.services.portService import PortService

update_ports_blueprint: Blueprint = Blueprint("update_ports", __name__)


@update_ports_blueprint.route("/ports/update/<int:port_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_port(port_id) -> tuple[Response, int]:
    """
    Aktualizuje dane portu na podstawie ID.

    Metoda: ``PUT``\n
    Url zapytania: ``/ports/update/<port-id>``

    Obsługuje żądania PUT do aktualizacji danych portu na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``port_id`` (int): ID portu do aktualizacji.

    Wymagane dane:\n
    - ``max_power`` (float): Maksymalna moc portu.\n
    - ``connector_type`` (str): Typ złącza portu. Dozwolone wartości: "Type1", "Type2", "CCS", "CHAdeMO", "Tesla NACS".\n
    - ``status`` (str): Status portu. Dozwolone wartości: "available", "inuse", "faulty", "maintenance".

    Zwraca:\n
    - ``200`` **OK**: Jeśli dane portu zostały pomyślnie zaktualizowane.\n
    - ``400`` **Bad Request**: Jeśli brakuje wymaganych danych lub dane są nieprawidłowe.\n
    - ``404`` **Not Found**: Jeśli port nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    ports_service: PortService = PortService()

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Nie przesłano żadnych danych"}), 400

        port: Port = ports_service.get(port_id)
        if not port:
            return jsonify({"error": "Port nie został znaleziony"}), 404

        allowed_fields: set[str] = {
            "max_power", "connector_type", "status"
        }

        update_fields: set[str] = set(data.keys()) & allowed_fields
        if not update_fields:
            return jsonify({"error": "Brak prawidłowych pól do aktualizacji"}), 400

        if "max_power" in data:
            try:
                max_power: float = float(data["max_power"])
                if max_power <= 0:
                    return jsonify({"error": "Maksymalna moc musi być większa niż 0"}), 400
            except ValueError:
                return jsonify({"error": "Nieprawidłowy format mocy"}), 400

        if "connector_type" in data:
            valid_types: list[str] = ["Type1", "Type2", "CCS", "CHAdeMO", "Tesla NACS"]
            connector_type: str = data["connector_type"]
            if connector_type not in valid_types:
                return jsonify({
                    "error": f"Nieprawidłowy typ złącza. Dozwolone wartości: {', '.join(valid_types)}"
                }), 400

        if "status" in data:
            valid_statuses: list[str] = ["available", "inuse", "faulty", "maintenance"]
            status: str = data["status"].lower()
            if status not in valid_statuses:
                return jsonify({
                    "error": f"Nieprawidłowy status. Dozwolone wartości: {', '.join(valid_statuses)}"
                }), 400

            data["status"] = "InUse" if status.lower() == "inuse" else status.capitalize()

        updated_port: Port = ports_service.update(port_id, **data)
        if not updated_port:
            return jsonify({"error": "Nie udało się zaktualizować portu"}), 400

        return jsonify(updated_port.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@update_ports_blueprint.route("/ports/<int:port_id>/status", methods=["PATCH"])
@jwt_required()
@admin_required
def update_port_status(port_id) -> tuple[Response, int]:
    """
    Aktualizuje status portu.

    Metoda: ``PATCH``\n
    Url zapytania: ``/ports/<port-id>/status``

    Obsługuje żądania PATCH do aktualizacji statusu portu na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``port_id`` (int): ID portu do aktualizacji.

    Dane żądania:\n
    - ``status`` (str): Nowy status portu. Dozwolone wartości: "available", "inuse", "faulty", "maintenance".

    Zwraca:\n
    - ``200`` **OK**: Jeśli status portu został pomyślnie zaktualizowany, zwraca wiadomość potwierdzającą.\n
    - ``400`` **Bad Request**: Jeśli dane żądania są niepoprawne.\n
    - ``404`` **Not Found**: Jeśli port nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił nieoczekiwany błąd podczas aktualizacji statusu.
    """

    ports_service: PortService = PortService()

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Nie przesłano żadnych danych"}), 400

        if "status" not in data or data["status"] is None:
            return jsonify({"error": "Status jest wymagany"}), 400

        valid_statuses: list[str] = ["available", "inuse", "faulty", "maintenance"]
        status: str = data["status"].lower()
        if status not in valid_statuses:
            return jsonify({
                "error": f"Nieprawidłowy status. Dozwolone wartości: {', '.join(valid_statuses)}"
            }), 400

        status = "InUse" if status.lower() == "inuse" else status.capitalize()

        port: Port = ports_service.update_status(port_id, status)
        if not port:
            return jsonify({"error": "Port nie został znaleziony"}), 404

        return jsonify({"message": "Status portu został zaktualizowany pomyślnie"}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": "Wystąpił nieoczekiwany błąd podczas aktualizacji statusu"}), 500
