from datetime import datetime

from sqlalchemy import Column, Integer, String, BigInteger, func, ForeignKey, Boolean, Text

from app import db
from app.models.faq import Faq
from app.services.service import Service


class FaqService(Service):
    def __init__(self):
        """
        Konstruktor klasy FaqService, który inicjalizuje klasę bazową Service.
        """
        super().__init__(
            table_name="faq",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_faq
            }
        )

    def _row_to_faq(self, row: dict) -> Faq:
        return Faq(
            id=row["id"],
            question=row["question"],
            answer=row["answer"],
            public=row["public"],
            user_id=row["user_id"],
            created_on=row["created_on"]
        )

    def _get_columns(self):
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('question', Text, nullable=False),
            Column('answer', Text, nullable=False),
            Column('public', Boolean, nullable=False, default=False),
            Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
            Column('created_on', BigInteger, nullable=False, server_default=func.now())
        ]

    def get(self, faq_id: int):
        """
        Pobiera FAQ o podanym ID.

        Argumenty:
            faq_id (int): ID FAQ, który chcemy pobrać.

        Zwraca:
            Faq: Obiekt FAQ
        """
        return super().get(faq_id)

    def get_all(self):
        """
        Pobiera wszystkie FAQ.

        Zwraca:
            list[Faq]: Lista FAQ
        """
        return super().get_all()

    def get_by_question(self, question: str):
        """
        Pobiera FAQ o podanej treści pytania.

        Argumenty:
            question (str): Treść pytania, które chcemy pobrać.

        Zwraca:
            list[Faq]: Lista FAQ
        """
        return [faq for faq in super().get_all() if faq.question.lower() == question.lower()]

    def get_by_answer(self, answer: str):
        """
        Pobiera FAQ o podanej treści odpowiedzi.

        Argumenty:
            answer (str): Treść odpowiedzi, którą chcemy pobrać.

        Zwraca:
            list[Faq]: Lista FAQ
        """
        return [faq for faq in super().get_all() if faq.answer.lower() == answer.lower()]

    def get_by_user(self, user_id: int):
        """
        Pobiera FAQ o podanym ID użytkownika.

        Argumenty:
            user_id (int): ID użytkownika, którego FAQ chcemy pobrać.

        Zwraca:
            list[Faq]: Lista FAQ
        """
        return [faq for faq in super().get_all() if faq.user_id == user_id]

    def create(self, user_id: int, question: str, answer: str, public: bool = False):
        """
        Tworzy nowy FAQ.

        Argumenty:
            user_id (int): ID użytkownika, który stworzył FAQ.
            question (str): Treść pytania.
            answer (str): Treść odpowiedzi.
            public (bool, opcjonalnie): Czy FAQ jest publiczne.

        Zwraca:
            Faq: Obiekt FAQ
        """
        session = self.Session()
        try:
            next_id = session.query(func.max(Faq.id)).scalar() + 1 if session.query(Faq.id).count() > 0 else 1
            new_faq = Faq(
                id=next_id,
                question=question,
                answer=answer,
                user_id=user_id,
                public=public,
                created_on=BigInteger().python_type(int(datetime.utcnow().timestamp() * 1000))
            )

            session.add(new_faq)
            session.commit()

            self.set(new_faq.id, new_faq)
            return new_faq
        finally:
            session.close()

    def add_question(self, user_id: int, question: str):
        """
        Dodaje pytanie do FAQ.

        Argumenty:
            user_id (int): ID użytkownika, który stworzył pytanie.
            question (str): Treść pytania.

        Zwraca:
            Faq: Obiekt FAQ
        """
        session = self.Session()
        try:
            next_id = db.session.query(func.max(Faq.id)).scalar() + 1 if db.session.query(Faq.id).count() > 0 else 1
            new_faq = Faq(
                id=next_id,
                question=question,
                answer="",
                user_id=user_id,
                public=False,
                created_on=BigInteger().python_type(int(datetime.utcnow().timestamp() * 1000))
            )

            session.add(new_faq)
            session.commit()

            self.set(new_faq.id, new_faq)
            return new_faq
        finally:
            session.close()

    def add_answer(self, faq_id: int, answer: str):
        """
        Dodaje odpowiedź do FAQ.

        Argumenty:
            faq_id (int): ID FAQ, do którego dodajemy odpowiedź.
            answer (str): Treść odpowiedzi.

        Zwraca:
            Faq: Obiekt FAQ
        """
        session = self.Session()
        try:
            faq = session.query(Faq).get(faq_id)
            if faq:
                faq.answer = answer
                session.commit()

                faq = session.merge(faq)
                self.set(faq.id, faq)
                return faq
            return False
        finally:
            session.close()

    def delete(self, faq_id: int):
        """
        Usuwa FAQ o podanym ID.

        Argumenty:
            faq_id (int): ID FAQ, który chcemy usunąć.

        Zwraca:
            bool: True jeśli FAQ zostało usunięte, False jeśli FAQ nie istnieje
        """
        session = self.Session()
        try:
            faq = session.query(Faq).get(faq_id)
            if faq:
                session.delete(faq)
                session.commit()
                self.clear(faq_id)
                return True
            return False
        finally:
            session.close()

    def update(self, faq_id: int, question: str, answer: str, public: bool = False):
        """
        Aktualizuje FAQ o podanym ID.

        Argumenty:
            faq_id (int): ID FAQ, który chcemy aktualizować.
            question (str): Treść pytania.
            answer (str): Treść odpowiedzi.
            public (bool, opcjonalnie): Czy FAQ jest publiczne.

        Zwraca:
            Faq: Obiekt FAQ
        """
        session = self.Session()
        try:
            faq = session.query(Faq).get(faq_id)
            if faq:
                faq.question = question
                faq.answer = answer
                faq.public = public
                session.commit()

                faq = session.merge(faq)
                self.set(faq.id, faq)
                return faq
            return False
        finally:
            session.close()

    def update_question(self, faq_id: int, question: str):
        """
        Aktualizuje pytanie FAQ o podanym ID.

        Argumenty:
            faq_id (int): ID FAQ, który chcemy aktualizować.
            question (str): Treść pytania.

        Zwraca:
            Faq: Obiekt FAQ
        """
        session = self.Session()
        try:
            faq = session.query(Faq).get(faq_id)
            if faq:
                faq.question = question
                session.commit()

                faq = session.merge(faq)
                self.set(faq.id, faq)
                return faq
            return False
        finally:
            session.close()

    def update_answer(self, faq_id: int, answer: str):
        """
        Aktualizuje odpowiedź FAQ o podanym ID.

        Argumenty:
            faq_id (int): ID FAQ, który chcemy aktualizować.
            answer (str): Treść odpowiedzi.

        Zwraca:
            Faq: Obiekt FAQ
        """
        session = self.Session()
        try:
            faq = session.query(Faq).get(faq_id)
            if faq:
                faq.answer = answer
                session.commit()

                faq = session.merge(faq)
                self.set(faq.id, faq)
                return faq
            return False
        finally:
            session.close()

    def publish(self, faq_id: int):
        """
        Publikuje FAQ o podanym ID.

        Argumenty:
            faq_id (int): ID FAQ, który chcemy publikować.

        Zwraca:
            Faq: Obiekt FAQ
        """
        session = self.Session()
        try:
            faq = session.query(Faq).get(faq_id)
            if faq:
                faq.public = True
                session.commit()

                faq = session.merge(faq)
                self.set(faq.id, faq)
                return faq
            return False
        finally:
            session.close()

    def to_dict(self, faq: Faq):
        """
        Metoda pomocnicza, która konwertuje obiekt FAQ do słownika.

        Argumenty:
            faq (Faq): Obiekt FAQ.

        Zwraca:
            dict: Słownik z informacjami o FAQ
        """
        return {
            "id": faq.id,
            "question": faq.question,
            "answer": faq.answer,
            "public": faq.public,
            "user_id": faq.user_id,
            "created_on": faq.created_on
        }