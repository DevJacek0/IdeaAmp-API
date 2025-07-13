import datetime
from datetime import time
import time

from flask import Blueprint, jsonify, request, Response

from app.models.port import Port
from app.models.station import Station
from app.services.service import Service
from app.services import PortService, ChargingSessionsService, StationService

station_chargings_blueprint: Blueprint = Blueprint('station_api', __name__, url_prefix="/station")


@station_chargings_blueprint.route('/scan-qr', methods=['POST'])
def scan_qr() -> tuple[Response, int]:
    """
    Skanuje kod QR.

    Metoda: ``POST``\n
    Url zapytania: ``/station/scan-qr``

    Obsługuje żądania POST do skanowania kodu QR. Wymagane jest podanie tokenu QR, ID stacji oraz ID portu
    w treści żądania. Funkcja ta jest przeznaczona wyłącznie do celów symulacyjnych, ponieważ podobny kod
    znajdowałby się w samej stacji ładowania.

    Parametry żądania:\n
    - ``qr_token`` (str): Token QR do zeskanowania.\n
    - ``station_id`` (int): ID stacji.\n
    - ``ip_address`` (str): Adres IP stacji.\n

    Zwraca:\n
    - ``200`` **OK**: Wiadomość wskazująca, że kod QR został pomyślnie zeskanowany, wraz z ID użytkownika.\n
    - ``400`` **Bad Request**: Jeśli brakuje wymaganych danych, kod QR jest nieważny lub przeterminowany, lub port jest zajęty.\n
    - ``404`` **Not Found**: Jeśli nie znaleziono portu lub stacji.\n
    - ``500`` **Internal Server Error**: Jeśli wystąpił błąd serwera.
    """

    data = request.get_json()

    if not all([
        data.get('qr_token'),
        data.get('station_id'),
        # data.get('port_id')
    ]):
        return jsonify({
            'error': 'Brak wymaganych danych'
        }), 400

    try:
        qr_token: str = data['qr_token']
        station_id: int = data['station_id']
        ip_address: str = data['ip_address']
        # port_id: int = data['port_id']

        cache_key: str = f"qr_token:{qr_token}"
        qr_data = Service.cache_get(cache_key)

        if not qr_data or time.time() > qr_data.get("expiration", 0):
            return jsonify({
                'error': 'Nieważny lub przeterminowany kod QR: %s' % qr_data
            }), 400

        port_service: PortService = PortService()
        # port: Port = port_service.get(int(port_id))
        station_service: StationService = StationService()
        station: Station = station_service.get(int(station_id))

        # if not port:
        #     return jsonify({
        #         'error': 'Nie znaleziono portu'
        #     }), 404

        if not station:
            return jsonify({
                'error': 'Nie znaleziono stacji'
            }), 404

        # if not station.opening_time < datetime.datetime.now().time() < (station.closing_time if station.closing_time != 0 else 24):
        #     return jsonify({
        #         'error': 'Stacja jest obecnie zamknięta'
        #     }), 400

        # if port.status != 'Available':
        #     return jsonify({
        #         'error': 'Port jest obecnie zajęty'
        #     }), 400

        qr_data["station_data"] = {
            'station_id': station_id,
            # 'port_id': port_id,
            # 'max_power': float(port.max_power),
            # 'connector_type': port.connector_type,
            'price_per_kwh': float(station.price_per_kwh),
            'ip_address': ip_address,
        }
        Service.cache_set(cache_key, qr_data)
        Service.cache_set(f"station{station.id}ip", ip_address)

        return jsonify({
            'message': 'Kod QR zeskanowany pomyślnie',
            'user_id': qr_data['user_id']
        }), 200

    except Exception as e:
        print(f"Błąd podczas skanowania kodu QR: {str(e)}")
        return jsonify({
            'error': 'Wystąpił błąd podczas skanowania kodu QR'
        }), 500