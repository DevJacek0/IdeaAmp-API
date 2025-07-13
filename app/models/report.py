from datetime import datetime

from app import db


class Report(db.Model):
    """
    Model dla raportów

    Atrybuty:
        id (int): Identyfikator raportu
        generated_by (int): Identyfikator użytkownika, który wygenerował raport
        type (str): Typ raportu
        generated_on (unix timestamp): Data wygenerowania raportu
        pdf_id (int): Identyfikator pliku PDF
    """
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.Enum('Usage', 'Cost', 'Statistics', 'Invoice', name='report_types'), nullable=False)
    generated_on = db.Column(db.BigInteger, nullable=False, default=lambda: int(datetime.utcnow().timestamp() * 1000))
    pdf_id = db.Column(db.Integer, nullable=False)

    def __init__(self, id, generated_by, type, pdf_id, generated_on=None):
        self.id = id
        self.generated_by = generated_by
        self.type = type
        self.pdf_id = pdf_id
        self.generated_on = generated_on

    def __repr__(self):
        return f"<Report(id={self.id}, type={self.type}, generated_by={self.generated_by})>"
