from datetime import datetime

from app import db


class Faq(db.Model):
    """
    Model dla pytań i odpowiedzi

    Atrybuty:
        id (int): Identyfikator pytań i odpowiedzi
        question (str): Pytanie
        answer (str): Odpowiedź
        user_id (int): Identyfikator użytkownika
        public (bool): Czy pytanie i odpowiedź jest publiczne
        created_on (unix timestamp): Data utworzenia
    """
    __tablename__ = "faq"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    public = db.Column(db.Boolean, nullable=False, default=False)
    created_on = db.Column(db.BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp() * 1000))

    def __init__(self, id: int, question: str, answer: str,public: bool,user_id: int, created_on=None):
        self.id = id
        self.question = question
        self.answer = answer
        self.public = public
        self.user_id = user_id
        self.created_on = created_on
