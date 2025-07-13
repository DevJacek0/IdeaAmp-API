from sqlalchemy import Column, Integer, DECIMAL, Enum, ForeignKey, func
from app.models.port import Port
from app import db
from app.services.service import Service


class PortService(Service):
    def __init__(self):
        """
        Konstruktor klasy PortService, który inicjalizuje klasę bazową Service.
        """

        super().__init__(
            table_name="ports",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_port
            }
        )

    def _row_to_port(self, row: dict) -> Port:
        return Port(
            id=row["id"],
            station_id=row["station_id"],
            max_power=row["max_power"],
            connector_type=row["connector_type"],
            status=row["status"]
        )

    def _get_columns(self):
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('station_id', Integer, ForeignKey('stations.id'), nullable=False),
            Column('max_power', DECIMAL(5, 2), nullable=False),
            Column('connector_type', Enum('Type1', 'Type2', 'CCS', 'CHAdeMO', 'Tesla NACS', 
                   name='connector_types'), nullable=False),
            Column('status', Enum('Available', 'InUse', 'Faulty', 'Maintenance', 
                   name='port_status'), nullable=False)
        ]

    def get(self, port_id: int):
        """
        Metoda zwracająca port o podanym identyfikatorze.

        Argumenty:
            port_id (int): Identyfikator portu.

        Zwraca:
            Port: Obiekt portu o podanym identyfikatorze.
        """
        return super().get(port_id)

    def get_all(self):
        """
        Metoda zwracająca wszystkie porty.

        Zwraca:
            list: Lista obiektów portów.
        """
        return super().get_all()

    def get_by_station(self, station_id: int):
        """
        Metoda zwracająca porty dla danej stacji.

        Argumenty:
            station_id (int): Identyfikator stacji.

        Zwraca:
            list: Lista obiektów portów dla danej stacji.
        """
        return [port for port in self.get_all() if port.station_id == station_id]

    def get_available_ports(self):
        """
        Metoda zwracająca dostępne porty.

        Zwraca:
            list: Lista obiektów dostępnych portów.
        """
        return [port for port in self.get_all() if port.status == 'Available']

    def create(self, station_id: int, max_power: float, connector_type: str, status: str) -> Port:
        """
        Metoda tworząca nowy port.

        Argumenty:
            station_id (int): Identyfikator stacji.
            max_power (float): Maksymalna moc zasilania.
            connector_type (str): Rodzaj połączenia.
            status (str): Status portu.

        Zwraca:
            Port: Obiekt utworzonego portu.
        """
        session = self.Session()
        try:
            next_id = session.query(func.max(Port.id)).scalar() + 1 if session.query(Port.id).count() > 0 else 1
            new_port = Port(
                id=next_id,
                station_id=station_id,
                max_power=max_power,
                connector_type=connector_type,
                status=status
            )

            session.add(new_port)
            session.commit()

            self.set(new_port.id, new_port)
            return new_port
        finally:
            session.close()

    def update(self, port_id: int, **kwargs):
        """
        Metoda aktualizująca port.

        Argumenty:
            port_id (int): Identyfikator portu.
            **kwargs: Argumenty do aktualizacji.

        Zwraca:
            Port: Obiekt aktualizowanego portu.
        """
        session = self.Session()
        try:
            port: Port = session.query(Port).get(port_id)
            if not port:
                return None

            for key, value in kwargs.items():
                if hasattr(port, key):
                    setattr(port, key, value)

            session.commit()
            refreshed_port = session.merge(port)
            self.set(refreshed_port.id, refreshed_port)
            return port
        finally:
            session.close()

    def update_status(self, port_id: int, status: str):
        """
        Metoda aktualizuje status portu.

        Argumenty:
            port_id (int): Identyfikator portu.
            status (str): Nowy status portu.

        Zwraca:
            bool: True jesli port został zaktualizowany, False w przeciwnym przypadku.
        """
        session = self.Session()
        try:
            port = session.query(Port).get(port_id)
            if port:
                port.status = status
                session.commit()

                refreshed_port = session.merge(port)
                self.set(refreshed_port.id, refreshed_port)
                return True
            return False
        finally:
            session.close()

    def delete(self, port_id: int) -> bool:
        """
        Metoda usuwa port.

        Argumenty:
            port_id (int): Identyfikator portu.

        Zwraca:
            bool: True jesli port został usuniety, False w przeciwnym przypadku.
        """
        session = self.Session()
        try:
            port = session.query(Port).get(port_id)
            if port:
                session.delete(port)
                session.commit()
                self.clear(port_id)
                return True
            return False
        finally:
            session.close() 