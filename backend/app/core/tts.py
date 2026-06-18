import io
from gtts import gTTS

class TTSService:
    def __init__(self, lang: str = "pl"):
        self.lang = lang

    def generate_speech(self, text: str, lang: str = None) -> bytes:
        """
        Konwertuje podany tekst na mowę (pliki MP3) i zwraca jako bajty z pamięci RAM.
        Dzięki temu nie musimy zapisywać plików na dysk kontenera Docker.
        """
        if not text.strip():
            return b""
            
        tts = gTTS(text=text, lang=lang or self.lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
