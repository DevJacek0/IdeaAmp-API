from app import config
from app.services import UsersService, CarsService
from google import genai


class NotificationService:
    def __init__(self):
        """
        Konstruktor klasy NotificationService
        """
        self.user_service = UsersService()
        self.car_service = CarsService()

    def generate_notification(self, car_id: int):
        """
        Generuje powiadomienie o samochodzie elektrycznym

        Argumenty:
            car_id (int): ID pojazdu, którego powiadomienie chcemy wygenerować

        Zwraca:
            str: Powiadomienie o samochodzie elektrycznym
        """
        car = self.car_service.get(car_id)
        if not car:
            return False

        car_name = car.name
        if not car_name:
            return False

        ai_api_key = config.get_config().AI_API_KEY

        client = genai.Client(api_key=ai_api_key)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=(
                f"Podaj krótką, użyteczną ciekawostkę o samochodzie elektrycznym {car_name} w języku polskim. "
                f"Ciekawostka powinna być interesująca, praktyczna i zmieścić się w powiadomieniu push na telefonie. "
                f"Zacznij od: 'Czy wiesz, że Twój samochód - {car_name}...', a następnie podaj treść. "
                f"Odpowiedź ma być tylko samym tekstem ciekawostki, bez dodatkowych informacji."
            ))

        fact = response.text.strip()
        return fact






