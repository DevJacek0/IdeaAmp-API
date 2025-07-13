import os
from datetime import time, datetime
from math import radians, sin, cos, asin, sqrt

from flask import current_app, request
from sqlalchemy import Column, Integer, DECIMAL, func, String, Enum, Time
from werkzeug.utils import secure_filename

from app import db
from app.models.station import Station
from app.services.service import Service


class StationService(Service):
    def __init__(self):
        """
        Konstruktor klasy StationService, który inicjalizuje klasę bazową Service.
        """
        super().__init__(
            table_name="stations",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_station
            }
        )

    def _row_to_station(self, row: dict) -> Station:
        return Station(
            id=row["id"],
            name=row["name"],
            lat=row["lat"],
            lng=row["lng"],
            address=row["address"],
            image_url=row["image_url"],
            status=row["status"],
            opening_time=row["opening_time"],
            closing_time=row["closing_time"],
            price_per_kwh=row["price_per_kwh"]
        )

    def _get_columns(self):
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('name', String(100), nullable=False),
            Column('lat', DECIMAL(10, 8), nullable=False),
            Column('lng', DECIMAL(11, 8), nullable=False),
            Column('address', String(255), nullable=False),
            Column('image_url', String(500), nullable=True),
            Column('status', Enum('active', 'inactive', "maintenance", name='station_status'), nullable=False,
                   default='active'),
            Column('opening_time', Time, nullable=False),
            Column('closing_time', Time, nullable=False),
            Column('price_per_kwh', DECIMAL(10, 2), nullable=False)
        ]

    def get(self, session_id: int):
        """
        Metoda pobiera informacje o stacji z bazy danych na podstawie podanego identyfikatora.

        Argumenty:
            session_id (int): Identyfikator stacji, którą chcemy pobrać.

        Zwraca:
            Station: Obiekt stacji lub None, jeśli stacja nie została znaleziona.
        """
        return super().get(session_id)

    def get_all(self):
        """
        Metoda pobiera wszystkie stacje z bazy danych.

        Zwraca:
            List[Station]: Lista obiektów stacji.
        """
        return super().get_all()

    def create(self, name: str, lat: float, lng: float, address: str,
               status: str, opening_time, closing_time,
               price_per_kwh: float, image_file=None) -> Station:
        """
        Metoda tworzy nową stacje w bazie danych.

        Argumenty:
            name (str): Nazwa stacji.
            lat (float): Szerokość geograficzna stacji.
            lng (float): Długość geograficzna stacji.
            address (str): Adres stacji.
            status (str): Status stacji (np. "active", "inactive", "maintenance").
            opening_time (Union[datetime, str]): Czas otwarcia stacji.
            closing_time (Union[datetime, str]): Czas zamkniecia stacji.
            price_per_kwh (float): Cena za kWh.
            image_file (file): Obrazek stacji.

        Zwraca:
            Station: Obiekt stacji.
        """
        session = self.Session()
        try:
            next_id = session.query(func.max(Station.id)).scalar() + 1 if session.query(Station.id).count() > 0 else 1
            image_url = None
            if image_file:
                image_url = self.save_station_image(image_file, name)

            if isinstance(opening_time, datetime):
                opening_time = opening_time.time()
            elif isinstance(opening_time, str):
                try:
                    hour, minute = map(int, opening_time.split(':'))
                    opening_time = time(hour=hour, minute=minute)
                except ValueError:
                    raise ValueError("Nieprawidłowy format czasu otwarcia (wymagany format: HH:MM)")

            if isinstance(closing_time, datetime):
                closing_time = closing_time.time()
            elif isinstance(closing_time, str):
                try:
                    hour, minute = map(int, closing_time.split(':'))
                    closing_time = time(hour=hour, minute=minute)
                except ValueError:
                    raise ValueError("Nieprawidłowy format czasu zamknięcia (wymagany format: HH:MM)")

            new_station = Station(
                id=next_id,
                name=name,
                lat=lat,
                lng=lng,
                address=address,
                image_url=image_url,
                status=status,
                opening_time=opening_time,
                closing_time=closing_time,
                price_per_kwh=price_per_kwh
            )

            session.add(new_station)
            session.commit()
            refreshed_station = session.merge(new_station)
            self.set(refreshed_station.id, refreshed_station)

            return refreshed_station

        except Exception as e:
            session.rollback()
            print(f"Błąd podczas tworzenia stacji: {str(e)}")
            raise
        finally:
            session.close()

    @staticmethod
    def save_station_image(image_file, station_name: str) -> str:
        """
        Metoda zapisuje obrazek stacji na dysku.

        Argumenty:
            image_file (file): Obrazek stacji.
            station_name (str): Nazwa stacji.

        Zwraca:
            str: URL obrazka stacji.
        """
        if not image_file:
            return None

        file_extension = os.path.splitext(image_file.filename)[1].lower()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_station_name = secure_filename(station_name).lower().replace(' ', '_')
        filename = f"{safe_station_name}_{timestamp}{file_extension}"

        upload_folder = os.path.join('app','attachments', 'all', 'uploads', 'stations')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        file_path = os.path.join(upload_folder, filename)
        image_file.save(file_path)

        host_url = request.host_url.rstrip('/')
        return f"{host_url}/uploads/stations/{filename}"

    def update_station(self, station_id: int, **kwargs):
        """
        Metoda aktualizuje dane stacji w bazie danych.

        Argumenty:
            station_id (int): ID stacji.
            kwargs (dict): Argumenty do aktualizacji.

        Zwraca:
            Station: Obiekt stacji.
        """
        session = self.Session()
        try:
            station = session.query(Station).get(station_id)
            if not station:
                return None

            for key, value in kwargs.items():
                if hasattr(station, key):
                    setattr(station, key, value)

            session.commit()
            refreshed_station = session.merge(station)
            self.set(refreshed_station.id, refreshed_station)
            return station
        finally:
            session.close()

    def update_status(self, station_id: int, status: str):
        """
        Metoda aktualizuje status stacji w bazie danych.

        Argumenty:
            station_id (int): ID stacji.
            status (str): Nowy status stacji.

        Zwraca:
            Station: Obiekt stacji.
        """
        return self.update_station(station_id, status=status)

    def update_price(self, station_id: int, price_per_kwh: float):
        """
        Metoda aktualizuje cene stacji w bazie danych.

        Argumenty:
            station_id (int): ID stacji.
            price_per_kwh (float): Nowa cena stacji.

        Zwraca:
            Station: Obiekt stacji.
        """
        return self.update_station(station_id, price_per_kwh=price_per_kwh)

    @staticmethod
    def delete_station_image(image_url: str) -> bool:
        """
        Metoda usuwa obrazek stacji z dysku.

        Argumenty:
            image_url (str): URL obrazka stacji.

        Zwraca:
            bool: True jeśli obrazek został usunięty, False w przeciwnym przypadku.
        """
        try:
            filename = image_url.split('/')[-1]
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'stations')
            file_path = os.path.join(upload_folder, filename)

            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Błąd podczas usuwania zdjęcia: {e}")
            return False

    def delete(self, station_id: int) -> bool:
        """
        Metoda usuwa stacje z bazy danych.

        Argumenty:
            station_id (int): ID stacji.

        Zwraca:
            bool: True jeśli stacja została usunięta, False w przeciwnym przypadku.
        """
        session = self.Session()
        try:
            station = session.query(Station).get(station_id)
            if station:
                if station.image_url:
                    self.delete_station_image(station.image_url)

                session.delete(station)
                session.commit()
                self.clear(station_id)
                return True
            return False
        finally:
            session.close()

    @staticmethod
    def is_within_radius(lat1: float, lon1: float, lat2: float, lon2: float, radius: float) -> bool:
        """
        Metoda sprawdza, czy stacja znajduje się w okolicy podanego promienia.

        Argumenty:
            lat1 (float): Latitude pierwszego punktu.
            lon1 (float): Longitude pierwszego punktu.
            lat2 (float): Latitude drugiego punktu.
            lon2 (float): Longitude drugiego punktu.
            radius (float): Promieniu.

        Zwraca:
            bool: True jeśli stacja znajduje się w okolicy promienia, False w przeciwnym przypadku.
        """
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km <= radius

    @staticmethod
    def verify_station_image(image_url: str) -> bool:
        """
        Metoda sprawdza, czy obrazek stacji istnieje na dysku.

        Argumenty:
            image_url (str): URL obrazka stacji.

        Zwraca:
            bool: True jeśli obrazek stacji istnieje, False w przeciwnym przypadku.
        """
        try:
            filename = image_url.split('/')[-1]
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'stations')
            file_path = os.path.join(upload_folder, filename)
            return os.path.exists(file_path)
        except Exception:
            return False

    @staticmethod
    def parse_time(time_value):
        """
        Metoda parsuje ciąg znaków reprezentujący czas w formacie ``HH:MM`` na obiekt ``datetime.time``.

        Argumenty:
            time_value (str | time): Wartość czasu do sparsowania.

        Zwraca:
            time: Obiekt czasu, jeśli parsowanie się powiedzie.\n
            ValueError: Jeśli parsowanie się nie powiedzie.
        """
        if isinstance(time_value, str):
            try:
                parsed_datetime = datetime.strptime(time_value, '%H:%M')
                return parsed_datetime.time()
            except ValueError as e:
                raise ValueError(f"Nieprawidłowy format czasu. Wymagany format: HH:MM")
        elif isinstance(time_value, time):
            return time_value
        elif isinstance(time_value, datetime):
            return time_value.time()
        else:
            raise ValueError(f"Nieprawidłowy typ danych dla czasu")
