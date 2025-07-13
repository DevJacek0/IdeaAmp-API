import os

from flask import Blueprint, jsonify, request, Response, send_file
from flask_jwt_extended import jwt_required
from datetime import datetime, time

from werkzeug.utils import send_file

from app.models.station import Station
from app.routes.decorators.pagination import paginate
from app.services.attachmentService import AttachmentsService
from app.services.stationService import StationService

gets_stations_blueprint: Blueprint = Blueprint("gets_stations", __name__, url_prefix="/stations")


@gets_stations_blueprint.route("/get-all", methods=["GET"])
@jwt_required()
@paginate
def get_stations() -> tuple[Response, int] | list[dict[str, int | str | float | None]]:
    """
    Pobiera wszystkie stacje.

    Metoda: ``GET``\n
    Url zapytania: ``/stations/get-all``

    Obsługuje żądania GET do pobrania wszystkich stacji. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry opcjonalne:\n
    - ``status`` (str): Status stacji (np. "active", "inactive", "maintenance").\n
    - ``lat`` (float): Szerokość geograficzna do filtrowania stacji w promieniu.\n
    - ``lng`` (float): Długość geograficzna do filtrowania stacji w promieniu.\n
    - ``radius`` (float): Promień w kilometrach do filtrowania stacji.\n
    - ``price_per_kwh`` (float): Maksymalna cena za kWh.\n
    - ``open_now`` (bool): Filtruje stacje, które są obecnie otwarte.

    Zwraca:\n
    - ``200`` **OK**: Lista stacji w formacie JSON.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    stations_service: StationService = StationService()

    try:
        status: str = request.args.get('status')
        lat: float = request.args.get('lat', type=float)
        lng: float = request.args.get('lng', type=float)
        radius: float = request.args.get('radius', type=float)
        price_per_kwh: float = request.args.get('price_per_kwh', type=float)
        open_now: bool = request.args.get('open_now', '').lower() == 'true'

        stations: list[Station] = stations_service.get_all()

        if status:
            stations = [s for s in stations if s.status == status]
        if price_per_kwh is not None:
            stations = [s for s in stations if float(s.price_per_kwh) <= price_per_kwh]
        if lat and lng and radius:
            stations = [s for s in stations if
                        stations_service.is_within_radius(lat, lng, float(s.lat), float(s.lng), radius)]
        if open_now:
            current_time: time = datetime.now().time()
            stations = [s for s in stations if parse_time(s.opening_time) <= current_time <= parse_time(s.closing_time)]

        return [
            {
                "id": station.id,
                "name": station.name,
                "lat": float(station.lat),
                "lng": float(station.lng),
                "address": station.address,
                "image_url": station.image_url,
                "status": station.status,
                "opening_time": parse_time(station.opening_time).strftime('%H:%M') if parse_time(
                    station.opening_time) else None,
                "closing_time": parse_time(station.closing_time).strftime('%H:%M') if parse_time(
                    station.closing_time) else None,
                "price_per_kwh": float(station.price_per_kwh)
            }
            for station in stations
        ]

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gets_stations_blueprint.route("/get/<int:station_id>", methods=["GET"])
def get_station(station_id) -> tuple[Response, int]:
    """
    Pobiera stację na podstawie ID.

    Metoda: ``GET``\n
    Url zapytania: ``/stations/get/<station-id>``

    Obsługuje żądania GET do pobrania stacji na podstawie ID. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``station_id`` (int): ID stacji do pobrania.

    Zwraca:\n
    - ``200`` **OK**: Szczegóły stacji w formacie JSON.\n
    - ``404`` **Not Found**: Jeśli stacja nie została znaleziona.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    stations_service: StationService = StationService()

    try:
        station: Station = stations_service.get(station_id)
        if not station:
            return jsonify({"error": "Stacja nie została znaleziona"}), 404

        return jsonify({
            "id": station.id,
            "name": station.name,
            "lat": float(station.lat),
            "lng": float(station.lng),
            "address": station.address,
            "image_url": station.image_url,
            "status": station.status,
            "opening_time": parse_time(station.opening_time).strftime('%H:%M') if parse_time(
                station.opening_time) else None,
            "closing_time": parse_time(station.closing_time).strftime('%H:%M') if parse_time(
                station.closing_time) else None,
            "price_per_kwh": float(station.price_per_kwh),
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@gets_stations_blueprint.route("/get-image/<int:station_id>", methods=["GET"])
def get_station_image(station_id):
    """
    Pobiera obraz stacji.

    Metoda: ``GET``\n
    Url zapytania: ``/stations/get-image``

    Obsługuje żądania GET do pobrania obrazu stacji. Użytkownik musi być uwierzytelniony za pomocą JWT.

    Parametry:\n
    - ``station_id`` (int): ID stacji do pobrania obrazu.

    Zwraca:\n
    - ``200`` **OK**: Obraz stacji w formacie png.\n
    - ``404`` **Not Found**: Jeśli stacja nie została znaleziona.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    stations_service: StationService = StationService()
    attachments_service: AttachmentsService = AttachmentsService()

    try:
        station: Station = stations_service.get(station_id)
        if not station:
            return jsonify({"error": "Stacja nie została znaleziona"}), 404

        file_path = f"./app/attachments/uploads/stations/{station.id}.png"
        if not os.path.exists(file_path):
            return jsonify({"error": "Obraz stacji nie istnieje"}), 404

        full_path = os.path.abspath(file_path)
        print(attachments_service.get_file_path(full_path))
        base_url = "http://192.168.0.103:5000/attachments/uploads/stations/"
        image_url = f"{base_url}{station.id}.png"

        return jsonify({
            "image_url": image_url
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def parse_time(time_value: str | time) -> time | None:
    """
    Konwertuje ciąg znaków reprezentujący czas w formacie ``HH:MM`` na obiekt ``datetime.time``. Jeśli wejście jest już
    obiektem ``time``, zwraca go bez zmian. Jeśli ciąg znaków nie może zostać przetworzony, zwraca ``None``.

    Parametry:\n
    - ``time_value`` (str | time): Wartość czasu do sparsowania.

    Zwraca:\n
    - ``time``: Obiekt czasu, jeśli parsowanie się powiedzie.\n
    - ``None``: Jeśli parsowanie się nie powiedzie.
    """

    if isinstance(time_value, str):
        try:
            return datetime.strptime(time_value, '%H:%M').time()
        except ValueError:
            return None
    return time_value

