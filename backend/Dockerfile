FROM python:3.11-slim

# Instalacja zależności systemowych dla OpenCV i ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kopiowanie i instalacja pakietów
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu aplikacji
COPY app/ ./app/

# Port dla serwera FastAPI (Spaces domyślnie nasłuchuje na 7860 lub 8000, dla Spaces często jest to 7860)
EXPOSE 7860

# Uruchomienie uvicorna na porcie 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
