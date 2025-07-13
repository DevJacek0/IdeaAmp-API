
def check_chargers_job():
    """
    Funkcja wykonywana co 24 godziny, loguje wszystkie stacje, które nie sa używane od 10 dni.
    """
    from app import create_app
    from app.services import AuditLogsService

    app = create_app()

    with app.app_context():
        audit_logs_service = AuditLogsService()
        audit_logs_service.check_unused_charges()


def init_check_chargers(scheduler):
    """
    Dodanie do schedulera funkcji wykonywanej co 24 godziny
    """
    scheduler.add_job(check_chargers_job, 'interval', hours=24)
