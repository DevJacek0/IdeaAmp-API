from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.models.station import Station
from app.routes.decorators.adminRequired import admin_required
from app.services.stationService import StationService

delete_stations_blueprint: Blueprint = Blueprint("delete_stations", __name__, url_prefix="/stations")


@delete_stations_blueprint.route("/delete/<int:station_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_station(station_id):
    """
    Usuwa stację.

    Metoda: ``DELETE``\n
    Url zapytania: ``/stations/delete/<station_id>``

    Obsługuje żądania DELETE do usunięcia stacji na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT
    i posiadać uprawnienia administratora.

    Parametry:\n
    - ``station_id`` (int): ID stacji do usunięcia.

    Zwraca:\n
    - ``200`` **OK**: Jeśli stacja została pomyślnie usunięta, zwraca wiadomość potwierdzającą.\n
    - ``404`` **Not Found**: Jeśli stacja nie została znaleziona.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił nieoczekiwany błąd podczas usuwania stacji.
    """

    stations_service: StationService = StationService()

    try:
        station: Station = stations_service.get(station_id)
        if not station:
            return jsonify({"error": "Stacja nie została znaleziona"}), 404

        if station.image_url:
            stations_service.delete_station_image(station.image_url)

        if not stations_service.delete(station_id):
            return jsonify({"error": "Stacja nie została znaleziona"}), 404
        return jsonify({"message": "Stacja została usunięta pomyślnie"}), 200
    except Exception as e:
        return jsonify({"error": f"Wystąpił nieoczekiwany błąd podczas usuwania stacji: {str(e)}"}), 500
