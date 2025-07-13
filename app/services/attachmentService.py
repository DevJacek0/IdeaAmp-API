import os
import uuid
from datetime import datetime

from flask import current_app
from werkzeug.utils import secure_filename
from sqlalchemy import Column, Integer, Text, TIMESTAMP, func
from app import db
from app.models.attachment import Attachment
from app.services.service import Service


class AttachmentsService(Service):
    def __init__(self):
        """
        Konstruktor klasy AttachmentsService, który inicjalizuje obiekty klasy Service i ustawia ścieżki do folderów z plikami.
        """

        self.UPLOAD_FOLDER = os.path.join(current_app.root_path,'attachments', 'all')
        self.AVATARS_FOLDER = os.path.join(current_app.root_path,'attachments', 'all', 'uploads', 'avatars')
        self.REPORTS_FOLDER_T = os.path.join(current_app.root_path,'attachments', 'all', 'reports', 'transactions')
        self.REPORTS_FOLDER_S = os.path.join(current_app.root_path,'attachments', 'all', 'reports', 'sessions')
        self.INVOICES_FOLDER = os.path.join(current_app.root_path,'attachments', 'all', 'invoices')
        self.ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(self.REPORTS_FOLDER_T, exist_ok=True)
        os.makedirs(self.REPORTS_FOLDER_S, exist_ok=True)
        os.makedirs(self.INVOICES_FOLDER, exist_ok=True)

        super().__init__(
            table_name="attachments",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_attachment
            }
        )

    def _row_to_attachment(self, row: dict) -> Attachment:
        return Attachment(
            id=row["id"],
            path=row["path"],
        )

    def _get_columns(self):
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('path', Text, nullable=False),
        ]

    def allowed_file(self, filename):
        """
        Sprawdza, czy plik ma prawidłowy format.

        Argumenty:
        - filename (str): Nazwa pliku.

        Zwraca:
        - bool: True, jesli plik ma prawidłowy format, False w przeciwnym przypadku.
        """
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def save_file(self, file):
        """
        Zapisuje plik na serwerze.

        Argumenty:
        - file (werkzeug.datastructures.FileStorage): Obiekt pliku.

        Zwraca:
        - Attachment: Obiekt Attachment z zapisanym plikiem.
        """
        session = self.Session()
        try:
            if file and self.allowed_file(file.filename):
                _, ext = os.path.splitext(secure_filename(file.filename))

                filename = f"{uuid.uuid4()}{ext}"

                file_path = os.path.join(self.AVATARS_FOLDER, filename)

                file.save(file_path)

                relative_path = os.path.join('uploads', 'avatars', filename)

                next_id = session.query(func.max(Attachment.id)).scalar()
                next_id = (next_id or 0) + 1

                attachment = Attachment(
                    id=next_id,
                    path=relative_path
                )

                session.add(attachment)
                session.commit()

                refreshed_attachment = session.query(Attachment).get(attachment.id)
                self.set(refreshed_attachment.id, refreshed_attachment)

                return refreshed_attachment
            return None

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_file_path(self, relative_path):
        """
        Zwraca ścieżkę do pliku na serwerze.

        Argumenty:
        - relative_path (str): Ścieżka do pliku względem katalogu głównego aplikacji.

        Zwraca:
        - str: Ścieżka do pliku na serwerze.
        """
        return os.path.join(current_app.root_path, relative_path)

    def delete_file(self, attachment_id):
        """
        Usuwa plik na serwerze.

        Argumenty:
        - attachment_id (int): Identyfikator pliku do usunięcia.

        Zwraca:
        - bool: True, jesli plik został usunięty, False w przeciwnym przypadku.
        """
        session = self.Session()
        try:
            attachment = session.query(Attachment).get(attachment_id)
            if attachment:
                full_path = self.get_file_path(attachment.path)

                if os.path.exists(full_path):
                    os.remove(full_path)

                session.delete(attachment)
                session.commit()

                self.clear(attachment_id)
                return True
            return False

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get(self, attachment_id):
        """
        Pobiera plik na serwerze.

        Argumenty:
        - attachment_id (int): Identyfikator pliku do pobrania.

        Zwraca:
        - Attachment: Obiekt Attachment z pobranym plikiem.
        """
        return super().get(attachment_id)

    def get_all(self):
        """
        Pobiera wszystkie pliki na serwerze.

        Zwraca:
        - list: Lista obiektów Attachment z pobranymi plikami.
        """
        return super().get_all()
