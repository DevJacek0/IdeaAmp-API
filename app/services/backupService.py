import os

import pymysql

from app import db


class BackupService:
    @staticmethod
    def create_backup():
        """Tworzy backup bazy MySQL.

        Zwraca:
        - `str`: Słownik z informacjami o baku bazy danych.
        - `None`: Jeśli wystąpi błąd.
        """
        try:
            engine_url = str(db.engine.url)

            file_path = os.path.join(os.getcwd(), "app", "attachments", "backup.sql")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            if not engine_url.startswith("mysql"):
                raise ValueError("Nieobsługiwany typ bazy danych.")

            user = db.engine.url.username
            password = db.engine.url.password or ""
            host = db.engine.url.host
            port = db.engine.url.port or 3306
            database = db.engine.url.database

            connection = pymysql.connect(
                host=host, user=user, password=password, database=database, port=port
            )

            with connection.cursor() as cursor, open(file_path, "w", encoding="utf-8") as backup_file:
                cursor.execute("SHOW TABLES;")
                tables = [table[0] for table in cursor.fetchall()]

                for table in tables:
                    cursor.execute(f"SHOW CREATE TABLE `{table}`;")
                    create_table_stmt = cursor.fetchone()[1]
                    backup_file.write(f"\nDROP TABLE IF EXISTS `{table}`;\n{create_table_stmt};\n\n")

                    cursor.execute(f"SELECT * FROM `{table}`;")
                    rows = cursor.fetchall()

                    if rows:
                        columns = [desc[0] for desc in cursor.description]
                        values = ",\n".join(
                            str(tuple(row)).replace("None", "NULL") for row in rows
                        )
                        insert_stmt = f"INSERT INTO `{table}` ({', '.join(columns)}) VALUES \n{values};\n\n"
                        backup_file.write(insert_stmt)

            connection.close()
            print(f"[Backup] MySQL database backup saved to {file_path}.")
            return file_path

        except Exception as e:
            print(f"[Backup] Błąd: {e}")
            return None
