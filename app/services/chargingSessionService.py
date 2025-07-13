from sqlalchemy import Column, Integer, DECIMAL, TIMESTAMP, func, BigInteger
from app.models.chargingSession import ChargingSession
from app import db
from app.models.user import User
from app.services.service import Service
from datetime import datetime
from typing import Optional
from threading import Timer
from app.services.portService import PortService
from app.services.userService import UsersService
from app.services.stationService import StationService
from app.services.auditLogService import AuditLogsService
from app.services.carService import CarsService
from app.services.transactionService import TransactionService
from app.services.discountService import DiscountService


class ChargingSessionsService(Service):
    active_sessions: dict[int, any] = {}

    def __init__(self):
        """
        Konstruktor klasy ChargingSessionsService, który inicjalizuje klasę bazową Service.
        """

        self.ports_service = PortService()
        self.users_service = UsersService()
        self.stations_service = StationService()
        self.audit_logs_service = AuditLogsService()
        self.cars_service = CarsService()
        self.transaction_service = TransactionService()
        self.discount_service = DiscountService()

        super().__init__(
            table_name="charging_sessions",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_session
            }
        )

    def _row_to_session(self, row: dict) -> ChargingSession:
        return ChargingSession(
            id=row["id"],
            user_id=row["user_id"],
            port_id=row["port_id"],
            car_id=row["car_id"],
            started_on=row["started_on"],
            end_on=row["end_on"],
            energy_consumed=row["energy_consumed"],
            power_limit=row["power_limit"],
            cost=row["cost"]
        )

    def _get_columns(self):
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('user_id', Integer, nullable=True),
            Column('port_id', Integer, nullable=False),
            Column('car_id', Integer, nullable=True),
            Column('started_on', BigInteger, nullable=False, server_default=func.now()),
            Column('end_on', BigInteger),
            Column('energy_consumed', DECIMAL(10, 2), nullable=True),
            Column('power_limit', DECIMAL(5, 2), nullable=True),
            Column('cost', DECIMAL(10, 2), nullable=True)
        ]

    def get(self, session_id: int):
        """
        Pobiera informację o sesji ładowania dla podanego identyfikatora sesji ładowania.

        Argumenty:
            session_id (int): Identyfikator sesji ładowania, którą chcemy pobrać.

        Zwraca:
            ChargingSession: Obiekt sesji ładowania.
        """

        return super().get(session_id)

    def get_all(self):
        """
        Pobiera wszystkie informacje o sesjach ładowania.

        Zwraca:
            list[ChargingSession]: Lista obiektów sesji ładowania.
        """
        return super().get_all()

    def get_by_user(self, user_id: int):
        """
        Pobiera informacje o sesjach ładowania dla podanego identyfikatora użytkownika.

        Argumenty:
            user_id (int): Identyfikator użytkownika.

        Zwraca:
            list[ChargingSession]: Lista obiektów sesji ładowania.
        """
        return [session for session in super().get_all() if session.user_id == user_id]

    def get_active_sessions(self):
        """
        Pobiera informacje o aktywnych sesjach ładowania.

        Zwraca:
            list[ChargingSession]: Lista obiektów sesji ładowania.
        """
        return [session for session in super().get_all() if session.end_on is None]

    def get_between(self, start: int, end: int, user_id: int | None = None) -> list[dict[str, User | ChargingSession]]:
        """
        Pobiera informacje o sesjach ładowania dla podanych dat.

        Argumenty:
            start (int): Data początkowa w milisekundach.
            end (int): Data koncowa w milisekundach.
            user_id (int | None): Identyfikator użytkownika, dla którego pobieramy sesje ładowania. Domyslnie None.

        Zwraca:
            list[dict[str, User | ChargingSession]]: Lista obiektów sesji ładowania.
        """
        if user_id is None:
            sessions = [{
                "user": self.users_service.get(s.user_id),
                "session": s,
                "car": self.cars_service.get(s.car_id)
            } for s in self.get_all() if int(start) < int(s.started_on) / 1000 < int(end)]
        else:
            user = self.users_service.get(user_id)

            sessions = [{
                "user": user,
                "session": s,
                "car": self.cars_service.get(s.car_id)
            } for s in self.get_by_user(user_id) if int(start) < int(s.started_on) / 1000 < int(end)]

        return sorted(sessions, key=lambda s: s["session"].started_on, reverse=True)

    def get_last_24_hours(self, user_id: int | None = None) -> list[dict[str, User | ChargingSession]]:
        """
        Pobiera informacje o sesjach ładowania w ostatnich 24 godzinach.

        Argumenty:
            user_id (int | None): Identyfikator użytkownika, dla którego pobieramy sesje ładowania. Domyslnie None.

        Zwraca:
            list[dict[str, User | ChargingSession]]: Lista obiektów sesji ładowania.
        """
        if user_id is None:
            sessions = [{
                "user": self.users_service.get(s.user_id),
                "session": s,
                "car": self.cars_service.get(s.car_id)
            } for s in self.get_all() if int(datetime.now().timestamp()) - int(s.started_on) / 1000 < 86400]

        else:
            user = self.users_service.get(user_id)

            sessions = [{
                "user": user,
                "session": s,
                "car": self.cars_service.get(s.car_id)
            } for s in self.get_by_user(user_id) if int(datetime.now().timestamp()) - int(s.started_on) / 1000 < 86400]

        return sorted(sessions, key=lambda s: s["session"].started_on, reverse=True)

    def get_last_month(self, user_id: int | None = None) -> list[dict[str, User | ChargingSession]]:
        """
        Pobiera informacje o sesjach ładowania w ostatnim miesiacu.

        Argumenty:
            user_id (int | None): Identyfikator użytkownika, dla którego pobieramy sesje ładowania. Domyslnie None.

        Zwraca:
            list[dict[str, User | ChargingSession]]: Lista obiektów sesji ładowania.
        """
        if user_id is None:
            sessions = [{
                "user": self.users_service.get(s.user_id),
                "session": s,
                "car": self.cars_service.get(s.car_id)
            } for s in self.get_all() if int(datetime.now().timestamp()) - int(s.started_on) / 1000 < 86400 * 30]

        else:
            user = self.users_service.get(user_id)

            sessions = [{
                "user": user,
                "session": s,
                "car": self.cars_service.get(s.car_id)
            } for s in self.get_by_user(user_id) if int(datetime.now().timestamp()) - int(s.started_on) / 1000 < 86400 * 30]

        return sorted(sessions, key=lambda s: s["session"].started_on, reverse=True)

    def create_session(self, user_id: int, port_id: int, car_id: int = None,
                       power_limit: float = None) -> ChargingSession | None:

        """
        Tworzy nową sesje ładowania.

        Argumenty:
            user_id (int): Identyfikator użytkownika.
            port_id (int): Identyfikator portu ładowarki.
            car_id (int | None): Identyfikator pojazdu. Domyslnie None.
            power_limit (float | None): Limit mocowy. Domyslnie None.

        Zwraca:
            ChargingSession | None: Obiekt sesji ładowania lub None w przypadku błedu.
        """
        session = self.Session()
        try:
            next_id = session.query(func.max(ChargingSession.id)).scalar() + 1 if session.query(
                ChargingSession.id).count() > 0 else 1
            new_session = ChargingSession(
                id=next_id,
                user_id=user_id,
                port_id=port_id,
                car_id=car_id,
                power_limit=power_limit
            )

            session.add(new_session)
            session.commit()
            self.set(new_session.id, new_session)
            return new_session
        except Exception as e:
            session.rollback()
            print(f"[Error] Błąd podczas tworzenia sesji ładowania: {e}")
            return None
        finally:
            session.close()

    def initialize_charging(self, user_id: int, port_id: int) -> Optional[dict]:
        """
        Inicjalizuje sesję ładowania po zeskanowaniu QR kodu.

        Argumenty:
            user_id (int): Identyfikator użytkownika.
            port_id (int): Identyfikator portu ładowarki.

        Zwraca:
            dict | None: Obiekt sesji ładowania lub None w przypadku błedu.
        """
        try:
            port = self.ports_service.get(port_id)
            station = self.stations_service.get(port.station_id)

            session = self.create_session(user_id, port_id)
            if not session:
                return None

            self.ports_service.update_status(port_id, 'InUse')

            self.active_sessions[session.id] = {
                'session_id': session.id,
                'user_id': user_id,
                'port_id': port_id,
                'station_id': station.id,
                'max_power': float(port.max_power),
                'price_per_kwh': float(station.price_per_kwh),
                'connector_type': port.connector_type,
                'charging_status': 'initialized',
                'started_on': int(datetime.now().timestamp() * 1000),
                'current_kwh': 0.0,
                'current_power': 0.0,
                'current_cost': 0.0
            }

            return self.active_sessions[session.id]

        except Exception as e:
            print(f"Błąd podczas inicjalizacji ładowania: {str(e)}")
            return None

    def update_session_car(self, session_id: int, car_id: int) -> bool:
        """
        Aktualizuje ID samochodu dla istniejącej sesji ładowania.

        Argumenty:
            session_id (int): Identyfikator sesji ładowania.
            car_id (int): Identyfikator samochodu.

        Zwraca:
            bool: True jesli aktualizacja przebiegła pomyslnie, False w przypadku błedu.
        """
        session = self.Session()
        try:
            charging_session = session.query(ChargingSession).filter(ChargingSession.id == session_id).first()
            if charging_session:
                charging_session.car_id = car_id
                session.commit()
                self.set(charging_session.id, charging_session)
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"[Error] Błąd podczas aktualizacji car_id w sesji ładowania: {e}")
            return False
        finally:
            session.close()

    def end_session(self, session_id: int, energy_consumed: float, final_cost: float = None):
        """
        Konczy sesje ładowania.

        Argumenty:
            session_id (int): Identyfikator sesji ładowania.
            energy_consumed (float): Zuzycie energia w kWh.
            final_cost (float | None): Koncowy koszt ładowania. Domyslnie None.

        Zwraca:
            ChargingSession | None: Obiekt sesji ładowania lub None w przypadku błedu.
        """
        session = self.Session()
        try:
            charging_session = session.query(ChargingSession).get(session_id)
            if not charging_session:
                print(f"[Error] Sesja ładowania {session_id} nie istnieje!")
                return None

            charging_session.end_on = int(datetime.now().timestamp() * 1000)
            charging_session.energy_consumed = energy_consumed
            charging_session.cost = final_cost


            session.commit()
            self.set(charging_session.id, charging_session)
            return charging_session
        except Exception as e:
            session.rollback()
            print(f"[Error] Błąd podczas kończenia sesji ładowania: {session_id}: {e}")
            return None
        finally:
            session.close()

    def start_charging(self, session_id: int, user_id: int, target_kwh: float, car_id: int,
                       discount_code: str = None) -> tuple[bool, float, str]:
        """
        Rozpoczyna właściwe ładowanie z określoną ilością kWh i opcjonalnym kodem rabatowym.

        Argumenty:
            session_id (int): Identyfikator sesji ładowania.
            user_id (int): Identyfikator użytkownika.
            target_kwh (float): Celowe zuzycie energia w kWh.
            car_id (int): Identyfikator samochodu.
            discount_code (str | None): Kod rabatowy. Domyslnie None.

        Zwraca:
            tuple[bool, float, str]: Krotka zawierajaca (sukces, szacowany_koszt, wiadomość)
        """
        try:
            session = self.get_session_status(session_id)
            if not session or session['user_id'] != user_id:
                return False, 0, "Brak sesji lub nieprawidłowy użytkownik"

            user = self.users_service.get(user_id)
            price_per_kwh = float(session['price_per_kwh'])
            estimated_cost = target_kwh * price_per_kwh

            discount_message = None
            if discount_code:
                estimated_cost, discount_message, discount_status = self.discount_service.apply_discount(estimated_cost,
                                                                                                         discount_code)
                if discount_status != self.discount_service.DiscountStatus.SUCCESS:
                    self.ports_service.update_status(int(session['port_id']), 'Available')
                    return False, estimated_cost, f"Błąd rabatu: {discount_message}"

            if user.balance < estimated_cost:
                self.ports_service.update_status(int(session['port_id']), 'Available')
                return False, estimated_cost, f"Niewystarczające środki. Potrzeba: {estimated_cost}, Saldo: {user.balance}"

            car = self.cars_service.get(car_id)
            if not car:
                self.ports_service.update_status(int(session['port_id']), 'Available')
                return False, estimated_cost, "Nie znaleziono samochodu"

            db_session = self.Session()
            try:
                charging_session = db_session.query(ChargingSession).get(session_id)
                if charging_session:
                    charging_session.car_id = car_id
                    charging_session.power_limit = min(float(session['max_power']), float(car.max_charging_power))
                    db_session.commit()
                    self.set(charging_session.id, charging_session)

                session['car_id'] = car_id
                session['target_kwh'] = target_kwh
                session['estimated_cost'] = estimated_cost
                session['charging_status'] = 'charging'
                session[
                    'discount_code'] = discount_code if discount_code and discount_status == self.discount_service.DiscountStatus.SUCCESS else None
                self.active_sessions[session_id] = session

                return True, estimated_cost, "Rozpoczęto ładowanie"
            finally:
                db_session.close()

        except Exception as e:
            print(f"[Error] Błąd podczas rozpoczynania ładowania: {e}")
            return False, 0, f"Błąd systemu: {str(e)}"

    def update_charging_status(self, session_id: int, current_kwh: float, status: str, charging_power: float,
                               current_cost: float) -> bool:
        """
        Aktualizuje status ładowania na podstawie danych z pojazdu/stacji

        Argumenty:
            session_id (int): Identyfikator sesji ładowania.
            current_kwh (float): Aktualne zuzycie energia w kWh.
            status (str): Aktualny status ładowania.
            charging_power (float): Aktualna moc ładowania.
            current_cost (float): Aktualny koszt ładowania.

        Zwraca:
            bool: True jesli aktualizacja przebiegła pomyslnie
        """
        try:
            if session_id not in self.active_sessions:
                return False

            session = self.active_sessions[session_id]
            session.update({
                'current_kwh': current_kwh,
                'current_power': charging_power,
                'current_cost': current_cost,
                'charging_status': status
            })

            # 1kWh = 100pkt
            points_to_add = int((current_kwh - session.get('last_points_kwh', 0)) * 100)
            if points_to_add > 0:
                session['last_points_kwh'] = current_kwh
                self.users_service.add_points(session['user_id'], points_to_add)

            return True

        except Exception as e:
            print(f"[Error] Błąd podczas aktualizacji statusu ładowania: {e}")
            return False

    def process_payment(self, session_id: int, final_cost: float, discount_code: str = None, car_id: int = None,
                        station_id: int = None) -> tuple[float, bool]:
        """
        Przetwarza płatność za sesję ładowania z opcjonalnym kodem rabatowym.


        Argumenty:
            session_id (int): Identyfikator sesji ładowania.
            final_cost (float): Koncowy koszt ładowania.
            discount_code (str | None): Kod rabatowy. Domyslnie None.
            car_id (int | None): Identyfikator samochodu. Domyslnie None.
            station_id (int | None): Identyfikator stacji ładowania. Domyslnie None.

        Zwraca:
            tuple[float, bool]: Krotka zawierajaca (szacowany_koszt, sukces)
        """
        try:
            session = self.active_sessions[session_id]
            if not session:
                return final_cost, False

            if discount_code:
                cost, message, status = self.discount_service.apply_discount(final_cost, discount_code)

                if status == self.discount_service.DiscountStatus.SUCCESS:
                    final_cost = cost

            self.transaction_service.create_transaction(
                user_id=session['user_id'],
                car_id=session['car_id'],
                station_id=session['station_id'],
                amount=-final_cost,
                type='Payment'
            )

            self.users_service.update_balance(session['user_id'], -final_cost)

            return final_cost, True
        except Exception as e:
            print(f"[Error] Błąd podczas przetwarzania płatności: {e}")
            return final_cost, False

    def end_charging_session(self, session_id: int, final_energy: float, final_cost: float, reason: str = None,
                             discount_code: str = None) -> bool:
        """
        Kończy sesję ładowania i przetwarza płatność z opcjonalnym kodem rabatowym

        Argumenty:
            session_id (int): Identyfikator sesji ładowania.
            final_energy (float): Koncowy zuzycie energia w kWh.
            final_cost (float): Koncowy koszt ładowania.
            reason (str | None): Powod zakonczenia ładowania. Domyslnie None.
            discount_code (str | None): Kod rabatowy. Domyslnie None.

        Zwraca:
            bool: True jesli koniec ładowania przebiegło pomyslnie
        """
        try:
            session = self.active_sessions[session_id]

            if session is None:
                print(f"[ERROR] Sesja {session_id} nie istnieje w active_sessions!")
                return False

            try:
                port = self.ports_service.get(int(session['port_id']))
            except Exception as e:
                print(f"[ERROR] Nie udało się pobrać portu: {e}")
                return False

            try:
                station = self.stations_service.get(int(session['station_id']))
            except Exception as e:
                print(f"[ERROR] Nie udało się pobrać stacji: {e}")
                return False

            if reason is None:
                if port and port.status == 'Maintenance':
                    reason = 'port_maintenance'
                elif station and station.status == 'Maintenance':
                    reason = 'station_maintenance'

            if discount_code is None:
                discount_code = session.get('discount_code')

            try:
                final_cost, payment_success = self.process_payment(
                    session_id, final_cost, discount_code, session['car_id'], session['station_id']
                )
            except Exception as e:
                print(f"[ERROR] Błąd podczas przetwarzania płatności: {e}")
                return False

            if not payment_success:
                print(f"[ERROR] Płatność nie powiodła się dla sesji {session_id}")
                return False

            try:
                session = self.end_session(session_id, final_energy, final_cost)
            except Exception as e:
                print(f"[ERROR] Błąd podczas kończenia sesji: {e}")
                return False

            if not session:
                print(f"[ERROR] Sesja {session_id} nie została poprawnie zakończona.")
                return False

            try:
                port = self.ports_service.get(session.port_id)
                if port:
                    self.ports_service.update_status(port.id, 'Available')
            except Exception as e:
                print(f"[ERROR] Błąd podczas aktualizacji statusu portu: {e}")

            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            else:
                print(f"[WARNING] Próba usunięcia nieistniejącej sesji {session_id}.")

            return True

        except Exception as e:
            print(f"[FATAL ERROR] Nieoczekiwany błąd podczas kończenia sesji {session_id}: {e}")
            return False

    def get_session_status(self, session_id: int) -> Optional[dict]:
        """
        Zwraca aktualny status sesji ładowania

        Argumenty:
            session_id (int): Identyfikator sesji ładowania.

        Zwraca:
            dict | None: Aktualny status sesji ładowania.
        """
        if session_id not in ChargingSessionsService.active_sessions:
            return None

        return ChargingSessionsService.active_sessions[session_id]

    def get_active_session_for_user(self, user_id: int) -> Optional[dict]:
        """
        Zwraca aktywną sesję dla danego użytkownika, jeśli istnieje

        Argumenty:
            user_id (int): Identyfikator użytkownika.

        Zwraca:
            dict | None: Aktualny status sesji ładowania.
        """
        for session in self.active_sessions.values():
            if session['user_id'] == user_id:
                return session
        return None

    def check_charging_availability(self, session_id: int) -> tuple[bool, str]:
        """
        Sprawdza czy ładowanie może być kontynuowane (port i stacja są dostępne)

        Argumenty:
            session_id (int): Identyfikator sesji ładowania.

        Zwraca:
            tuple[bool, str]: Krotka zawierajaca (moze_kontynuowac, powod_przerwania)
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return False, "session_not_found"

            port = self.ports_service.get(session['port_id'])
            if port.status == 'Maintenance':
                return False, "port_maintenance"

            station = self.stations_service.get(session['station_id'])
            if station.status == 'Maintenance':
                return False, "station_maintenance"

            return True, None
        except Exception as e:
            print(f"[Error] Błąd podczas sprawdzania dostępności: {e}")
            return False, "system_error"
