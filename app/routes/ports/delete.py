from flask import Blueprint, jsonify, Response
from flask_jwt_extended import jwt_required
from app.routes.decorators.adminRequired import admin_required
from app.services.portService import PortService

delete_ports_blueprint: Blueprint = Blueprint("delete_ports", __name__)


@delete_ports_blueprint.route("/ports/<int:port_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_port(port_id) -> tuple[Response, int]:
    """
    Usuwa port.

    Metoda: ``DELETE``\n
    Url zapytania: ``/ports/<port-id>``

    Obsługuje żądania DELETE do usunięcia portu na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``port_id`` (int): ID portu do usunięcia.

    Zwraca:\n
    - ``200`` **OK**: Jeśli port został pomyślnie usunięty, zwraca wiadomość potwierdzającą.\n
    - ``404`` **Not Found**: Jeśli port nie został znaleziony.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił nieoczekiwany błąd podczas usuwania portu.
    """

    ports_service: PortService = PortService()

    try:
        if not ports_service.delete(port_id):
            return jsonify({"error": "Port nie został znaleziony"}), 404

        return jsonify({"message": "Port został usunięty pomyślnie"}), 200
    except Exception as e:
        return jsonify({"error": f"Wystąpił nieoczekiwany błąd podczas usuwania portu: {str(e)}"}), 500
