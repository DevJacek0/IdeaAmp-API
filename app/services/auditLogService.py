import json
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import Column, Integer, String, JSON, func, BigInteger
from app.models.auditLog import AuditLog
from app.models.chargingSession import ChargingSession
from app.models.station import Station
from app.services.service import Service


class AuditLogsService(Service):
    def __init__(self):
        """
        Konstruktor klasy AuditLogsService z inicjalizacją podstawowych parametrów.
        """

        super().__init__(
            table_name="audit_logs",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_log
            }
        )

    def _row_to_log(self, row: dict) -> AuditLog:
        return AuditLog(
            id=row["id"],
            user_id=row["user_id"],
            action=row["action"],
            details=row["details"],
            created_on=row["created_on"]
        )

    def _get_columns(self):
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('user_id', Integer, nullable=False),
            Column('action', String(255), nullable=False),
            Column('details', JSON, nullable=True),
            Column('created_on', BigInteger, nullable=False, server_default=func.now())
        ]

    def get(self, log_id: int):
        """
        Pobiera log o podanym identyfikatorze.

        Argumenty:
        - log_id (int): Identyfikator logu do pobrania.

        Zwraca:
        - AuditLog: Obiekt logu lub None, jesli log nie został znaleziony.
        """
        return super().get(log_id)

    def get_all(self):
        """
        Pobiera wszystkie logi.

        Zwraca:
        - List[AuditLog]: Lista wszystkich logów.
        """

        return super().get_all()

    def get_by_user(self, user_id: int):
        """
        Pobiera logi dla podanego identyfikatora użytkownika.

        Argumenty:
        - user_id (int): Identyfikator użytkownika.

        Zwraca:
        - List[AuditLog]: Lista logów dla podanego użytkownika.
        """

        return [log for log in super().get_all() if log.user_id == user_id]

    def get_by_action(self, action: str):
        """
        Pobiera logi dla podanej akcji.

        Argumenty:
        - action (str): Akcja.

        Zwraca:
        - List[AuditLog]: Lista logów dla podanej akcji.
        """

        return [log for log in super().get_all() if log.action.lower() == action.lower()]

    def log_action(self, user_id: int, action: str, details: dict = None) -> AuditLog:
        """
        Loguje akcje użytkownika.

        Argumenty:
        - user_id (int): Identyfikator użytkownika.
        - action (str): Akcja.
        - details (dict): Detale akcji.

        Zwraca:
        - AuditLog: Obiekt logu.
        """

        session = self.Session()
        try:
            next_id = session.query(func.max(AuditLog.id)).scalar() + 1 if session.query(
                AuditLog.id).count() > 0 else 1
            new_log = AuditLog(
                id=next_id,
                user_id=user_id,
                action=action,
                details=details or {},
                created_on=int(datetime.utcnow().timestamp() * 1000)
            )

            session.add(new_log)
            session.commit()

            refreshed_log = session.merge(new_log)
            self.set(refreshed_log.id, refreshed_log)
            return refreshed_log
        finally:
            session.close()

    def log_login(self, user_id: int, ip_address: str, user_agent: str, success: bool = True) -> AuditLog:
        """
        Loguje logowanie użytkownika.

        Argumenty:
        - user_id (int): Identyfikator użytkownika.
        - ip_address (str): Adres IP użytkownika.
        - user_agent (str): Agent użytkownika.
        - success (bool): Czy logowanie użytkownika przebiegło pomyslnie.

        Zwraca:
        - AuditLog: Obiekt logu.
        """

        action = "login" if success else "login_failed"
        details = {
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        return self.log_action(user_id, action, details)

    def log_logout(self, user_id: int, ip_address: str, user_agent: str) -> AuditLog:
        """
        Loguje wylogowanie użytkownika.

        Argumenty:
        - user_id (int): Identyfikator użytkownika.
        - ip_address (str): Adres IP użytkownika.
        - user_agent (str): Agent użytkownika.

        Zwraca:
        - AuditLog: Obiekt logu.
        """

        details = {
            "ip_address": ip_address,
            "user_agent": user_agent
        }
        return self.log_action(user_id, "logout", details)

    def get_login_history(self, user_id: int = None):
        """
        Pobiera historie logowania.

        Argumenty:
        - user_id (int): Identyfikator użytkownika.

        Zwraca:
        - List[AuditLog]: Lista logów logowania.
        """

        logs = self.get_all()
        login_actions = ["login", "login_failed", "logout"]

        filtered_logs = [
            log for log in logs
            if log.action in login_actions and
               (user_id is None or log.user_id == user_id)
        ]

        return filtered_logs

    def log_station_failure(self, station_id: int):
        """
        Loguje awarię stacji i sprawdza, czy w ciągu ostatnich 24h stacja weszła 3 razy w stan awaryjny.
        Jeśli tak, generuje dodatkowy log 'station_critical_failure'.

        Argumenty:
        - station_id (int): Identyfikator stacji.
        """

        logs = [
            {"action": log.action, "details": log.details, "created_on": log.created_on}
            for log in self.get_all()
        ]

        last_24h_timestamp = int((datetime.utcnow() - timedelta(hours=24)).timestamp() * 1000)

        failure_logs = []

        for log in logs:
            try:
                details = json.loads(log["details"]) if isinstance(log["details"], str) else log["details"]

                created_on = int(log["created_on"]) if isinstance(log["created_on"], str) else log["created_on"]

                if log["action"] == "station_failure" and details.get(
                        "station_id") == station_id and created_on >= last_24h_timestamp:
                    failure_logs.append(log)
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"Błąd dekodowania JSON lub konwersji danych w logu: {log}, błąd: {e}")

        self.log_action(
            user_id=0,
            action="station_failure",
            details={"station_id": station_id}
        )

        if len(failure_logs) + 1 >= 3:
            self.log_action(
                user_id=0,
                action="station_critical_failure",
                details={"station_id": station_id,
                         "message": "Stacja weszła w stan awaryjny 3 razy w ciągu ostatnich 24h."}
            )

    def check_unused_charges(self):
        """
        Sprawdza, czy stacja jest nieuzyczona w ciągu ostatnich 10 dni, jeśli tak - loguje to w logach.
        """

        from app.services.chargingSessionService import ChargingSessionsService
        from app.services.stationService import StationService
        from app.services.portService import PortService
        charging_session_service: ChargingSessionsService = ChargingSessionsService()
        station_service: StationService = StationService()
        port_service: PortService = PortService()

        threshold_date: int = int((datetime.utcnow() - timedelta(days=10)).timestamp() * 1000)
        charging_sessions: List[ChargingSession] = charging_session_service.get_all()
        stations: List[Station] = station_service.get_all()

        used_stations = {port_service.get(int(session.port_id)).station_id for session in charging_sessions if
                         session.started_on >= threshold_date}
        all_stations = {station.id for station in stations}

        unused_stations = all_stations - used_stations

        for station_id in unused_stations:
            self.log_action(
                user_id=0,
                action="unused_station",
                details={"station_id": station_id}
            )