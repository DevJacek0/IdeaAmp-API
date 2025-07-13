import time
from decimal import Decimal
from json import JSONEncoder
from typing import Any

import aiohttp
import requests
from flask import Blueprint, request
from app import sock
from flask_jwt_extended import decode_token
import json
from datetime import datetime
from werkzeug.security import generate_password_hash

from app.models.car import Car
from app.models.user import User
from app.services import ports_service
from app.services.chargingSessionService import ChargingSessionsService
from app.services.userService import UsersService
from app.services.carService import CarsService
from app.services.portService import PortService
from app.services.service import Service


class DecimalEncoder(JSONEncoder):
    """
    Klasa pomocnicza do serializacji obiektów typu Decimal.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)


charging_socket_blueprint: Blueprint = Blueprint('charging_socket', __name__)


@sock.route('/ws/charging/<int:session_id>')
def charging_socket(ws, session_id):
    """
    Obsługuje połączenie WebSocket dla sesji ładowania.

    Obsługuje połączenie WebSocket dla sesji ładowania pojazdu elektrycznego. Wymaga uwierzytelnienia za pomocą JWT.

    Parametry:\n
    - ``session_id`` (int): ID sesji ładowania.

    Zwraca:\n
    - ``charging_started``: Informacje o rozpoczęciu ładowania.\n
    - ``charging_update``: Aktualizacje dotyczące stanu ładowania.\n
    - ``charging_completed``: Informacje o zakończeniu ładowania.\n
    - ``charging_interrupted``: Informacje o przerwaniu ładowania.\n
    - ``error``: Informacje o błędach.
    """

    global user_id
    try:
        token: str = request.args.get('token')
        if not token:
            ws.send(json.dumps({'type': 'error', 'message': 'Brak tokena JWT'}))
            return

        try:
            decoded_token = decode_token(token)
            user_id = int(decoded_token['sub'])
        except Exception as e:
            ws.send(json.dumps({'type': 'error', 'message': f'Błąd JWT: {str(e)}'}))
            return
    except Exception as e:
        print(e)

    charging_service: ChargingSessionsService = ChargingSessionsService()
    users_service: UsersService = UsersService()
    cars_service: CarsService = CarsService()

    session: dict[str, Any] = charging_service.get_session_status(session_id)

    if not session or session['user_id'] != user_id:
        ws.send(json.dumps({
            'type': 'error',
            'message': 'Brak dostępu do tej sesji ładowania'
        }))
        return

    car = cars_service.get(int(session['car_id']))
    if not car:
        ws.send(json.dumps({
            'type': 'error',
            'message': 'Nie znaleziono pojazdu'
        }))
        return

    import websocket
    rpi_address = None
    rpi_ws = None
    try:
        rpi_address = "192.168.0.104:3030"

        rpi_ws = websocket.create_connection(f"ws://{rpi_address}")

        rpi_ws.send(json.dumps({
            "type": "buzzer",
        }))

        if session['port_id'] == ports_service.get_by_station(session['station_id']):
            rid = 1
        else:
            rid = 2

        rpi_ws.send(json.dumps({
            "type": f"relay_{rid}", 'enable': False # zmiana na False
        }))


        print(f"Successfully connected RPI at {rpi_address}")
    except Exception as e:
        print(f"Failed to communicate with RPI WebSocket {rpi_address}: {str(e)}")

    current_kwh: float = 0
    current_cost: float = 0
    charging_power: float = min(float(session['max_power']), float(car.max_charging_power))
    battery_temp: float = 25.0
    status: str = "active"

    try:
        ws.send(json.dumps({
            'type': 'charging_started',
            'data': {
                'session_id': session_id,
                'max_power': charging_power,
                'target_kwh': session['target_kwh'],
                'price_per_kwh': session['price_per_kwh'],
                'battery_capacity': car.battery_capacity
            }
        }, cls=DecimalEncoder))

        while ws.connected:
            can_continue, interrupt_reason = charging_service.check_charging_availability(session_id)
            if not can_continue:
                if interrupt_reason == 'session_not_found':
                    break
                else:
                    charging_service.end_charging_session(
                        session_id=session_id,
                        final_energy=current_kwh,
                        final_cost=current_cost,
                        reason=interrupt_reason
                    )

                    ws.send(json.dumps({
                        'type': 'charging_interrupted',
                        'data': {
                            'session_id': session_id,
                            'final_energy': round(current_kwh, 2),
                            'final_cost': round(current_cost, 2),
                            'reason': interrupt_reason,
                            'battery_level': round(battery_level, 1) if 'battery_level' in locals() else 0
                        }
                    }, cls=DecimalEncoder))
                    break

            # rpi_mess = rpi_ws.recv()
            # rpi_data = json.loads(rpi_mess)
            time_delta: int = 1

            if session['port_id'] == ports_service.get_by_station(session['station_id']):
                pid = 1
            else:
                pid = 3

            url = f"http://192.168.0.104:8080/ina?type={pid}"

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    rpi_data = response.json()
                    energy_delta: float = rpi_data.get("kwh")
                    print(energy_delta)
                else:
                    print(f"Unexpected response status: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"Error fetching data from RPI: {str(e)}")

                # Fallback to a default value if the request fails
                # energy_delta: float = rpi_data.get("kwh")  # kWh
                # energy_delta: float = 1
            # energy_delta: float = rpi_data.get("kwh")  # kWh
            energy_delta: float = 1  # kWh

            current_kwh += energy_delta

            battery_temp += 0.1
            if battery_temp > 40:
                charging_power *= 0.9

            battery_capacity: float = float(car.battery_capacity)
            battery_level: float = min(100, (current_kwh / battery_capacity) * 100)

            price_per_kwh: float = float(session['price_per_kwh'])
            cost_delta: float = energy_delta * price_per_kwh
            current_cost += cost_delta

            ws.send(json.dumps({
                'type': 'charging_update',
                'data': {
                    'session_id': session_id,
                    'current_kwh': round(current_kwh, 2),
                    'charging_power': round(charging_power, 2),
                    'battery_level': round(battery_level, 1),
                    'battery_temp': round(battery_temp, 1),
                    'current_cost': round(current_cost, 2),
                    'target_kwh': session['target_kwh'],
                    'remaining_kwh': round(session['target_kwh'] - current_kwh, 2) if session['target_kwh'] else None,
                    'timestamp': int(datetime.utcnow().timestamp() * 1000)
                }
            }, cls=DecimalEncoder))

            status: str = "active"
            charging_service.update_charging_status(session_id, current_kwh, status, charging_power, current_cost)

            end_reason: str | None = None
            if battery_level >= 100:
                end_reason = "battery_full"
            elif current_kwh >= battery_capacity:
                end_reason = "capacity_reached"
            elif current_kwh >= (float(session['target_kwh']) - 0.01):
                end_reason = "target_reached"

            if end_reason:
                status = "done"
                charging_service.update_charging_status(
                    session_id=session_id,
                    current_kwh=current_kwh,
                    status=status,
                    current_cost=current_cost,
                    charging_power=charging_power
                )

                charging_service.end_charging_session(
                    session_id=session_id,
                    final_energy=current_kwh,
                    final_cost=current_cost,
                    reason=end_reason
                )

                ws.send(json.dumps({
                    'type': 'charging_completed',
                    'data': {
                        'session_id': session_id,
                        'final_energy': round(current_kwh, 2),
                        'final_cost': round(current_cost, 2),
                        'end_reason': end_reason,
                        'battery_level': round(battery_level, 1)
                    }
                }, cls=DecimalEncoder))
                break
            time.sleep(time_delta)

    except Exception as e:
        error_message: str = f"Błąd podczas ładowania: {str(e)}"
        print(error_message)
        ws.send(json.dumps({
            'type': 'error',
            'data': {
                'message': error_message,
                'session_id': session_id,
                'current_kwh': round(current_kwh, 2) if 'current_kwh' in locals() else 0,
                'current_cost': round(current_cost, 2) if 'current_cost' in locals() else 0
            }
        }, cls=DecimalEncoder))
    finally:
        if 'charging_service' in locals() and 'session_id' in locals():
            if 'current_kwh' not in locals():
                current_kwh = 0
            if 'current_cost' not in locals():
                current_cost = 0
            if 'status' not in locals():
                status = "interrupted"

            session_status: dict[str, Any] = charging_service.get_session_status(int(session_id))

            if session_status is None or session_status['charging_status'] in ['stopped', 'completed']:
                return
            else:
                charging_service.update_charging_status(session_id, current_kwh, "interrupted", charging_power,
                                                        current_cost)

                charging_service.end_charging_session(
                    session_id=session_id,
                    final_energy=current_kwh,
                    final_cost=current_cost,
                    reason="connection_lost"
                )

        if ws.connected:
            ws.close()
        rpi_ws.send(json.dumps({
            "status": "end",
        }))
        rpi_ws.close()


@sock.route('/ws/qr-waiting')
def qr_waiting_socket(ws):
    """
    Obsługuje połączenie WebSocket dla oczekiwania na kod QR.

    Obsługuje połączenie WebSocket dla oczekiwania na kod QR do rozpoczęcia sesji ładowania. Wymaga uwierzytelnienia za pomocą JWT.

    Zwraca:\n
    - ``qr_token``: Token QR do rozpoczęcia sesji ładowania.\n
    - ``station_connected``: Informacje o połączeniu ze stacją ładowania.\n
    - ``error``: Informacje o błędach.
    """

    try:
        token: str = request.args.get('token')
        if not token:
            ws.send(json.dumps({'type': 'error', 'message': 'Brak tokena JWT'}))
            return

        try:
            decoded_token: dict = decode_token(token)
            user_id = int(decoded_token['sub'])
        except Exception as e:
            ws.send(json.dumps({'type': 'error', 'message': f'Błąd JWT: {str(e)}'}))
            return

        qr_token: str = generate_password_hash(f"{user_id}_{time.time()}")[:32]
        cache_key: str = f"qr_token:{qr_token}"

        Service._global_cache[cache_key] = {
            "user_id": user_id,
            "expiration": time.time() + 300,  # 5 minut
            "websocket": ws
        }

        ws.send(json.dumps({
            'type': 'qr_token',
            'data': {
                'token': qr_token
            }
        }))

        while ws.connected:
            time.sleep(1)

            qr_data = Service._global_cache.get(cache_key)
            if not qr_data:
                ws.send(json.dumps({
                    'type': 'error',
                    'message': 'Sesja QR wygasła'
                }))
                break

            if time.time() > qr_data["expiration"]:
                Service._global_cache.pop(cache_key, None)
                ws.send(json.dumps({
                    'type': 'error',
                    'message': 'Kod QR wygasł'
                }))
                break

            if "station_data" in qr_data:
                station_data = qr_data["station_data"]
                cars_service = CarsService()
                user_cars = cars_service.get_by_owner(user_id)
                compatible_cars = [
                    car for car in user_cars
                ]

                if not compatible_cars:
                    ws.send(json.dumps({
                        'type': 'error',
                        'message': 'Nie znaleziono samochodów.'
                    }))
                    break

                station_data['available_cars'] = [{
                    'id': car.id,
                    'name': car.name,
                    'battery_capacity': float(car.battery_capacity),
                    'max_charging_power': float(car.max_charging_power)
                } for car in compatible_cars]

                ws.send(json.dumps({
                    'type': 'station_connected',
                    'data': station_data
                }))

                try:
                    confirmation = ws.receive()
                    if confirmation:
                        confirm_data = json.loads(confirmation)
                        if confirm_data.get('type') == 'confirm_connection':
                            return init_charging_process(ws, user_id, station_data)
                except Exception as e:
                    print(f"Błąd podczas potwierdzania połączenia: {str(e)}")
                break

    except Exception as e:
        print(f"Błąd w QR websocket: {str(e)}")
        if ws.connected:
            ws.send(json.dumps({
                'type': 'error',
                'message': f'Wystąpił błąd: {str(e)}'
            }))
    finally:
        if 'cache_key' in locals():
            Service._global_cache.pop(cache_key, None)
        if ws.connected:
            ws.close()




def init_charging_process(ws, user_id, station_data):
    """
    Inicjalizuje proces ładowania.

    Inicjalizuje proces ładowania pojazdu elektrycznego na podstawie danych stacji ładowania.

    Parametry:\n
    - ``ws``: Obiekt WebSocket.\n
    - ``user_id`` (int): ID użytkownika.\n
    - ``station_data`` (dict): Dane stacji ładowania.

    Zwraca:\n
    - ``charging_options``: Opcje ładowania dla użytkownika.\n
    - ``charging_initialized``: Informacje o zainicjalizowaniu sesji ładowania.\n
    - ``error``: Informacje o błędach.
    """

    try:
        users_service: UsersService = UsersService()
        cars_service: CarsService = CarsService()
        ports_service: PortService = PortService()

        user: User = users_service.get(int(user_id))
        if not user:
            ws.send(json.dumps({'type': 'error', 'message': 'Nie znaleziono użytkownika'}))
            return

        user_cars: list[Car] = cars_service.get_by_owner(int(user_id))
        compatible_cars: list[Car] = [
            car for car in user_cars
        ]

        if not compatible_cars:
            ws.send(json.dumps({
                'type': 'error',
                'message': 'Nie znaleziono kompatybilnych samochodów do tego portu ładowania.'
            }))
            return
        else:
            ws.send(json.dumps({
                'type': 'charging_options',
                'data': {
                    'user_info': {
                        'balance': float(user.balance),
                        'points': user.points
                    },
                    'available_cars': [{
                        'id': car.id,
                        'name': car.name,
                        'battery_capacity': float(car.battery_capacity),
                        'max_charging_power': float(car.max_charging_power)
                    } for car in compatible_cars],
                    'station_info': station_data,
                    'ports': [{
                        'port_id': port.id,
                        'max_power': float(port.max_power),
                        'connector_type': port.connector_type,
                        'status': port.status,
                    } for port in ports_service.get_by_station(station_data['station_id'])],
                }
            }))

        while ws.connected:
            message = ws.receive()
            if not message:
                continue

            data = json.loads(message)
            if data['type'] == 'start_charging':
                params = data['data']

                if not all([params.get('car_id'), params.get('target_kwh'), params.get('port_id')]):
                    ws.send(json.dumps({
                        'type': 'error',
                        'message': 'Brak wymaganych parametrów'
                    }))
                    continue

                charging_service: ChargingSessionsService = ChargingSessionsService()
                session: dict = charging_service.initialize_charging(
                    user_id=user_id,
                    port_id=int(params['port_id'])
                )

                if not session:
                    ws.send(json.dumps({
                        'type': 'error',
                        'message': 'Nie można zainicjalizować sesji ładowania'
                    }))
                    return

                success, estimated_cost, message = charging_service.start_charging(
                    session_id=session['session_id'],
                    user_id=user_id,
                    target_kwh=float(params['target_kwh']),
                    car_id=int(params['car_id']),
                    discount_code=params.get('discount_code')
                )

                if success:
                    ws.send(json.dumps({
                        'type': 'charging_initialized',
                        'data': {
                            'session_id': session['session_id'],
                            'redirect_to': f'/ws/charging/{session["session_id"]}'
                        }
                    }))


                    try:
                        import websocket
                        rpi_address = '192.168.0.104:3030'

                        rpi_ws = websocket.create_connection(f"ws://{rpi_address}")

                        rpi_ws.send(json.dumps({
                            "port": params['port_id'],
                        }))

                        rpi_ws.close()

                        print(f"Successfully sent message to RPI at {rpi_address}")
                    except Exception as e:
                        print(f"Failed to communicate with RPI WebSocket: {str(e)}")
                    break
                else:
                    ws.send(json.dumps({
                        'type': 'error',
                        'message': message
                    }))

    except Exception as e:
        print(f"Błąd podczas inicjalizacji ładowania: {str(e)}")
        if ws.connected:
            ws.send(json.dumps({
                'type': 'error',
                'message': f'Wystąpił błąd: {str(e)}'
            }))
