from app.services.attachmentService import AttachmentsService
from app.services.carService import CarsService
from app.services.faqService import FaqService
from app.services.pointThresholdService import PointThresholdService
from app.services.stationService import StationService
from app.services.userService import UsersService
from app.services.auditLogService import AuditLogsService
from app.services.chargingSessionService import ChargingSessionsService
from app.services.portService import PortService
from app.services.reportsService import ReportsService
from app.services.transactionService import TransactionService
from app.services.discountService import DiscountService

cars_service = CarsService()
users_service = UsersService()
audit_logs_service = AuditLogsService()
charging_sessions_service = ChargingSessionsService()
attachments_service = AttachmentsService()
station_service = StationService()
ports_service = PortService()
reports_service = ReportsService()
transaction_service = TransactionService()
discounts_service = DiscountService(),
points_service = PointThresholdService()
faq_service = FaqService()
