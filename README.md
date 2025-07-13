# ⚡ IdeaAmp API

- Link do dokumentacji webowej: https://ozt-backend-docs.netlify.app/

# 🎯 Kluczowe funkcje:
## 🔌 Zarządzanie ładowaniem pojazdów
### `/chargings/`
- Rozpoczynanie i kończenie sesji ładowania  
- Pobieranie statusu sesji  
- Historia ładowania  

### `/stations/`
- Lista dostępnych stacji  
- Szczegóły pojedynczej stacji  
- Zarządzanie konfiguracją stacji  

### `/ports/`
- Lista portów w danej stacji  
- Status dostępności portów  

---

## 🚗 Zarządzanie pojazdami
### `/cars/`
- Rejestracja i edycja pojazdów użytkowników  
- Pobieranie informacji o pojazdach  
- Przypisanie pojazdu do użytkownika  

### `/points/` - Zaimplementowane jedynie w API
- Przypisywanie punktów dostępu do użytkowników  
- Rejestracja nowych punktów  


---

## 💰 Płatności i faktury
### `/transactions/`
- Tworzenie i pobieranie historii transakcji  
- Szczegóły płatności za ładowanie  

### `/invoices/`
- Generowanie faktur za sesje ładowania  
- Pobieranie faktur użytkownika  

---

## 📢 Powiadomienia i historia działań
### `/notifications/`
- Powiadomienia AI

### `/auditLogs/`
- Historia operacji użytkownika  
- Śledzenie zmian w systemie  

---

## ⚙️ Inne funkcje
### `/users/`
- Rejestracja i logowanie użytkowników  
- Pobieranie danych konta
- Edycja danych konta
- Resetowanie hasła
- Two factor authentication
- avatar upload
- Historia logowania

### `/backup/`
- Eksport danych  

### `/faq/`
- Zarządzanie listą ładowania

### `/websockets/`
- Komunikacja w czasie rzeczywistym  
- Aktualizacja statusu ładowania na żywo  

### `/decorators/`
- Walidacja admina  
- Paginacja 

### `/discounts/`
- Zarzadzanie rabatami

### `/reports/`
- Statystyki użytkowania stacji  
- Tworzenie i pobieranie raportów. 


---

# 🛡️ Użyte zabezpieczenia

## 🔐 JWT
JWT jest używany do autoryzacji użytkowników. Użytkownik musi się zalogować, aby korzystać z wszystkich funkcji API.

## ⏰ Kontrola timestampów
Przy każdym zapytaniu do API jest sprawdzany timestamp. Jesli timestamp jest starszy od 30 sekund, to zapytanie jest odrzucone.

---
# Technologie i biblioteki


| Technologia | Wersja | Opis                  | Zastosowanie                                                                  |
|-------------|--------|-----------------------|-------------------------------------------------------------------------------|
| Python | 3.11   | Język programowania   | Backend                                                                       |
| Flask | 3.1.0  | Framework dla Pythona | Główny framework backendu                                                     |
| Flask-Cors | 5.0.0  | Obsługa CORS          | Obsługa CORS, przydatne ze względu na różnice hostowania frontendu i backendu |
| Flask-JWT-Extended | 4.7.1  | Obsługa JWT | Obsługa JWT - głównego systemu autoryzacji                                    |
| Flask-SQLAlchemy | 3.1.1  | ORM           | Obsługa bazy danych z Flaskiem                                                |
| SQLAlchemy | 2.0.37 | ORM           | Obsługa bazy danych                                                           |
| flask-mail | 0.10.0 | Obsługa maila | Obsługa maila dla resetów hasła, przypominania hasła oraz 2FA                 |
| flask-migrate | 4.1.0  | Obsługa migracji | Obsługa migracji bazy danych                                                  |
| pymysql | 1.1.1  | Obsługa bazy danych | Obsługa bazy danych MySQL                                                     |
| python-dotenv | 1.0.1  | Obsługa plików .env | Obsługa plików .env                                                           |
| genai | 2.1.0  | Obsługa AI | Wykorzystanie sztucznej inteligencji, np. w ciekawostach AI                   |
| google-genai | 1.4.0  | Google AI | Integracja z modelami AI Google                                               |
| tiktoken | 0.9.0  | Tokenizacja tekstu | Obsługa tokenizacji dla modeli AI                                             |
| fpdf2 | 2.8.2  | Generowanie PDF | Tworzenie faktur i raportów użytkownika                                       |
| apscheduler | 3.11.0 | Harmonogram zadań | Wysyłanie powiadomień do logowania audytowanego                               |                                                            |

---
Więcej szczegółów znajdziesz w poniższej dokumentacji.