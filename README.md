# English Version / Wersja Angielska

# 🎾 Squash AI Coach

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

**Squash AI Coach** is an innovative analytics system designed for beginner and intermediate squash players. The application analyzes live match footage, tracks player movements, and uses the **Gemma 4 31B** AI model (with built-in fallback models) to provide valuable, concise tips regarding technique, footwork, and court positioning (e.g., the mandatory return to the "T").

**Players set up a phone or camera with a view of the court, and then each wears a single earpiece. During the match, the AI coach analyzes the video feed and communicates with them in real-time, delivering personalized audio feedback, e.g., "Peter - return to the T faster."**

The ready-to-use web application is available at: [https://squash-ai-coach.vercel.app](https://squash-ai-coach.vercel.app)

The system consists of two main components:
1. **Web Application (Frontend)**: The user interface operating as a PWA (Progressive Web App) that captures video from the camera.
2. **Server (Backend)**: A Python/FastAPI engine that processes the video stream and communicates with language models.

## 🚀 Key Features

- **Live Video Analysis:** Captures video straight from a phone or camera and instantly sends it for analysis.
- **Technique Evaluation:** Focuses on squash fundamentals: returning to the T, knee bend (lunge), safe distance, short swing.
- **Intelligent Audio Feedback (AI Coach):** Short, specific, personalized audio tips generated live by AI models straight to the player's earpiece.
- **PWA Application:** Can be "installed" on the phone's home screen for quick access.

## 🛠️ Architecture and Technologies

- **AI Engine:** Google Gemma 4 31B (and fallback models)
- **Backend:** Python, FastAPI, Uvicorn
- **Frontend:** Vanilla HTML, CSS, JavaScript (supporting WebSockets and Web Audio API)

## ⚙️ How to run the project?

You can easily use the already hosted frontend: [https://squash-ai-coach.vercel.app](https://squash-ai-coach.vercel.app)

However, your own backend instance is required for full functionality.

### 1. Running Backend on Hugging Face Spaces (Recommended)

The fastest way to get free backend hosting is by creating a Hugging Face Space.

1. Log in to your [Hugging Face](https://huggingface.co/) account.
2. Create a new **Space** and choose the **Docker** technology or a Python/FastAPI template.
3. Copy the files from this repository (the `backend/` folder) to your newly created Space.
4. Define the necessary secrets in your Space settings (e.g., API keys required for AI models).
5. Hugging Face will automatically build the environment. Copy the public URL of your Space and paste it into the "Settings" panel in the [Vercel app](https://squash-ai-coach.vercel.app).

### 2. Running Backend Locally (For developers)

```bash
git clone https://github.com/Dawe1600/Squash_Trener.git
cd Squash_Trener/backend

python -m venv .venv
# Activation (Windows)
.venv\Scripts\activate
# Activation (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
---

# Wersja Polska / Polish Version

# 🎾 Squash AI Coach

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

**Squash AI Coach** to innowacyjny system analityczny stworzony z myślą o początkujących i średniozaawansowanych graczach w squasha. Aplikacja analizuje nagrania z meczów w czasie rzeczywistym, śledzi ruchy zawodników i za pomocą modelu sztucznej inteligencji **Gemma 4 31B** (wraz z wbudowanymi zapasowymi modelami fallback) dostarcza cenne krótkie wskazówki dotyczące techniki, pracy nóg oraz pozycjonowania na korcie (np. obowiązkowy powrót na literę "T").

**Gracze ustawiają telefon lub kamerę z widokiem na kort, a następnie zakładają po jednej słuchawce. Podczas gry agent (Trener AI) analizuje obraz i komunikuje się z nimi na bieżąco, podając personalizowane uwagi, np. "Piotr - szybciej wracaj na T".**

Gotowa aplikacja webowa dostępna jest pod adresem: [https://squash-ai-coach.vercel.app](https://squash-ai-coach.vercel.app)

System składa się z dwóch części:
1. **Aplikacji Webowej (Frontend)**: Interfejsu użytkownika działającego jako PWA (Progressive Web App), który przechwytuje obraz z kamery.
2. **Serwera (Backend)**: Silnika w Pythonie/FastAPI przetwarzającego strumień wideo i komunikującego się z modelami językowymi.

## 🚀 Główne Funkcje

- **Analiza Wideo na Żywo:** Przechwytywanie wideo prosto z telefonu lub kamery i natychmiastowe przesyłanie do analizy.
- **Ocena Techniki:** Skupienie na fundamentach squasha: powrót na T, ugięcie kolan (lunge), bezpieczny odstęp, krótki zamach.
- **Inteligentne Wskazówki (AI Feedback) w słuchawce:** Krótkie i konkretne, dostosowane do gracza podpowiedzi głosowe generowane na żywo przez modele AI.
- **Aplikacja PWA:** Możliwość "zainstalowania" aplikacji na ekranie głównym telefonu dla szybszego dostępu.

## 🛠️ Architektura i Wykorzystane Technologie

- **AI Engine:** Google Gemma 4 31B (oraz modele zapasowe / fallback)
- **Backend:** Python, FastAPI, Uvicorn
- **Frontend:** Vanilla HTML, CSS, JavaScript (z obsługą WebSockets i Web Audio API)

## ⚙️ Jak uruchomić projekt?

Możesz w łatwy sposób skorzystać z już zahostowanego frontendu: [https://squash-ai-coach.vercel.app](https://squash-ai-coach.vercel.app)

Jednakże do pełnego działania wymagany jest Twój własny backend.

### 1. Uruchomienie Backendu na Hugging Face Spaces (Zalecane)

Najszybszym sposobem na darmowy hosting swojego backendu jest stworzenie instancji w serwisie Hugging Face.

1. Zaloguj się na swoje konto na [Hugging Face](https://huggingface.co/).
2. Utwórz nowy **Space** i wybierz technologię **Docker** lub bazujący na Python/FastAPI szablon.
3. Skopiuj pliki z tego repozytorium (folder `backend/`) do swojego nowo utworzonego Space.
4. Zdefiniuj odpowiednie sekrety (tzw. Secrets) w ustawieniach Twojego Space, w szczególności klucze API wymagane do działania modeli AI.
5. Hugging Face automatycznie zbuduje środowisko. Następnie skopiuj publiczny adres URL swojego serwera Space i wklej go w panelu "Ustawienia" w aplikacji [na Vercelu](https://squash-ai-coach.vercel.app).

### 2. Uruchomienie Backendu Lokalnie (Dla developerów)

```bash
git clone https://github.com/Dawe1600/Squash_Trener.git
cd Squash_Trener/backend

python -m venv .venv
# Aktywacja (Windows)
.venv\Scripts\activate
# Aktywacja (Linux/Mac)
source .venv/bin/activate

# Instalacja zależności
pip install -r requirements.txt

# Uruchomienie serwera
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## 📄 Licencja

Ten projekt jest udostępniany na licencji MIT. Szczegóły znajdziesz w pliku [LICENSE](LICENSE).
