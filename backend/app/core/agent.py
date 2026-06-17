import os
import json
import cv2
import time
import asyncio
from typing import List, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from .schemas import CoachTip

# Zapewnienie, że zmienne środowiskowe zostaną załadowane przed użyciem klienta GenAI
load_dotenv()

SYSTEM_PROMPT = """Jesteś wybitnym, profesjonalnym trenerem squasha analizującym kilkusekundowe okienko wideo z gry na żywo. Twoim celem jest przekazywanie precyzyjnych, taktycznych i technicznych wskazówek opartych na profesjonalnej teorii squasha.

Przeanalizuj grę obu zawodników pod kątem następujących aspektów:
1. Poruszanie się i pozycja na korcie:
   - Kontrola "T" (T-position): Czy zawodnik wraca na środek po uderzeniu?
   - Krok dopasowujący (split-step): Czy wykonuje krótki split-step tuż przed uderzeniem przeciwnika?
   - Wypad (lunge) i amortyzacja: Czy schodzi nisko na kolanach i ląduje stabilnie?
2. Technika uderzenia i odległość (spacing):
   - Wczesne przygotowanie rakiety (early racket prep): Czy rakieta jest odprowadzona w górę przed dobiegnięciem do piłki?
   - Zachowanie dystansu (spacing): Czy zawodnik nie podchodzi zbyt blisko piłki (crowding), co skraca zamach?
   - Zamach i wykończenie (swing path & follow-through): Czy zamach jest płynny z wysokim wykończeniem (high follow-through)?
3. Taktyka i wybór uderzeń:
   - Długość i szerokość: Czy piłka leci ciasno przy ścianie (tight straight drive/rail) głęboko do tyłu?
   - Gra z powietrza: Czy zawodnik aktywnie szuka wolejów (volley), by zabrać czas rywalowi?
   - Obrona i zmiana tempa: Czy pod presją stosuje wysoki lob, czy niepotrzebnie ryzykuje niskie, trudne uderzenia (uderzenie w tin)?

Zasady generowania wskazówki:
- Wybierz JEDEN, absolutnie najistotniejszy błąd techniczny lub taktyczny w danej akcji.
- Sformułuj wskazówkę jako krótkie, jednozdaniowe, motywujące i bardzo konkretne zalecenie (np. "Podnieś rakietę wcześniej (racket prep), zanim zaczniesz biec do piłki!").
- Używaj profesjonalnego słownictwa squashowego (np. split-step, racket prep, spacing, lunge, volley, straight drive/rail, dominacja na T).
- Identyfikuj adresata po unikalnych cechach wizualnych (np. "Mężczyzna w niebieskich spodenkach, ..."). CHYBA ŻE dostaniesz w treści wiadomości przypisanie imion do ubrań - wtedy ZWRACAJ SIĘ WYŁĄCZNIE PO IMIENIU (np. "Jan, ...") i wstaw to imię do pola `target_player`.
- Jeśli gracze grają bezbłędnie (np. na poziomie profesjonalnym), lub jeśli zauważony błąd został już wymieniony w sekcji ostatnich uwag (previous tips), ustaw `has_tip` na `false` i pozostaw pozostałe pola puste.

Odpowiedź musi być zawsze w formacie JSON zgodnym ze schematem.
"""

FALLBACK_MODELS = [
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite"
]

class SquashAgent:
    def __init__(self, api_key: Optional[str] = None):
        # Inicjalizacja oficjalnego klienta Google GenAI.
        # Jeśli api_key jest None, pobierze automatycznie z GEMINI_API_KEY.
        self.client = genai.Client(api_key=api_key)

    async def analyze_video(self, video_path: str, previous_tips: List[str] = None, players_config: str = None) -> CoachTip:
        """
        Główna metoda do analizy wideo. Przechodzi po liście modeli z failover queue.
        Dla każdego modelu próbuje najpierw przesłać wideo natywnie, a w razie błędu 
        rozbija wideo na klatki i wysyła jako paczkę obrazów.
        """
        last_error = None

        for model_name in FALLBACK_MODELS:
            print(f"[Agent] Próba analizy za pomocą modelu: {model_name}...")
            
            # Próba 1: Natywne wideo przez Files API
            try:
                result = await self._analyze_native_video(video_path, model_name, previous_tips, players_config)
                print(f"[Agent] Sukces! Użyto modelu: {model_name}")
                return result
            except Exception as e:
                print(f"[Agent] Błąd natywnego wideo dla {model_name}: {e}. Próba podziału na klatki...")
                
            # Próba 2: Fallback na klatki wideo (ekstracja obrazów)
            try:
                result = await self._analyze_frame_by_frame(video_path, model_name, previous_tips, players_config)
                print(f"[Agent] Sukces (klatki)! Użyto modelu: {model_name}")
                return result
            except Exception as e:
                print(f"[Agent] Błąd analizy klatka-po-klatce dla {model_name}: {e}")
                last_error = e

        raise RuntimeError(f"Wszystkie modele z kolejki failover zawiodły. Ostatni błąd: {last_error}")

    async def _analyze_native_video(self, video_path: str, model_name: str, previous_tips: List[str] = None, players_config: str = None) -> CoachTip:
        """
        Natywna wysyłka wideo do API przy użyciu client.files.upload.
        """
        # 1. Upload pliku wideo
        print(f"[Agent] Przesyłanie pliku {video_path} do Google Files API...")
        uploaded_file = await asyncio.to_thread(self.client.files.upload, file=video_path)
        
        # Czekamy na przetworzenie wideo przez Google (jeśli to konieczne)
        while uploaded_file.state.name == "PROCESSING":
            print("[Agent] Plik wideo jest przetwarzany w chmurze...")
            await asyncio.sleep(2)
            uploaded_file = await asyncio.to_thread(self.client.files.get, name=uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise ValueError("Przetwarzanie pliku wideo w chmurze zakończyło się błędem.")

        try:
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=CoachTip,
                temperature=0.2,
            )
            prompt_contents = [uploaded_file, "Przeanalizuj to wideo z meczu squasha i zwróć podsumowanie oraz oceny graczy."]
            if players_config:
                try:
                    conf = json.loads(players_config)
                    pa = conf.get("playerA", {})
                    pb = conf.get("playerB", {})
                    prompt_contents.append(f"\n\nRozpoznani gracze na korcie:\n- Gracz A: {pa.get('name')} ({pa.get('gender')}, ubiór: {pa.get('look')})\n- Gracz B: {pb.get('name')} ({pb.get('gender')}, ubiór: {pb.get('look')})\nZwracaj się do graczy WYŁĄCZNIE używając ich imienia (np. '{pa.get('name')}, zrób...'). W formacie JSON przypisz imię do zmiennej target_player.")
                except json.JSONDecodeError:
                    pass

            if previous_tips:
                tips_text = "\n\nOstatnio zwróciłeś już te uwagi (NIE POWTARZAJ ICH, skup się na innych błędach):\n"
                for tip in previous_tips:
                    tips_text += f"- {tip}\n"
                prompt_contents.append(tips_text)

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model_name,
                contents=prompt_contents,
                config=config
            )
            
            # 3. Czyszczenie pliku w chmurze
            try:
                await asyncio.to_thread(self.client.files.delete, name=uploaded_file.name)
            except Exception:
                pass
                
            return self._parse_response(response.text)
            
        except Exception as e:
            # Czyszczenie w razie błędu
            try:
                await asyncio.to_thread(self.client.files.delete, name=uploaded_file.name)
            except Exception:
                pass
            raise e

    async def _analyze_frame_by_frame(self, video_path: str, model_name: str, previous_tips: List[str] = None, players_config: str = None) -> CoachTip:
        """
        Fallback: Wyciąga klatki z wideo w odstępach co 1 sekundę i przesyła je jako listę obrazów JPEG w zapytaniu multimodalnym.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Nie można otworzyć pliku wideo: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25.0
            
        frame_interval = int(fps)  # 1 klatka na sekundę
        contents = []
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_idx % frame_interval == 0:
                # Skalowanie w dół dla zmniejszenia rozmiaru przesyłanych danych (max szerokość 1024px)
                h, w = frame.shape[:2]
                if w > 1024:
                    scale = 1024 / w
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

                # Kompresja klatki do JPEG
                success, encoded_img = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if success:
                    img_bytes = encoded_img.tobytes()
                    contents.append(
                        types.Part.from_bytes(
                            data=img_bytes,
                            mime_type="image/jpeg"
                        )
                    )
            frame_idx += 1
            
        cap.release()
        
        if not contents:
            raise ValueError("Nie udało się pobrać żadnych klatek z pliku wideo.")

        # Dodanie instrukcji do zapytania
        prompt_text = "Oto klatki z nagrania wideo w odstępie 1 sekundy. Przeanalizuj grę pod kątem pracy nóg, kontroli kortu oraz zamachu i zwróć ustrukturyzowany JSON."
        if players_config:
            try:
                conf = json.loads(players_config)
                pa = conf.get("playerA", {})
                pb = conf.get("playerB", {})
                prompt_text += f"\n\nRozpoznani gracze na korcie:\n- Gracz A: {pa.get('name')} ({pa.get('gender')}, ubiór: {pa.get('look')})\n- Gracz B: {pb.get('name')} ({pb.get('gender')}, ubiór: {pb.get('look')})\nZwracaj się do graczy WYŁĄCZNIE używając ich imienia (np. '{pa.get('name')}, zrób...'). W formacie JSON przypisz imię do zmiennej target_player."
            except json.JSONDecodeError:
                pass

        if previous_tips:
            prompt_text += "\n\nOstatnio zwróciłeś już te uwagi (NIE POWTARZAJ ICH, skup się na innych błędach):\n"
            for tip in previous_tips:
                prompt_text += f"- {tip}\n"
        contents.append(prompt_text)

        # Konfiguracja API
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=CoachTip,
            temperature=0.2,
        )

        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=model_name,
            contents=contents,
            config=config
        )
        
        return self._parse_response(response.text)

    def _parse_response(self, text: str) -> CoachTip:
        """
        Parsuje odpowiedź tekstową z API do modelu Pydantic CoachTip.
        Obsługuje ewentualny brak Structured Output (czysty tekst zawierający JSON).
        """
        clean_json_str = text.strip()
        if clean_json_str.startswith("```json"):
            clean_json_str = clean_json_str[7:]
        if clean_json_str.startswith("```"):
            clean_json_str = clean_json_str[3:]
        if clean_json_str.endswith("```"):
            clean_json_str = clean_json_str[:-3]
        
        clean_json_str = clean_json_str.strip()

        try:
            data = json.loads(clean_json_str)
            return CoachTip(**data)
        except Exception as e:
            print(f"[Agent] Błąd parsowania JSON ze zwracanego tekstu: {text}")
            raise ValueError("Zwrócona odpowiedź nie jest poprawnym obiektem JSON.") from e
