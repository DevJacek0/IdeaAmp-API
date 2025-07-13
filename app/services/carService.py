from datetime import datetime

from sqlalchemy import Column, Integer, String, Enum, DECIMAL, TIMESTAMP, func, BigInteger
from app.models.car import Car
from app import db
from app.services.service import Service


class CarsService(Service):
    def __init__(self):
        """
        Konstruktor klasy CarsService, który inicjalizuje klasę bazową Service.
        """

        super().__init__(
            table_name="cars",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_car
            }
        )

    def _row_to_car(self, row: dict) -> Car:
        return Car(
            id=row["id"],
            owner_id=row["owner_id"],
            plate=row["plate"],
            name=row["name"],
            battery_capacity=row["battery_capacity"],
            max_charging_power=row["max_charging_power"],
            connector_type=row["connector_type"],
            country_code=row["country_code"],
            year=row["year"],
            registered_on=row["registered_on"]
        )

    def _get_columns(self):
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('owner_id', Integer, nullable=False),
            Column('plate', String(20), nullable=False, unique=True),
            Column('name', String(100), nullable=False),
            Column('battery_capacity', DECIMAL(5, 2), nullable=False),
            Column('max_charging_power', DECIMAL(5, 2), nullable=False),
            Column('connector_type', Enum('Type1', 'Type2', 'CCS', 'CHAdeMO', 'Tesla NACS', name='connector_types'), nullable=False),
            Column('country_code', String(2), nullable=True),
            Column('year', Integer, nullable=False),
            Column('registered_on', BigInteger, nullable=False, server_default=func.now())
        ]

    def get(self, car_id: int):
        """
        Pobiera pojazd o podanym ID

        Argumenty:
            car_id (int): ID pojazdu, który chcemy pobrać

        Zwraca:
            Car: Obiekt pojazdu
        """
        return super().get(car_id)

    def get_all(self):
        """
        Pobiera wszystkie pojazdy

        Zwraca:
            List[Car]: Lista obiektów pojazdów
        """

        return super().get_all()

    def get_by_owner(self, owner_id: int):
        """
        Pobiera wszystkie pojazdy dla podanego własника

        Argumenty:
            owner_id (int): ID własника, dla którego chcemy pobrać pojazdy

        Zwraca:
            List[Car]: Lista obiektów pojazdów
        """
        return [car for car in self.get_all() if car.owner_id == owner_id]

    def plate_exists(self, plate: str) -> bool:
        """
        Sprawdza, czy pojazd o podanej rejestracji już istnieje

        Argumenty:
            plate (str): Rejestracja pojazdu, który chcemy sprawdzić

        Zwraca:
            bool: True, jeśli pojazd o podanej rejestracji już istnieje, False w przeciwnym przypadku
        """
        return any(car.plate == plate for car in self.get_all())

    def create(self, owner_id: int, plate: str, name: str, battery_capacity: float, max_charging_power: float,
               connector_type: str, country_code: str, year: int) -> Car:
        """
        Tworzy nowy pojazd

        Argumenty:
            owner_id (int): ID własnika pojazdu
            plate (str): Rejestracja pojazdu
            name (str): Nazwa pojazdu
            battery_capacity (float): Pojemność baterii pojazdu
            max_charging_power (float): Maksymalna moc ładowania pojazdu
            connector_type (str): Typ ładowarki pojazdu
            country_code (str): Kraj produkcji pojazdu
            year (int): Rok produkcji pojazdu

        Zwraca:
            Car: Obiekt pojazdu
        """
        next_id = db.session.query(func.max(Car.id)).scalar() + 1 if db.session.query(Car.id).count() > 0 else 1
        new_car = Car(
            id=next_id,
            owner_id=owner_id,
            plate=plate,
            name=name,
            battery_capacity=battery_capacity,
            max_charging_power=max_charging_power,
            connector_type=connector_type,
            country_code=country_code,
            year=year,
            registered_on=BigInteger().python_type(int(datetime.utcnow().timestamp() * 1000))
        )

        db.session.add(new_car)
        db.session.commit()

        self.set(new_car.id, new_car)
        return new_car

    def update(self, car_id: int, **kwargs):
        """
        Aktualizuje pojazd o podanym ID

        Argumenty:
            car_id (int): ID pojazdu, który chcemy aktualizować
            **kwargs: Argumenty do aktualizacji

        Zwraca:
            Car: Obiekt pojazdu po aktualizacji
        """

        car = db.session.query(Car).get(car_id)
        if not car:
            return None

        for key, value in kwargs.items():
            if hasattr(car, key):
                setattr(car, key, value)

        db.session.commit()
        self.set(car.id, car)
        return car

    def delete(self, car_id: int):
        """
        Usuwa pojazd o podanym ID

        Argumenty:
            car_id (int): ID pojazdu, który chcemy usunąć

        Zwraca:
            bool: True, jeśli pojazd został usunięty, False w przeciwnym przypadku
        """

        car = db.session.query(Car).get(car_id)
        if car:
            db.session.delete(car)
            db.session.commit()
            self.clear(car_id)
            return True
        return False

    def get_by_plate(self, plate: str) -> Car:
        """
        Pobiera pojazd o podanej rejestracji

        Argumenty:
            plate (str): Rejestracja pojazdu, który chcemy pobrać

        Zwraca:
            Car: Obiekt pojazdu
        """

        return next((car for car in self.get_all() if car.plate == plate), None)
