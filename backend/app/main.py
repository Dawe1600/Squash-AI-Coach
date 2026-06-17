import os
import time
import shutil
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Ładowanie zmiennych środowiskowych z pliku .env (jeśli istnieje lokalnie) przed innymi importami
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import router as api_router

async def garbage_collector():
    while True:
        try:
            now = time.time()
            # Skanujemy główny katalog roboczy w poszukiwaniu buforów sierocych
            for item in os.listdir("."):
                if item.startswith("temp_buffer_") and os.path.isdir(item):
                    mod_time = os.path.getmtime(item)
                    if now - mod_time > 2 * 3600: # Starsze niż 2 godziny
                        shutil.rmtree(item, ignore_errors=True)
                        print(f"[GarbageCollector] Usunięto przestarzały katalog: {item}")
        except Exception as e:
            print(f"[GarbageCollector] Błąd podczas czyszczenia: {e}")
        # Uruchamiaj skanowanie co godzinę
        await asyncio.sleep(3600)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uruchomienie tła dla Garbage Collectora
    gc_task = asyncio.create_task(garbage_collector())
    yield
    # Anulowanie zadania przy wyłączaniu
    gc_task.cancel()

app = FastAPI(
    title="Squash AI Coach API",
    description="Backend FastAPI obsługujący analizę taktyki w squasha w czasie rzeczywistym",
    version="1.0.0",
    lifespan=lifespan
)

# Konfiguracja CORS - kluczowa dla komunikacji PWA (hosting statyczny) z backendem (Hugging Face Spaces)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W wersji produkcyjnej można zawęzić do domeny frontendu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejestracja routera z endpointami
app.include_router(api_router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Squash AI Coach Backend",
        "info": "Prześlij fragmenty wideo na /api/upload-chunk i podłącz się do WebSocket /ws/session"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
