import os
import sys
import glob
import time
import shutil
import asyncio
import argparse
import requests
import websockets
import subprocess

async def websocket_listener(session_id, ws_url):
    print(f"[WS] Łączenie z {ws_url}...")
    try:
        async with websockets.connect(ws_url) as websocket:
            print("[WS] Połączono z serwerem. Oczekiwanie na komunikaty...")
            while True:
                try:
                    message = await websocket.recv()
                    if isinstance(message, bytes):
                        print(f"\n[WS AUDIO] Otrzymano plik audio ({len(message)} bytes). Zapisuję jako feedback_test.mp3...")
                        with open("feedback_test.mp3", "wb") as f:
                            f.write(message)
                    else:
                        print(f"\n[WS JSON] Odpowiedź serwera: {message}")
                except websockets.exceptions.ConnectionClosed:
                    print("\n[WS] Rozłączono.")
                    break
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"\n[WS ERROR] Błąd: {e}")

async def send_chunks(session_id, api_url, chunks_dir):
    chunks = sorted(glob.glob(os.path.join(chunks_dir, "chunk_*.mp4")))
    if not chunks:
        print(f"Brak fragmentów w katalogu {chunks_dir}.")
        return

    print(f"[Uploader] Znaleziono {len(chunks)} fragmentów. Rozpoczynam wysyłkę z opóźnieniem (Real-time simulation)...")
    
    for i, chunk_path in enumerate(chunks):
        print(f"[Uploader] Wysyłanie fragmentu {i+1}/{len(chunks)}: {os.path.basename(chunk_path)}")
        
        def upload_file(path):
            with open(path, "rb") as f:
                files = {"file": ("chunk.mp4", f, "video/mp4")}
                url = f"{api_url}?session_id={session_id}"
                try:
                    res = requests.post(url, files=files)
                    return res.status_code
                except Exception as e:
                    return str(e)
                    
        status = await asyncio.to_thread(upload_file, chunk_path)
        print(f"[Uploader] Wysłano. Status HTTP: {status}")
        
        # Symulacja czasu trwania paczki (np. 3 sekundy) przed wysłaniem kolejnej
        if i < len(chunks) - 1:
            await asyncio.sleep(3.0)

    print("\n[Uploader] Zakończono wysyłanie wszystkich fragmentów wideo.")
    print("Oczekuję 25 sekund na ewentualną odpowiedź i procesowanie AI, zanim zamknę skrypt...")
    for _ in range(25):
        await asyncio.sleep(1.0)

async def main():
    parser = argparse.ArgumentParser(description="Symulacja kamery aplikacji Squash PWA.")
    parser.add_argument("video", help="Ścieżka do pliku wideo (np. test_match.mp4)")
    parser.add_argument("--host", default="localhost", help="Host serwera backend (domyślnie: localhost)")
    parser.add_argument("--port", default="8000", help="Port serwera (domyślnie: 8000)")
    parser.add_argument("--chunk-time", default=3, type=int, help="Czas trwania jednej paczki w sekundach (domyślnie: 3)")
    parser.add_argument("--players", default=None, help="Konfiguracja graczy w formacie JSON do przekazania AI")
    
    args = parser.parse_args()

    video_path = args.video
    if not os.path.exists(video_path):
        print(f"Błąd: Nie znaleziono pliku {video_path}")
        sys.exit(1)

    temp_dir = "temp_simulate_chunks"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    # Używamy ffmpeg do podziału wideo na równe segmenty
    print(f"Cięcie wideo '{video_path}' na paczki po {args.chunk_time} sekund za pomocą ffmpeg...")
    cmd = [
        "ffmpeg", "-y", "-i", video_path, 
        "-c", "copy", "-map", "0", 
        "-segment_time", str(args.chunk_time), 
        "-f", "segment", 
        "-reset_timestamps", "1",
        os.path.join(temp_dir, "chunk_%03d.mp4")
    ]
    
    # Wywołanie ffmpeg ukrywając standardowe wyjście, chyba że wystąpi błąd
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        print("Błąd podczas cięcia wideo. Upewnij się, że 'ffmpeg' jest poprawnie zainstalowany w systemie i dostępny w zmiennej PATH.")
        shutil.rmtree(temp_dir)
        sys.exit(1)

    session_id = f"test_sim_{int(time.time())}"
    import urllib.parse
    ws_url = f"ws://{args.host}:{args.port}/ws/session?session_id={session_id}"
    if args.players:
        ws_url += f"&players_config={urllib.parse.quote(args.players)}"
    api_url = f"http://{args.host}:{args.port}/api/upload-chunk"

    print(f"\nUruchamianie symulacji dla sesji: {session_id}")
    
    # Uruchomienie nasłuchiwania WebSocket w tle
    ws_task = asyncio.create_task(websocket_listener(session_id, ws_url))
    
    # Odczekanie chwili na ustanowienie połączenia WS
    await asyncio.sleep(1)
    
    # Uruchomienie wysyłki plików
    await send_chunks(session_id, api_url, temp_dir)

    # Zakończenie
    ws_task.cancel()
    
    # Sprzątanie
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"\nUsunięto folder tymczasowy z paczkami ({temp_dir}).")
        print("Symulacja zakończona.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPrzerwano przez użytkownika. Sprzątanie...")
        if os.path.exists("temp_simulate_chunks"):
            shutil.rmtree("temp_simulate_chunks")
        sys.exit(0)
