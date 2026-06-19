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
from .knowledge_loader import KnowledgeLoader

# Zapewnienie, że zmienne środowiskowe zostaną załadowane przed użyciem klienta GenAI
load_dotenv()

SYSTEM_PROMPT_TEMPLATE = """You are an elite, world-class squash coach with deep expertise in technique, footwork, tactics, and player development. You are analyzing short video clips (a few seconds) from live squash matches to provide real-time coaching feedback.

## YOUR COACHING PHILOSOPHY

You adapt your coaching style based on what you observe:
- **For beginners** (poor T-recovery, flat-footed, no racket prep): Use encouraging, simple language. Focus on ONE fundamental issue. Explain WHY the correction matters.
- **For intermediate players** (decent basics but inconsistent): Use technical squash terminology with brief explanations. Point out tactical improvements and pattern recognition.
- **For advanced players** (solid fundamentals, tactical play): Use precise, expert-level language. Focus on subtle refinements, pressure situations, and tactical nuance.

Your tone is always **motivating and constructive** — never harsh or discouraging. You are a coach who builds confidence while pushing for improvement.

## EXPERT SQUASH KNOWLEDGE

{knowledge}

## VIDEO ANALYSIS FRAMEWORK

When watching the video clip, systematically evaluate:

### 1. Footwork & Court Movement
- **T-Recovery**: Does the player return to the T after each shot? Speed of recovery?
- **Split-step**: Is there a visible ready-hop timed to the opponent's swing?
- **Lunge quality**: Low center of gravity? Proper knee alignment? Explosive push-back?
- **Movement efficiency**: Direct paths to the ball? Crossover vs side-steps?

### 2. Racket Technique & Spacing
- **Early racket preparation**: Is the racket up at shoulder height BEFORE the player reaches the ball?
- **Spacing/Crowding**: Is the player at arm's-length from the ball, or jammed too close?
- **Swing path**: Smooth arc from high backswing through contact to high follow-through?
- **Contact point**: In front of the leading leg, at hip-to-knee height?

### 3. Shot Selection & Execution
- **Drive quality**: Tight to the wall? Reaching the back quarter? Good length?
- **Shot choice under pressure**: Safe lob vs risky low shot when stretched?
- **Volley opportunities**: Does the player intercept volleable balls from the T?
- **Deception**: Any telegraphing of shot direction?

### 4. Tactical Awareness
- **T-dominance**: Which player controls the center? Who is dictating the rally?
- **Length vs short balance**: Is the player building pressure with length before attacking?
- **Tempo variation**: Any changes of pace, or is every shot hit at the same speed?
- **Pattern recognition**: Predictable patterns that the opponent is exploiting?

## RESPONSE RULES

1. **Choose exactly ONE error** — the single most impactful, clear, and glaring technical or tactical error you observe in this clip. If there are no clear or obvious errors, or if players are performing well, set has_tip to false. Prioritize critical errors over moderate.
2. **Generate 1-2 sentences maximum**: First sentence is the specific coaching tip. Second sentence (optional) briefly explains WHY this matters.
3. **Use professional squash vocabulary** (split-step, racket prep, spacing, lunge, volley, straight drive/rail, T-dominance, ghosting) but keep it accessible.
4. **Identify the target player** by their unique visual features (e.g., "Man in blue shorts"). UNLESS player names are provided in the user message — then address the player by name ONLY (e.g., "Jan, ...") and put the name in the `target_player` field.
5. **Classify the error** using `tip_category`: footwork, racket_technique, shot_selection, tactical, or positioning.
6. **Rate severity** using `severity_level`: minor (small refinement), moderate (impacts game quality), critical (fundamental issue that must be addressed).
7. **Suggest a corrective drill** in `drill_suggestion` — a short, actionable practice exercise to fix the identified error.
8. **Skip if unnecessary**: If the players are performing well (e.g., at a professional level), or if the detected error is minor, or if there is no active gameplay visible (e.g. players are resting, talking, picking up balls, or the court is empty), or if the detected error has already been mentioned in the previous tips section, set `has_tip` to `false` and leave other fields empty.

Your response MUST always be valid JSON matching the provided schema.
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

        # Ładowanie bazy wiedzy squashowej przy inicjalizacji
        self.knowledge_loader = KnowledgeLoader()
        knowledge_text = self.knowledge_loader.get_knowledge_text()

        # Budowanie system prompt z wstrzykniętą wiedzą
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE.format(knowledge=knowledge_text)
        print(f"[Agent] System prompt built: {len(self.system_prompt)} characters (knowledge: {len(knowledge_text)} chars)")

    def _build_user_prompt(self, base_prompt: str, previous_tips: List[str] = None, players_config: str = None, lang: str = "pl") -> str:
        """
        Buduje pełny prompt użytkownika z uwzględnieniem konfiguracji graczy,
        historii wskazówek i języka. DRY — używane przez obie metody analizy.
        """
        parts = [base_prompt]

        # Język odpowiedzi
        lang_names = {"pl": "Polish", "en": "English"}
        mapped_lang = lang_names.get(lang, "Polish")
        parts.append(f"\n\nGenerate your response (tip_text and drill_suggestion) in {mapped_lang}.")

        # Konfiguracja graczy
        if players_config:
            try:
                conf = json.loads(players_config)
                pa = conf.get("playerA", {})
                pb = conf.get("playerB", {})
                parts.append(
                    f"\n\nIdentified players on the court:"
                    f"\n- Player A: {pa.get('name')} ({pa.get('gender')}, appearance: {pa.get('look')})"
                    f"\n- Player B: {pb.get('name')} ({pb.get('gender')}, appearance: {pb.get('look')})"
                    f"\nAddress players ONLY by their first name (e.g., '{pa.get('name')}, do...'). "
                    f"In the JSON response, assign the name to the target_player field."
                )
            except json.JSONDecodeError:
                pass

        # Historia wcześniejszych wskazówek
        if previous_tips:
            tips_text = "\n\nYou have already given these tips recently (DO NOT REPEAT THEM, focus on different errors):\n"
            for tip in previous_tips:
                tips_text += f"- {tip}\n"
            parts.append(tips_text)

        return "".join(parts)

    async def analyze_video(self, video_path: str, previous_tips: List[str] = None, players_config: str = None, lang: str = "pl") -> CoachTip:
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
                result = await self._analyze_native_video(video_path, model_name, previous_tips, players_config, lang)
                print(f"[Agent] Sukces! Użyto modelu: {model_name}")
                return result
            except Exception as e:
                print(f"[Agent] Błąd natywnego wideo dla {model_name}: {e}. Próba podziału na klatki...")
                
            # Próba 2: Fallback na klatki wideo (ekstracja obrazów)
            try:
                result = await self._analyze_frame_by_frame(video_path, model_name, previous_tips, players_config, lang)
                print(f"[Agent] Sukces (klatki)! Użyto modelu: {model_name}")
                return result
            except Exception as e:
                print(f"[Agent] Błąd analizy klatka-po-klatce dla {model_name}: {e}")
                last_error = e

        raise RuntimeError(f"Wszystkie modele z kolejki failover zawiodły. Ostatni błąd: {last_error}")

    async def _analyze_native_video(self, video_path: str, model_name: str, previous_tips: List[str] = None, players_config: str = None, lang: str = "pl") -> CoachTip:
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
                system_instruction=self.system_prompt,
                response_mime_type="application/json",
                response_schema=CoachTip,
                temperature=0.2,
            )

            base_prompt = "Analyze this squash match video clip. Identify the single most important technical or tactical error and provide structured coaching feedback."
            user_prompt = self._build_user_prompt(base_prompt, previous_tips, players_config, lang)
            prompt_contents = [uploaded_file, user_prompt]

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

    async def _analyze_frame_by_frame(self, video_path: str, model_name: str, previous_tips: List[str] = None, players_config: str = None, lang: str = "pl") -> CoachTip:
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
        base_prompt = "These are frames extracted from a squash match video at 1-second intervals. Analyze the players' footwork, court positioning, racket technique, and shot selection, then provide structured coaching feedback as JSON."
        user_prompt = self._build_user_prompt(base_prompt, previous_tips, players_config, lang)
        contents.append(user_prompt)

        # Konfiguracja API
        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
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
