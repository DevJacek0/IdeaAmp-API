import os
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, String, Enum, Text, TIMESTAMP, func, ForeignKey, BigInteger

from app.models.car import Car
from app.models.chargingSession import ChargingSession
from app.models.pdf import ReportPDF, InvoicePDF
from app.models.report import Report
from app.models.transaction import Transaction
from app.models.user import User
from app.services import AttachmentsService, UsersService
from app.services.service import Service


class ReportsService(Service):
    def __init__(self):
        """
        Konstruktor klasy ReportsService, który inicjalizuje klasę bazową Service.
        """
        super().__init__(
            table_name="reports",
            load_recipe={
                "identifier": "id",
                "function": self._row_to_report
            }
        )
        self.attachments_service = AttachmentsService()
        self.users_service = UsersService()

    def _row_to_report(self, row: dict) -> Report:
        return Report(
            id=row["id"],
            generated_by=row["generated_by"],
            type=row["type"],
            generated_on=row["generated_on"],
            pdf_id=row["pdf_id"]
        )

    def _get_columns(self):
        return [
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('generated_by', Integer, ForeignKey('users.id'), nullable=False),
            Column('type', Enum('Usage', 'Cost', 'Statistics', 'Invoice', name='report_types'), nullable=False),
            Column('generated_on', BigInteger, nullable=False, server_default=func.now()),
            Column('pdf_id', Integer, nullable=False)
        ]

    def get(self, report_id: int):
        """
        Pobiera raport o podanym identyfikatorze.

        Argumenty:
        - report_id (int): Identyfikator raportu do pobrania.

        Zwraca:
        - Report: Obiekt raportu lub None, jesli raport nie został znaleziony.
        """
        return super().get(report_id)

    def get_all(self):
        """
        Pobiera wszystkie raporty.

        Zwraca:
        - List[Report]: Lista obiektów raportów.
        """
        return super().get_all()

    def get_by_user(self, user_id: int):
        """
        Pobiera raporty dla podanego identyfikatora użytkownika.

        Argumenty:
        - user_id (int): Identyfikator użytkownika.

        Zwraca:
        - List[Report]: Lista obiektów raportów dla podanego użytkownika.
        """
        return [report for report in self.get_all() if report.generated_by == user_id]

    def get_by_type(self, report_type: str):
        """
        Pobiera raporty o podanym typie.

        Argumenty:
        - report_type (str): Typ raportu.

        Zwraca:
        - List[Report]: Lista obiektów raportów o podanym typie.
        """
        return [report for report in self.get_all() if report.type.lower() == report_type.lower()]

    def create_report(self, generated_by: int, report_type: str) -> Report | None:
        """
        Tworzy nowy raport.

        Argumenty:
        - generated_by (int): Identyfikator użytkownika, który wygenerował raport.
        - report_type (str): Typ raportu.

        Zwraca:
        - Report: Obiekt raportu.
        """
        session = self.Session()
        try:
            next_id = session.query(func.max(Report.id)).scalar() + 1 if session.query(Report.id).count() > 0 else 1
            pdf_id = session.query(func.max(Report.pdf_id)).scalar() + 1 if session.query(
                Report.pdf_id).count() > 0 else 1

            new_report = Report(
                id=next_id,
                generated_by=generated_by,
                type=report_type,
                pdf_id=pdf_id
            )

            session.add(new_report)
            session.commit()

            self.set(new_report.id, new_report)
            return new_report
        finally:
            session.close()

    @staticmethod
    def parse_date_params(start_date: str = None, end_date: str = None) -> tuple[datetime, datetime]:
        """
        Metoda pomocnicza, która parsuje parametry dat do generowania raportów.

        Argumenty:
        - start_date (str): Data początkowa.
        - end_date (str): Data koncowa.

        Zwraca:
        - Tuple[datetime, datetime]: Krotka zawierająca daty początkową i koncą.
        """

        try:
            if not start_date or not end_date:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
            else:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')

            return start_date, end_date
        except ValueError:
            raise ValueError("Nieprawidłowy format daty. Wymagany format: YYYY-MM-DD")

    @staticmethod
    def calculate_peak_hours(sessions: list) -> list:
        """
        Metoda pomocnicza, która oblicza najpopularniejsze godziny ładowania.

        Argumenty:
        - sessions (list): Lista obiektów sesji ładowania.

        Zwraca:
        - List[Tuple[int, int]]: Lista krotków zawierających godziny ładowania i liczbę sesji ładowania w danej godzinie.
        """

        hour_usage = {}
        for session in sessions:
            started_on = int(session["session"].started_on) / 1000
            hour = datetime.fromtimestamp(started_on).hour
            hour_usage[hour] = hour_usage.get(hour, 0) + 1
        return sorted(hour_usage.items(), key=lambda x: x[1], reverse=True)[:3]

    def generate_transactions_report(self, transactions: list[dict[str, User | Transaction]], timestamp_from: int,
                                     timestamp_to: int, generated_by: int) -> int:

        """
        Generuje raport transakcji.

        Argumenty:
        - transactions (list[dict[str, User | Transaction]]): Lista obiektów transakcji.
        - timestamp_from (int): Data początkowa w milisekundach.
        - timestamp_to (int): Data koncowa w milisekundach.
        - generated_by (int): Identyfikator użytkownika, który wygenerował raport.

        Zwraca:
        - int: Identyfikator utworzonego raportu.
        """
        report: Report = self.create_report(generated_by, 'Cost')
        user: User = self.users_service.get(generated_by)

        pdf: ReportPDF = ReportPDF(f'Raport transakcji nr. {report.pdf_id}',
                       f"{user.first_name} {user.last_name}",
                                   datetime.now().strftime("%d-%m-%Y"),
                                   datetime.fromtimestamp(timestamp_from).strftime("%d-%m-%Y"),
                                   datetime.fromtimestamp(timestamp_to).strftime("%d-%m-%Y")
                                   )
        pdf.add_page()
        pdf.set_font("MonaSans", "", 11)

        with pdf.table() as table:
            row = table.row()
            row.cell("Imię")
            row.cell("Nazwisko")
            row.cell("Typ transakcji")
            row.cell("Data transakcji")
            row.cell("Wartość transakcji")

            total: float = 0
            for transaction in transactions:
                t: Transaction = transaction.get("transaction")
                u: User = transaction.get("user")
                date: str = datetime.fromtimestamp(t.created_on / 1000).strftime("%d-%m-%Y %H:%M")

                row = table.row()
                row.cell(u.first_name)
                row.cell(u.last_name)
                row.cell(t.type)
                row.cell(date)
                row.cell(str(abs(t.amount)))

                total += abs(t.amount)

            pdf.set_font("MonaSans", "B", 12)
            row = table.row()
            row.cell("Suma", colspan=4)
            row.cell(str(total))

        pdf_path = self.attachments_service.get_file_path(
            rf"attachments/all/reports/transactions/report_{report.pdf_id}.pdf")

        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        pdf.output(pdf_path)

        return report.id

    def generate_sessions_report(self, sessions: list[dict[str, User | ChargingSession]], timestamp_from: int,
                                 timestamp_to: int, generated_by: int) -> int:

        """
        Generuje raport sesji ładowania.

        Argumenty:
        - sessions (list[dict[str, User | ChargingSession]]): Lista obiektów sesji ładowania.
        - timestamp_from (int): Data początkowa w milisekundach.
        - timestamp_to (int): Data koncowa w milisekundach.
        - generated_by (int): Identyfikator użytkownika, który wygenerował raport.

        Zwraca:
        - int: Identyfikator utworzonego raportu.
        """
        report: Report = self.create_report(generated_by, 'Usage')
        user: User = self.users_service.get(generated_by)

        pdf: ReportPDF = ReportPDF(f'Raport sesji ładowania nr. {report.pdf_id}',
                       f"{user.first_name} {user.last_name}",
                                   datetime.now().strftime("%d-%m-%Y"),
                                   datetime.fromtimestamp(timestamp_from).strftime("%d-%m-%Y"),
                                   datetime.fromtimestamp(timestamp_to).strftime("%d-%m-%Y")
                                   )
        pdf.add_page()
        pdf.set_font("MonaSans", "", 9)

        with pdf.table() as table:
            row = table.row()
            row.cell("Imię")
            row.cell("Nazwisko")
            row.cell("Nr. rejestracyjne")
            row.cell("Data rozpoczęcia")
            row.cell("Data zakończenia")
            row.cell("Zużyta energia")
            row.cell("Koszt")

            total_energy: float = 0
            total_cost: float = 0
            for session in sessions:
                s: ChargingSession = session.get("session")
                u: User = session.get("user")
                c: Car = session.get("car")
                start_date: str = datetime.fromtimestamp(s.started_on / 1000).strftime("%d-%m-%Y %H:%M")
                end_date: str = datetime.fromtimestamp(s.end_on / 1000).strftime("%d-%m-%Y %H:%M")

                row = table.row()
                row.cell(u.first_name)
                row.cell(u.last_name)
                row.cell(c.plate)
                row.cell(start_date)
                row.cell(end_date)
                row.cell(str(s.energy_consumed))
                row.cell(str(s.cost))

                total_energy += s.energy_consumed
                total_cost += s.cost

            pdf.set_font("MonaSans", "B", 12)
            row = table.row()
            row.cell("Suma", colspan=5)
            row.cell(str(total_energy))
            row.cell(str(total_cost))

        pdf_path: str = self.attachments_service.get_file_path(
            rf"attachments/all/reports/sessions/report_{report.pdf_id}.pdf")

        pdf.output(pdf_path)

        return report.id

    def generate_invoice(self, transactions: list[Transaction], user: User, generated_by: int) -> int:

        """
        Generuje fakturę VAT.

        Argumenty:
        - transactions (list[Transaction]): Lista obiektów transakcji.
        - user (User): Obiekt użytkownika.
        - generated_by (int): Identyfikator użytkownika, który wygenerował fakturę.

        Zwraca:
        - int: Identyfikator utworzonej faktury VAT.
        """
        invoice: Report = self.create_report(generated_by, 'Invoice')

        pdf: InvoicePDF = InvoicePDF(f'Faktura VAT nr. {invoice.pdf_id}', datetime.fromtimestamp(invoice.generated_on / 1000).strftime("%d-%m-%Y"), user)

        pdf.add_page()
        pdf.set_font("MonaSans", "", 9)


        with pdf.table(col_widths=(10, 100, 30, 20, 30, 30)) as table:
            row = table.row()
            row.cell("Lp.")
            row.cell("Nazwa")
            row.cell("Cena brutto")
            row.cell("VAT (%)")
            row.cell("Wartość netto")
            row.cell("VAT")

            total_brutto, total_netto, total_vat = 0, 0, 0
            for i, transaction in enumerate(transactions):
                brutto: float = abs(transaction.amount)
                netto: float = brutto / 1.08
                vat: float = 0.08 * netto

                row = table.row()
                row.cell(f"{i + 1}")
                row.cell("Ładowanie samochodu elektrycznego")
                row.cell(f"{brutto} PLN")
                row.cell("8")
                row.cell(f"{netto:.2f} PLN")
                row.cell(f"{vat:.2f} PLN")

                total_brutto += brutto
                total_netto += netto
                total_vat += vat

            pdf.set_font("MonaSans", "B", 9)
            row = table.row()
            row.cell("", border=0)
            row.cell(f"Razem")
            row.cell(f"{total_brutto} PLN")
            row.cell("-")
            row.cell(f"{total_netto:.2f} PLN")
            row.cell(f"{total_vat:.2f} PLN")


        pdf_path: str = self.attachments_service.get_file_path(
            rf"attachments/all/invoices/invoice_{invoice.pdf_id}.pdf")

        pdf.output(pdf_path)

        return invoice.id

    @staticmethod
    def format_peak_hours(peak_hours: list) -> dict:
        """
        Formatuje dane o godzinach maksymalnych zuzycia.

        Argumenty:
        - peak_hours (list): Lista obiektów zawierających informacje o godzinach maksymalnych zuzycia.

        Zwraca:
        - dict: Slownik z formatowanymi danymi o godzinach maksymalnych zuzycia.
        """

        return {
            "peak_hours": [
                {"hour": hour, "usage": usage} for hour, usage in peak_hours
            ]
        }
