from sqlalchemy import Column, Integer, DECIMAL, Enum, TIMESTAMP, func, ForeignKey, BigInteger
from app.models.transaction import Transaction
from app.models.user import User
from app.services import UsersService
from app.services.service import Service

class TransactionService(Service):
    def __init__(self):
        """
        Konstruktor klasy TransactionService, który inicjalizuje klasę bazową Service.
        """
        super().__init__(
            table_name="transactions",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_transaction
            }
        )
        self.user_service = UsersService()

    def _row_to_transaction(self, row: dict) -> Transaction:
        return Transaction(
            id=row["id"],
            user_id=row["user_id"],
            station_id=row["station_id"],
            car_id=row["car_id"],
            amount=float(row["amount"]),
            type=row["type"],
            created_on=row["created_on"]
        )

    def _get_columns(self):
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
            Column('station_id', Integer, ForeignKey('stations.id'), nullable=True),
            Column('car_id', Integer, ForeignKey('cars.id'), nullable=True),
            Column('amount', DECIMAL(10, 2), nullable=False),
            Column('type', Enum('TopUp', 'Payment', 'Refund', name='transaction_types'), nullable=False),
            Column('created_on', BigInteger, nullable=False, server_default=func.now())
        ]

    def get(self, transaction_id: int) -> Transaction:
        """
        Metoda pobiera transakcję o podanym identyfikatorze.

        Argumenty:
        - transaction_id (int): Identyfikator transakcji do pobrania.

        Zwraca:
        - Transaction: Obiekt transakcji lub None, jeśli transakcja nie została znaleziona.
        """
        return super().get(transaction_id)

    def get_all(self) -> list[Transaction]:
        """
        Metoda pobiera wszystkie transakcje.

        Zwraca:
        - list[Transaction]: Lista obiektów transakcji.
        """
        return super().get_all()

    def get_by_user(self, user_id: int) -> list[Transaction]:
        """
        Metoda pobiera wszystkie transakcje dla podanego użytkownika.

        Argumenty:
        - user_id (int): Identyfikator użytkownika.

        Zwraca:
        - list[Transaction]: Lista obiektów transakcji.
        """
        return [t for t in super().get_all() if t.user_id == user_id]

    def get_by_type(self, type: str) -> list[Transaction]:
        """
        Metoda pobiera wszystkie transakcje o podanym typie.

        Argumenty:
        - type (str): Typ transakcji.

        Zwraca:
        - list[Transaction]: Lista obiektów transakcji.
        """
        return [t for t in super().get_all() if t.type.lower() == type.lower()]

    def get_between(self, start: int, end: int, user_id: int | None = None) -> list[dict[str, User | Transaction]]:
        """
        Metoda pobiera informacje o transakcjach dla podanych dat.

        Argumenty:
        - start (int): Data początkowa w milisekundach.
        - end (int): Data końcowa w milisekundach.
        - user_id (int | None): Identyfikator użytkownika, dla którego pobieramy transakcje. Domyślnie None.

        Zwraca:
        - list[dict[str, User | Transaction]]: Lista obiektów transakcji.
        """
        if user_id is None:
             transactions = [{
                "user": self.user_service.get(t.user_id),
                "transaction": t
            } for t in self.get_all() if int(start) < int(t.created_on) / 1000 < int(end)]
        else:
            user = self.user_service.get(user_id)

            transactions = [{
                "user": user,
                "transaction": t
            } for t in self.get_by_user(user_id) if int(start) < int(t.created_on) / 1000 < int(end)]

        return sorted(transactions, key=lambda t: t["transaction"].created_on, reverse=True)

    def create_transaction(self, user_id: int,station_id: int, car_id: int, amount: float, type: str) -> Transaction | None:
        """
        Metoda tworzy nową transakcję.

        Argumenty:
        - user_id (int): Identyfikator użytkownika.
        - station_id (int): Identyfikator stacji.
        - car_id (int): Identyfikator samochodu.
        - amount (float): Kwota transakcji.
        - type (str): Typ transakcji.

        Zwraca:
        - Transaction: Obiekt transakcji.
        """
        session = self.Session()
        try:
            next_id = session.query(func.max(Transaction.id)).scalar() + 1 if session.query(Transaction.id).count() > 0 else 1
            
            new_transaction = Transaction(
                id=next_id,
                user_id=user_id,
                station_id=station_id,
                car_id=car_id,
                amount=amount,
                type=type
            )

            session.add(new_transaction)
            session.commit()
            transaction = session.merge(new_transaction)

            self.set(transaction.id, transaction)
            return new_transaction
        finally:
            session.close()

    def get_user_transactions(self, user_id: int) -> list[Transaction]:
        """
        Metoda pobiera wszystkie transakcje dla podanego użytkownika.

        Argumenty:
        - user_id (int): Identyfikator użytkownika.

        Zwraca:
        - list[Transaction]: Lista obiektów transakcji.
        """
        return [t for t in self.get_all() if t.user_id == user_id]

    def get_all_turnover(self) -> float:
        """
        Metoda pobiera cały obrót.

        Zwraca:
        - float: obrót.
        """
        return sum([t.amount for t in self.get_all() if t.type.lower() == "topup"])
