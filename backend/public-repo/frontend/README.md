# Squash AI Coach - Mobilny Klient PWA

Aplikacja mobilna (Progressive Web App - PWA) przeznaczona do uruchomienia bezpośrednio na korcie squasha. Aplikacja nagrywa obraz z kamery telefonu w wysokiej płynności (20-30 FPS), tnie wideo na małe, skompresowane paczki i przesyła je na backend, a po otrzymaniu analizy automatycznie odtwarza wskazówki taktyczne w słuchawkach graczy.

---

## ✨ Główne funkcje

* **Aplikacja PWA (Progressive Web App):** Możliwość zainstalowania bezpośrednio na ekranie głównym smartfona bez pośrednictwa sklepów App Store / Google Play.
* **Wybór kamer:** Lista wyboru pozwala przełączyć się na dowolny obiektyw w telefonie (w tym szerokokątny tylny obiektyw ułatwiający objęcie całego kortu).
* **MediaRecorder API (Płynność 20-30 FPS):** Nagrywanie wideo z optymalnym bitrate, dzielenie go w locie na 3-sekundowe segmenty i asynchroniczne wysyłanie przez żądania HTTP POST (Blob), co zapobiega utracie danych w przypadku słabszego sygnału internetowego (np. LTE wewnątrz budynku z kortami).
* **Automatyczne odtwarzanie wskazówek głosowych (iOS & Android):** System automatycznie obchodzi ograniczenia mobilnych przeglądarek blokujące autoodtwarzanie dźwięków. Pierwsze kliknięcie przycisku "Uruchom" odblokowuje kanał audio i pozwala na automatyczne odtworzenie plików `.mp3` otrzymanych przez WebSocket w tle.
* **Konfiguracja Graczy (Zwracanie się po imieniu):** Dedykowany formularz pozwala zdefiniować wygląd (np. kolor koszulki) i przypisać do niego imię gracza przed startem gry. Dzięki temu asystent AI zwraca się do konkretnych osób po imieniu zamiast poprzez długie opisy ubioru.
* **Nowoczesny design Glassmorphism:** Elegancki i responsywny interfejs z ciemnym motywem, rozmytymi elementami tła i animacjami nagrywania.

---

## 💻 Struktura plików

* **[index.html](file:///c:/Programowanie/Squash_Trener/frontend/index.html):** Główna struktura strony (podgląd wideo, karty wyników graczy, formularze ustawień).
* **[css/style.css](file:///c:/Programowanie/Squash_Trener/frontend/css/style.css):** Zbiór styli UI realizujących glassmorphic design, animacje pulsowania, loader oraz dostosowanie pod ekrany smartfonów.
* **[js/app.js](file:///c:/Programowanie/Squash_Trener/frontend/js/app.js):** Główny silnik aplikacji klienckiej (kamera, nagrywanie fragmentów, wysyłanie fetch POST, odbiór WebSocket, parsowanie JSON, odtwarzanie audio).
* **[manifest.json](file:///c:/Programowanie/Squash_Trener/frontend/manifest.json) & [sw.js](file:///c:/Programowanie/Squash_Trener/frontend/sw.js) & [js/pwa.js](file:///c:/Programowanie/Squash_Trener/frontend/js/pwa.js):** Skrypty i metadane niezbędne do prawidłowego funkcjonowania i rejestracji aplikacji jako PWA.

---

## 🛠️ Uruchomienie lokalne

Ponieważ przeglądarki ze względów bezpieczeństwa zezwalają na dostęp do kamery (`getUserMedia`) **wyłącznie** na adresie `localhost` oraz przez bezpieczne połączenie `HTTPS`, lokalne uruchomienie wymaga jednej z poniższych metod:

### Opcja 1: Uruchomienie lokalnego serwera statycznego
Możesz użyć dowolnego prostego serwera HTTP (np. z pakietu `npm`, Pythona czy rozszerzenia VS Code "Live Server").

Przykład przy użyciu Pythona (uruchom w katalogu `frontend/`):
```bash
python -m http.server 3000
```
Następnie otwórz przeglądarkę na komputerze pod adresem: `http://localhost:3000`.

### Opcja 2: Dostęp z telefonu (Testy na korcie)
Aby przetestować aplikację bezpośrednio na smartfonie, musisz hostować frontend przez bezpieczne połączenie **HTTPS**. Najprostszym sposobem jest skorzystanie z bezpłatnych platform hostingowych (patrz niżej).

---

## 🚀 Bezpłatne hostowanie (CI/CD)

### 1. Vercel (Rekomendowane)
Vercel automatycznie wdroży Twój frontend w kilkanaście sekund, wygeneruje darmowy certyfikat SSL (wymagany do HTTPS) i zaktualizuje stronę po każdym `git push`.
1. Wejdź na [vercel.com](https://vercel.com) i połącz swoje konto z GitHubem.
2. Kliknij **Add New -> Project** i zaimportuj repozytorium z Twoim frontendem (`frontend-trener-squash`).
3. Pozostaw ustawienia domyślne i kliknij **Deploy**.
4. Otrzymasz adres URL (np. `https://nazwa-projektu.vercel.app`), który możesz otworzyć na dowolnym smartfonie i zainstalować jako aplikację na pulpicie.

### 2. GitHub Pages
Możesz także skorzystać z darmowego hostowania bezpośrednio w GitHubie:
1. Przejdź do ustawień swojego repozytorium frontendu na GitHubie (**Settings -> Pages**).
2. W sekcji **Build and deployment** wybierz źródło: **Deploy from a branch**.
3. Jako gałąź wybierz `main` i folder `/ (root)`, a następnie kliknij **Save**.
4. GitHub Pages opublikuje stronę pod adresem `https://nazwa_uzytkownika.github.io/nazwa_repozytorium/` w ciągu minuty.
