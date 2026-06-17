import re
import os
import shutil
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Query, HTTPException, BackgroundTasks
from typing import Dict
from ..core.motion import MotionDetector
from ..core.agent import SquashAgent
from ..core.tts import TTSService

router = APIRouter()

# Klasa do zarządzania aktywnymi połączeniami i detektorami ruchu
class SessionManager:
    def __init__(self):
        self.active_websockets: Dict[str, WebSocket] = {}
        self.motion_detectors: Dict[str, MotionDetector] = {}
        self.is_analyzing: Dict[str, bool] = {}
        self.session_history: Dict[str, list] = {}
        self.players_configs: Dict[str, str] = {}
        self.agent = SquashAgent()
        self.tts = TTSService()

    async def connect(self, session_id: str, websocket: WebSocket, players_config: str = None):
        await websocket.accept()
        self.active_websockets[session_id] = websocket
        # Unikalny katalog roboczy dla bufora tej sesji
        buffer_dir = f"temp_buffer_{session_id}"
        self.motion_detectors[session_id] = MotionDetector(buffer_dir=buffer_dir)
        self.is_analyzing[session_id] = False
        self.session_history[session_id] = []
        if players_config:
            self.players_configs[session_id] = players_config
            print(f"[SessionManager] Skonfigurowano graczy dla sesji {session_id}: {players_config}")
        print(f"[SessionManager] Połączono nową sesję: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_websockets:
            del self.active_websockets[session_id]
        if session_id in self.motion_detectors:
            # Czyszczenie plików tymczasowych sesji
            self.motion_detectors[session_id].cleanup_all()
            # Próba usunięcia katalogu bufora
            try:
                shutil.rmtree(self.motion_detectors[session_id].buffer_dir, ignore_errors=True)
            except Exception:
                pass
            del self.motion_detectors[session_id]
        if session_id in self.is_analyzing:
            del self.is_analyzing[session_id]
        if session_id in self.session_history:
            del self.session_history[session_id]
        if session_id in self.players_configs:
            del self.players_configs[session_id]
        print(f"[SessionManager] Rozłączono sesję: {session_id}")

    async def send_json(self, session_id: str, data: dict):
        if session_id in self.active_websockets:
            await self.active_websockets[session_id].send_json(data)

    async def send_bytes(self, session_id: str, data: bytes):
        if session_id in self.active_websockets:
            await self.active_websockets[session_id].send_bytes(data)

manager = SessionManager()

def clean_markdown_for_tts(text: str) -> str:
    """Usuwa znaczniki markdown, aby tekst brzmiał naturalnie podczas syntezy mowy."""
    # Nagłówki
    text = re.sub(r'#+\s*', '', text)
    # Pogrubienia / pochylenia
    text = re.sub(r'\*+', '', text)
    # Myślniki list
    text = re.sub(r'^\s*[-*+]\s*', '', text, flags=re.MULTILINE)
    # Numerowane listy
    text = re.sub(r'^\s*\d+\.\s*', '', text, flags=re.MULTILINE)
    return text.strip()

async def process_analysis_background(session_id: str, video_path: str):
    """
    Uruchamia analizę AI w tle, generuje TTS i wysyła wyniki do klienta przez WebSocket.
    Dzięki temu HTTP POST zwraca status natychmiast, nie blokując wątku.
    """
    try:
        # Pobranie historii uwag i konfiguracji graczy
        previous_tips = manager.session_history.get(session_id, [])
        players_config = manager.players_configs.get(session_id)
        # 2. Analiza AI (Gemini/Gemma z failover)
        analysis_result = await manager.agent.analyze_video(video_path, previous_tips=previous_tips, players_config=players_config)
        
        # 3. Sprawdzamy, czy AI ma uwagę do powiedzenia
        if not analysis_result.has_tip or not analysis_result.tip_text:
            print(f"[endpoints] Brak rażących błędów. Ignoruję to okienko.")
            return

        # Aktualizacja historii (ostatnie 3 uwagi)
        history = manager.session_history.get(session_id, [])
        history.append(analysis_result.tip_text)
        manager.session_history[session_id] = history[-3:]

        # Informujemy klienta (UI), że jest uwaga i generujemy TTS
        await manager.send_json(session_id, {
            "type": "analysis_result",
            "data": analysis_result.model_dump()
        })
        
        # 4. Generowanie tekstu do przeczytania
        tts_text = analysis_result.tip_text
            
        # 5. Konwersja na mowę
        await manager.send_json(session_id, {
            "type": "status",
            "message": "Trener zwraca uwagę głosowo..."
        })
        mp3_bytes = await asyncio.to_thread(manager.tts.generate_speech, tts_text)
        
        # 6. Wysłanie dźwięku przez WebSocket
        if mp3_bytes:
            await manager.send_bytes(session_id, mp3_bytes)
            await manager.send_json(session_id, {
                "type": "status",
                "message": "Czekam na kolejne okienka..."
            })
            
    except Exception as e:
        print(f"[endpoints] Błąd analizy w tle: {e}")
        await manager.send_json(session_id, {
            "type": "error",
            "message": f"Wystąpił błąd podczas analizy: {str(e)}"
        })
    finally:
        # Usuwamy plik wideo po analizie i ZWALNIAMY BLOKADĘ
        if session_id in manager.is_analyzing:
            manager.is_analyzing[session_id] = False
            
        if os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass

@router.websocket("/ws/session")
async def websocket_endpoint(websocket: WebSocket, session_id: str = Query(...), players_config: str = Query(None)):
    await manager.connect(session_id, websocket, players_config)
    try:
        while True:
            # Utrzymujemy połączenie i odbieramy ewentualne polecenia ping/control od klienta
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"[WebSocket] Błąd na sesji {session_id}: {e}")
        manager.disconnect(session_id)

@router.post("/api/upload-chunk")
async def upload_chunk(
    background_tasks: BackgroundTasks,
    session_id: str = Query(...),
    file: UploadFile = File(...)
):
    if session_id not in manager.motion_detectors:
        raise HTTPException(status_code=400, detail="Brak aktywnej sesji WebSocket dla podanego session_id.")

    # Czytamy plik z żądania
    chunk_bytes = await file.read()
    detector = manager.motion_detectors[session_id]
    
    # Wyciągamy rozszerzenie z nazwy pliku w żądaniu
    filename = file.filename
    ext = os.path.splitext(filename)[1] if filename else ".webm"
    
    # Przekazujemy paczkę do detektora ruchu z odpowiednim rozszerzeniem
    is_window_ready = detector.add_chunk(chunk_bytes, ext=ext)
    
    # Jeśli mamy okienko 9-sekundowe i serwer NIE JEST w trakcie analizy
    if is_window_ready and not manager.is_analyzing.get(session_id, False):
        manager.is_analyzing[session_id] = True
        exchange_video_path = await asyncio.to_thread(detector.extract_window)
        
        if exchange_video_path:
            print(f"[endpoints] Przekazuję okienko wideo do analizy: {exchange_video_path}")
            await manager.send_json(session_id, {
                "type": "status",
                "message": "Wysyłam zgromadzone okienko wideo do AI..."
            })
            background_tasks.add_task(process_analysis_background, session_id, exchange_video_path)
            return {"status": "analysis_started", "message": "Rozpoczęto analizę okienka."}
        else:
            manager.is_analyzing[session_id] = False
        
    return {"status": "processing", "message": "Paczka wideo zbuforowana."}
