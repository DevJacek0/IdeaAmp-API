from fpdf import FPDF, Align

from app.models.user import User
from app.services import AttachmentsService

class PDF(FPDF):
    """
    Klasa przechowująca ustawienia PDF
    """
    def __init__(self):
        super().__init__()
        attachment_service: AttachmentsService = AttachmentsService()
        self.add_font("MonaSans", "", attachment_service.get_file_path(r"attachments/fonts/MonaSans.ttf"), uni=True)
        self.add_font("MonaSans", "B", attachment_service.get_file_path(r"attachments/fonts/MonaSans-Bold.ttf"), uni=True)

class ReportPDF(PDF):
    def __init__(self, header: str, generated_by: str, generated_on: str, from_date: str, to_date: str):
        super().__init__()
        self._header = header
        self._generated_by = generated_by
        self._generated_on = generated_on
        self._from_date = from_date
        self._to_date = to_date

    def header(self):
        self.set_font("MonaSans", "B", 30)
        self.cell(0, 10, self._header, 0, 1, 'C')
        self.ln(10)

        self.set_font("MonaSans", "", 12)
        self.cell(0, 7, f"Wygenerowany przez: {self._generated_by}", 0, 1, 'L')
        self.cell(0, 7, f"Wygenerowany dnia: {self._generated_on}", 0, 1, 'L')
        self.cell(0, 7, f"Zakres: od {self._from_date} do {self._to_date}", 0, 1, 'L')
        self.ln(10)

class InvoicePDF(PDF):
    _SELLER_NAME: str = "IdeaAmp"
    _SELLER_ADDRESS: str = "ul. Podhalańska 2"
    _SELLER_POSTAL_CODE: str = "80-322"
    _SELLER_CITY: str = "Gdańsk"
    _SELLER_COUNTRY: str = "Polska"

    def __init__(self, header: str, generated_on: str, buyer: User):
        super().__init__()
        self.attachment_service: AttachmentsService = AttachmentsService()
        self._header = header
        self._first_name = buyer.first_name
        self._last_name = buyer.last_name
        self._address = buyer.address_line1
        self._city = buyer.city
        self._postal_code = buyer.postal_code
        self._country = buyer.country
        self._creation_date = generated_on

    def header(self):
        self.image(
            self.attachment_service.get_file_path(r"attachments/logo_b.png"),
            x=Align.L, w=33, h=28, alt_text=self._SELLER_NAME
        )
        self.ln(10)

        self.set_font("MonaSans", "B", 20)
        self.cell(0, 10, self._header, 0, 1, 'C')
        self.set_font("MonaSans", "B", 12)
        self.cell(0, 10, f"Z dnia {self._creation_date}", 0, 1, 'C')
        self.ln(10)

        self.set_font("MonaSans", "B", 12)
        with self.table() as table:
            row = table.row()
            row.cell("Sprzedawca", border=0)
            row.cell("Nabywca", border=0)

            self.set_font("MonaSans", "", 12)
            row = table.row()
            row.cell(f"{self._SELLER_NAME}", border=0)
            row.cell(f"{self._first_name} {self._last_name}", border=0)
            row = table.row()
            row.cell(f"{self._SELLER_ADDRESS}", border=0)
            row.cell(f"{self._address}", border=0)
            row = table.row()
            row.cell(f"{self._SELLER_POSTAL_CODE} {self._SELLER_CITY}, {self._SELLER_COUNTRY}", border=0)
            row.cell(f"{self._postal_code} {self._city}, {self._country}", border=0)

        self.ln(10)