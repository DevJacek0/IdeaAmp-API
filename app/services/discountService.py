from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, func, BigInteger
from app.models.discount import Discount
from app import db
from app.services.service import Service
from datetime import datetime
from enum import Enum


class DiscountStatus(Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    EXPIRED = "expired"
    MAX_USES_REACHED = "max_uses_reached"
    ERROR = "error"


class DiscountService(Service):
    def __init__(self):
        """
        Konstruktor klasy DiscountService, który inicjalizuje klasę bazową Service.
        """
        super().__init__(
            table_name="discounts",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_discount
            }
        )
        self.DiscountStatus = DiscountStatus

    def _row_to_discount(self, row: dict) -> Discount:
        return Discount(
            id=row["id"],
            code=row["code"],
            value=float(row["value"]),
            expiry_on=row.get("expiry_on"),
            max_uses=row.get("max_uses"),
            usage_count=row.get("usage_count", 0)
        )

    def _get_columns(self):
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('code', String(50), nullable=False, unique=True),
            Column('value', DECIMAL(5, 2), nullable=False),
            Column('expiry_on', BigInteger, nullable=True),
            Column('usage_count', Integer, nullable=False, default=0),
            Column('max_uses', Integer, nullable=True)
        ]

    def get(self, discount_id: int) -> Discount:
        """
        Metoda pobierająca informacje o zniżce o podanym ID.

        Argumenty:
            discount_id (int): ID zniżki.

        Zwraca:
            Discount: Obiekt zniżki lub None, jeśli zniżka nie została znaleziona.
        """
        return super().get(discount_id)

    def get_all(self) -> list[Discount]:
        """
        Metoda pobierająca wszystkie znizki.

        Zwraca:
            list[Discount]: Lista obiektów znizek.
        """
        return super().get_all()

    def get_by_code(self, code: str) -> Discount:
        """
        Metoda pobierająca znizke o podanym kodzie.

        Argumenty:
            code (str): Kod zniżki.

        Zwraca:
            Discount: Obiekt zniżki lub None, jeśli zniżka nie została znaleziona.
        """
        return next((d for d in super().get_all() if d.code.lower() == code.lower()), None)

    def create_discount(self, code: str, value: float, expiry_on: int = None, max_uses: int = None) -> Discount:
        """
        Metoda tworząca nową znizke.

        Argumenty:
            code (str): Kod zniżki.
            value (float): Wartość zniżki (w procentach).
            expiry_on (int, opcjonalnie): Data wygaśnięcia zniżki jako unix timestamp.
            max_uses (int, opcjonalnie): Maksymalna liczba użytków znizki.

        Zwraca:
            Discount: Obiekt zniżki
        """
        try:
            next_id = db.session.query(func.max(Discount.id)).scalar()
            next_id = next_id + 1 if next_id is not None else 1

            new_discount = Discount(
                id=next_id,
                code=code,
                value=value,
                expiry_on=expiry_on,
                max_uses=max_uses,
                usage_count=0
            )

            db.session.add(new_discount)
            db.session.commit()

            self.set(next_id, new_discount)
            return new_discount
        except Exception as e:
            db.session.rollback()
            raise e

    def delete_discount(self, discount_id: int) -> bool:
        """
        Metoda usuwa znizke o podanym ID.

        Argumenty:
            discount_id (int): ID zniżki.

        Zwraca:
            bool: True, jesli znizka została usunieta, False w przeciwnym przypadku
        """
        try:
            discount = db.session.get(Discount, discount_id)
            if not discount:
                return False

            db.session.delete(discount)
            db.session.commit()

            self.clear(discount_id)
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def update_discount(self, discount_id: int, **kwargs):
        """
        Metoda aktualizuje znizke o podanym ID.

        Argumenty:
            discount_id (int): ID zniżki.
            **kwargs: Parametry aktualizacji znizki.

        Zwraca:
            Discount: Obiekt zniżki
        """
        session = self.Session()
        try:
            discount = session.query(Discount).get(discount_id)
            if not discount:
                return None

            for key, value in kwargs.items():
                if hasattr(discount, key):
                    setattr(discount, key, value)

            session.commit()

            refreshed_discount = session.merge(discount)
            self.set(refreshed_discount.id, refreshed_discount)
            return refreshed_discount
        finally:
            session.close()

    def apply_discount(self, amount: float, code: str) -> tuple[float, str, DiscountStatus]:
        """
        Aplikuje rabat do podanej kwoty.

        Argumenty:
            amount (float): Kwota do zrabatowania.
            code (str): Kod rabatowy.

        Zwraca:
            tuple[float, str, DiscountStatus]: Krotka zawierająca kwote rabatową, wiadomość o sukcesie oraz status
        """
        try:
            discount = db.session.query(Discount).filter(func.lower(Discount.code) == code.lower()).first()
            if not discount:
                return amount, "Nie znaleziono kodu rabatowego", DiscountStatus.NOT_FOUND

            if discount.expiry_on and datetime.utcnow() > discount.expiry_on:
                return amount, "Kod rabatowy wygasł", DiscountStatus.EXPIRED

            if discount.max_uses is not None and discount.usage_count >= discount.max_uses:
                return amount, "Kod rabatowy osiągnął maksymalną liczbę użyć", DiscountStatus.MAX_USES_REACHED

            discount.usage_count += 1

            db.session.commit()

            self.set(discount.id, discount)

            discounted_amount = amount * (1 - float(discount.value) / 100)
            print(discounted_amount)
            return discounted_amount, "Rabat został pomyślnie zastosowany", DiscountStatus.SUCCESS

        except Exception as e:
            db.session.rollback()
            raise e
