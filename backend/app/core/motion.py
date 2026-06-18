import os
import time
from typing import Optional

class MotionDetector:
    def __init__(
        self,
        buffer_dir: str = "temp_buffer",
        chunks_for_window: int = 3,  # np. 3 paczki = 9 sekund
        target_width: int = 640,
        target_height: int = 360
    ):
        self.buffer_dir = buffer_dir
        self.chunks_for_window = chunks_for_window
        self.target_width = target_width
        self.target_height = target_height
        
        # Tworzenie katalogu bufora
        os.makedirs(self.buffer_dir, exist_ok=True)
        
        # Zamiast listy osobnych plików, używamy jednego rosnącego pliku strumienia (dla ciągłego WebM z PWA timeslice)
        self.stream_path = os.path.join(self.buffer_dir, "stream.webm")
        
        # Stan detektora
        self.total_chunks = 0
        self.unprocessed_chunks = 0
        
    def add_chunk(self, chunk_bytes: bytes, ext: str = ".webm") -> bool:
        """
        Dopisuje nową paczkę wideo do głównego strumienia. Zwraca True, jeśli uzbierano wystarczająco dużo paczek
        do wygenerowania okienka analizy.
        """
        # Dopisywanie do końca pliku strumienia (PWA wysyła continuous blob stream)
        with open(self.stream_path, "ab") as f:
            f.write(chunk_bytes)
            
        self.total_chunks += 1
        self.unprocessed_chunks += 1
        
        # Jeśli osiągnęliśmy wystarczającą liczbę okienek, zwracamy True
        if self.unprocessed_chunks >= self.chunks_for_window:
            return True
            
        return False

    def extract_window(self) -> Optional[str]:
        """
        Wycina okno z głównego strumienia przy użyciu ffmpeg.
        Zwraca ścieżkę do gotowego pliku .mp4.
        """
        if self.unprocessed_chunks < self.chunks_for_window:
            return None
            
        output_filename = f"window_{int(time.time())}.mp4"
        output_path = os.path.join(self.buffer_dir, output_filename)
        
        # Długość okienka w sekundach (3 paczki = 9 sekund)
        duration = self.chunks_for_window * 3
        # Czas rozpoczęcia wycinania względem początku pliku
        start_time = max(0, (self.total_chunks - self.chunks_for_window) * 3)
        
        import subprocess
        # Ponieważ użyliśmy cwd=self.buffer_dir, ścieżki w poleceniu mogą być względne do tego folderu,
        # lub możemy usunąć cwd i używać pełnych ścieżek. Bezpieczniej jest używać pełnych ścieżek absolutnych.
        abs_stream_path = os.path.abspath(self.stream_path)
        abs_output_path = os.path.abspath(output_path)
        
        try:
            # -ss przesuwa się na odpowiedni moment strumienia, -t określa czas nagrania
            subprocess.run([
                "ffmpeg", "-y", 
                "-ss", str(start_time),
                "-i", abs_stream_path, 
                "-t", str(duration),
                "-c:v", "libx264", "-preset", "ultrafast", 
                abs_output_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[MotionDetector] Błąd wycinania okna ffmpeg: {e.stderr.decode('utf-8', errors='ignore')}")
            return None
        except Exception as e:
            print(f"[MotionDetector] Nieoczekiwany błąd ffmpeg: {e}")
            return None
                
        # Zostawiamy ostatnią paczkę z okienka jako kontekst (przesuwamy wskaźnik o chunks_for_window - 1)
        # Oznacza to, że z 3 przetworzonych paczek "skonsumowaliśmy" 2 starsze, a najnowsza jest nakładką
        self.unprocessed_chunks = 1
        
        return output_path

    def reset(self):
        """
        Czyści stan detektora i usuwa główny strumień.
        """
        self.total_chunks = 0
        self.unprocessed_chunks = 0
        if os.path.exists(self.stream_path):
            try:
                os.remove(self.stream_path)
            except Exception:
                pass

    def cleanup_all(self):
        """
        Usuwa wszystkie pliki z katalogu bufora przy zamykaniu aplikacji.
        """
        self.reset()
        if os.path.exists(self.buffer_dir):
            for file in os.listdir(self.buffer_dir):
                file_path = os.path.join(self.buffer_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception:
                    pass
