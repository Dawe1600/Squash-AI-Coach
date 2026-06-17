// Squash AI Coach - Main Logic

// Stan aplikacji
let stream = null;
let mediaRecorder = null;
let socket = null;
let chunkInterval = null;
let sessionId = "";
let recordingActive = false;
let audioCtx = null; // Web Audio API Context

// Elementy DOM
const videoPreview = document.getElementById('video-preview');
const cameraSelect = document.getElementById('camera-select');
const btnStart = document.getElementById('btn-start');
const btnStop = document.getElementById('btn-stop');
const recordingIndicator = document.getElementById('recording-indicator');
const connectionStatus = document.getElementById('connection-status');
const statusMessage = document.getElementById('status-message');
const analysisIndicator = document.getElementById('analysis-indicator');
const audioPlayer = document.getElementById('audio-player');

const backendUrlInput = document.getElementById('backend-url');
const sessionIdInput = document.getElementById('session-id');
const btnRegenSession = document.getElementById('btn-regen-session');

// Modal Konfiguracji Graczy
const btnConfigPlayers = document.getElementById('btn-config-players');
const playersModal = document.getElementById('players-modal');
const btnSavePlayers = document.getElementById('btn-save-players');
const btnCloseModal = document.getElementById('btn-close-modal');
let playersConfig = null;

// Sekcja czatu z trenerem
const coachFeed = document.getElementById('coach-feed');

// Inicjalizacja sesji
function initSession() {
    // Odczyt zapisanego URL backendu
    const savedUrl = localStorage.getItem('squash_backend_url');
    if (savedUrl) {
        backendUrlInput.value = savedUrl;
    }

    // Generowanie lub odczyt ID sesji
    sessionId = generateUUID();
    sessionIdInput.value = sessionId;

    // Odczyt konfiguracji graczy
    const savedPlayers = localStorage.getItem('squash_players_config');
    if (savedPlayers) {
        try {
            playersConfig = JSON.parse(savedPlayers);
            // Wypełnienie pól formularza
            if (playersConfig.playerA) {
                document.getElementById('player-a-name').value = playersConfig.playerA.name || '';
                document.getElementById('player-a-gender').value = playersConfig.playerA.gender || 'Mężczyzna';
                document.getElementById('player-a-look').value = playersConfig.playerA.look || '';
            }
            if (playersConfig.playerB) {
                document.getElementById('player-b-name').value = playersConfig.playerB.name || '';
                document.getElementById('player-b-gender').value = playersConfig.playerB.gender || 'Mężczyzna';
                document.getElementById('player-b-look').value = playersConfig.playerB.look || '';
            }
        } catch (e) {
            console.error("Błąd odczytu squash_players_config z localStorage:", e);
        }
    }
}

function generateUUID() {
    return 'session_' + Math.random().toString(36).substring(2, 11);
}

// Pobranie listy dostępnych kamer
async function getCameras() {
    try {
        await navigator.mediaDevices.getUserMedia({ video: true }); // Request permissions first
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        
        cameraSelect.innerHTML = '';
        if (videoDevices.length === 0) {
            cameraSelect.innerHTML = '<option value="">Brak kamer</option>';
            return;
        }

        videoDevices.forEach((device, index) => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.text = device.label || `Kamera ${index + 1}`;
            // Ustawienie domyślnie tylnej kamery (environment)
            if (device.label.toLowerCase().includes('back') || device.label.toLowerCase().includes('tył')) {
                option.selected = true;
            }
            cameraSelect.appendChild(option);
        });

        // Start podglądu z kamery
        await startCameraPreview();
    } catch (err) {
        console.error("Błąd pobierania kamer:", err);
        statusMessage.textContent = "Błąd: Brak dostępu do kamery. Nadaj uprawnienia w przeglądarce.";
    }
}

// Uruchomienie podglądu z kamery
async function startCameraPreview() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }

    const deviceId = cameraSelect.value;
    const constraints = {
        video: deviceId ? { deviceId: { exact: deviceId } } : { facingMode: 'environment' },
        audio: false // audio niepotrzebne w analizie wideo
    };

    try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        videoPreview.srcObject = stream;
    } catch (err) {
        console.error("Błąd uruchamiania podglądu:", err);
        statusMessage.textContent = "Błąd podglądu z kamery. Spróbuj wybrać inną kamerę.";
    }
}

// Połączenie z WebSocketem
function connectWebSocket() {
    if (socket) {
        socket.close();
    }

    const backendUrl = backendUrlInput.value.trim();
    localStorage.setItem('squash_backend_url', backendUrl);

    // Konwersja http(s) do ws(s)
    let wsUrl = backendUrl.replace(/^http/, 'ws');
    // Dodanie endpointu sesji
    wsUrl = `${wsUrl}/ws/session?session_id=${sessionId}`;
    
    // Dodanie konfiguracji graczy
    if (playersConfig) {
        wsUrl += `&players_config=${encodeURIComponent(JSON.stringify(playersConfig))}`;
    }

    updateConnectionStatus(false, "Łączenie...");

    socket = new WebSocket(wsUrl);
    socket.binaryType = 'blob';

    socket.onopen = () => {
        updateConnectionStatus(true, "Połączono");
        statusMessage.textContent = "Gotowy do rozpoczęcia treningu.";
    };

    socket.onclose = () => {
        updateConnectionStatus(false, "Rozłączony");
        if (recordingActive) {
            statusMessage.textContent = "Połączenie z serwerem przerwane. Próba ponownego połączenia...";
            setTimeout(connectWebSocket, 3000);
        }
    };

    socket.onerror = (err) => {
        console.error("Błąd WebSocket:", err);
        updateConnectionStatus(false, "Błąd");
    };

    socket.onmessage = async (event) => {
        if (event.data instanceof Blob) {
            // Otrzymaliśmy plik audio MP3 od syntezatora gTTS!
            playAudioFeedback(event.data);
        } else {
            // Otrzymaliśmy status lub dane analizy (JSON)
            try {
                const message = JSON.parse(event.data);
                handleServerMessage(message);
            } catch (err) {
                console.error("Błąd parsowania JSON z serwera:", err);
            }
        }
    };
}

function updateConnectionStatus(isConnected, text) {
    connectionStatus.className = `status-badge ${isConnected ? 'connected' : 'disconnected'}`;
    connectionStatus.querySelector('.status-text').textContent = text;
}

// Inicjalizacja Web Audio API
function initAudio() {
    if (!audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AudioContext();
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    
    // Wymuszone odblokowanie na iOS (odtworzenie głuchej sekundy podczas kliknięcia)
    const buffer = audioCtx.createBuffer(1, 1, 22050);
    const source = audioCtx.createBufferSource();
    source.buffer = buffer;
    source.connect(audioCtx.destination);
    if (source.start) {
        source.start(0);
    } else {
        source.noteOn(0);
    }
}

// Odtwarzanie wskazówek głosowych (Web Audio API)
function playAudioFeedback(blob) {
    if (!audioCtx) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const arrayBuffer = e.target.result;
        audioCtx.decodeAudioData(arrayBuffer, (buffer) => {
            const source = audioCtx.createBufferSource();
            source.buffer = buffer;
            source.connect(audioCtx.destination);
            if (source.start) {
                source.start(0);
            } else {
                source.noteOn(0);
            }
            console.log("[Audio] Pomyślnie odtworzono wskazówki głosowe (Blob).");
        }, (err) => {
            console.error("[Audio] Błąd dekodowania audio:", err);
        });
    };
    reader.onerror = function(err) {
        console.error("[Audio] Błąd odczytu pliku blob:", err);
    }
    reader.readAsArrayBuffer(blob);
}

async function playBase64Audio(base64str) {
    if (!audioCtx) return;
    try {
        const binaryString = window.atob(base64str);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        audioCtx.decodeAudioData(bytes.buffer, (buffer) => {
            const source = audioCtx.createBufferSource();
            source.buffer = buffer;
            source.connect(audioCtx.destination);
            source.start(0);
            console.log("[Audio] Pomyślnie odtworzono wskazówki głosowe (Base64).");
        });
    } catch (err) {
        console.error("[Audio] Błąd odtwarzania bazy64 przez Web Audio API:", err);
    }
}

// Obsługa komunikatów statusu/analizy z backendu
function handleServerMessage(msg) {
    switch (msg.type) {
        case 'status':
            statusMessage.textContent = msg.message;
            if (msg.message.includes("analizę") || msg.message.includes("głosowych")) {
                analysisIndicator.classList.remove('hidden');
            } else {
                analysisIndicator.classList.add('hidden');
            }
            break;
            
        case 'analysis_result':
            analysisIndicator.classList.add('hidden');
            // Backend w nowej wersji przysyła pola bezpośrednio w `msg`
            const dataToDisplay = msg.data ? msg.data : msg;
            displayAnalysis(dataToDisplay);
            
            // Odtwórz audio wysłane w formacie base64 za pomocą Web Audio API
            if (dataToDisplay.audio_base64) {
                playBase64Audio(dataToDisplay.audio_base64);
            }
            break;
            
        case 'error':
            analysisIndicator.classList.add('hidden');
            statusMessage.textContent = `Błąd: ${msg.message}`;
            break;
    }
}

// Wyświetlenie nowej wskazówki z analizy
function displayAnalysis(data) {
    if (!data.has_tip || !data.tip_text) {
        return; // Brak błędu do zgłoszenia
    }

    const bubble = document.createElement('div');
    bubble.className = 'coach-bubble';
    
    let targetHtml = '';
    if (data.target_player) {
        targetHtml = `<div class="player-target">Do: ${data.target_player}</div><br>`;
    }

    bubble.innerHTML = `
        <span class="coach-avatar">🎾</span>
        <div class="bubble-content">
            ${targetHtml}
            <strong>Trener AI:</strong> ${data.tip_text}
        </div>
    `;

    coachFeed.appendChild(bubble);
    
    // Przewiń na dół
    coachFeed.scrollTop = coachFeed.scrollHeight;
}

// Uruchomienie nagrywania i wysyłania paczek wideo
function startRecording() {
    if (!stream) return;

    recordingActive = true;
    btnStart.disabled = true;
    btnStop.disabled = false;
    recordingIndicator.classList.remove('hidden');
    
    startNewChunkRecording();
    statusMessage.textContent = "Trwa nagrywanie kortu. AI nasłuchuje końca wymiany...";
}

// Funkcja pomocnicza do nagrywania krótkich, kompletnych fragmentów
function startNewChunkRecording() {
    if (!recordingActive) return;

    const options = { mimeType: 'video/webm;codecs=vp8' };
    let chosenType = 'video/webm';
    if (!MediaRecorder.isTypeSupported(chosenType)) {
        chosenType = 'video/mp4';
    }
    
    try {
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: chosenType,
            videoBitsPerSecond: 250000 
        });
    } catch (e) {
        mediaRecorder = new MediaRecorder(stream);
    }

    mediaRecorder.ondataavailable = async (event) => {
        if (event.data && event.data.size > 0) {
            sendChunk(event.data);
        }
    };

    mediaRecorder.onstop = () => {
        // Zatrzymane na żądanie użytkownika. Nie restartujemy automatycznie.
    };

    // Uruchomienie nagrywania z parametrem timeslice = 3000ms. 
    // Przeglądarka automatycznie wyemituje ondataavailable co 3 sekundy.
    mediaRecorder.start(3000);
}

// Zatrzymanie nagrywania
function stopRecording() {
    recordingActive = false;
    btnStart.disabled = false;
    btnStop.disabled = true;
    recordingIndicator.classList.add('hidden');
    analysisIndicator.classList.add('hidden');

    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    statusMessage.textContent = "Sesja treningowa zatrzymana.";
}

// Wysłanie paczki wideo przez HTTP POST
async function sendChunk(blob) {
    const backendUrl = backendUrlInput.value.trim();
    const url = `${backendUrl}/api/upload-chunk?session_id=${sessionId}`;

    const formData = new FormData();
    // Nadajemy odpowiednie rozszerzenie w zależności od typu
    const fileExt = blob.type.includes('mp4') ? 'mp4' : 'webm';
    formData.append('file', blob, `chunk.${fileExt}`);

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.status === 'motion_stopped') {
            console.log("[PWA] Wykryto brak ruchu, serwer rozpoczął analizę.");
        }
    } catch (err) {
        console.error("Błąd wysyłania paczki:", err);
    }
}

// Event Listeners
btnStart.addEventListener('click', () => {
    // Wymóg konfiguracji graczy
    if (!playersConfig) {
        alert("Przed rozpoczęciem treningu musisz skonfigurować wygląd graczy!");
        playersModal.classList.remove('hidden');
        return;
    }

    // Odblokowanie Web Audio API na iOS (musi nastąpić w evencie interakcji użytkownika)
    initAudio();

    // Połączenie przed startem sesji
    connectWebSocket();
    // Odczekanie chwili na ustanowienie połączenia i start
    setTimeout(startRecording, 500);
});

btnStop.addEventListener('click', stopRecording);

cameraSelect.addEventListener('change', startCameraPreview);

btnRegenSession.addEventListener('click', () => {
    if (recordingActive) {
        alert("Zatrzymaj trening przed zmianą sesji.");
        return;
    }
    sessionId = generateUUID();
    sessionIdInput.value = sessionId;
    connectWebSocket();
});

// Obsługa modala konfiguracji graczy
if (btnConfigPlayers) {
    btnConfigPlayers.addEventListener('click', () => {
        playersModal.classList.remove('hidden');
    });
}

if (btnCloseModal) {
    btnCloseModal.addEventListener('click', () => {
        playersModal.classList.add('hidden');
    });
}

if (btnSavePlayers) {
    btnSavePlayers.addEventListener('click', () => {
        const playerA = {
            name: document.getElementById('player-a-name').value.trim(),
            gender: document.getElementById('player-a-gender').value,
            look: document.getElementById('player-a-look').value.trim()
        };
        const playerB = {
            name: document.getElementById('player-b-name').value.trim(),
            gender: document.getElementById('player-b-gender').value,
            look: document.getElementById('player-b-look').value.trim()
        };
        
        if (!playerA.name || !playerA.look || !playerB.name || !playerB.look) {
            alert("Wypełnij imiona i charakterystyczny ubiór dla obu graczy!");
            return;
        }
        
        playersConfig = { playerA, playerB };
        localStorage.setItem('squash_players_config', JSON.stringify(playersConfig));
        statusMessage.textContent = "Zapisano konfigurację graczy. Gotowy do rozpoczęcia treningu.";
        playersModal.classList.add('hidden');
        
        // Restart connection to pass new config
        connectWebSocket();
    });
}

// Obsługa zakładek na telefonie
const tabCamera = document.getElementById('tab-camera');
const tabFeedback = document.getElementById('tab-feedback');
const cameraPanel = document.getElementById('camera-panel');
const feedbackPanel = document.getElementById('feedback-panel');

if (tabCamera && tabFeedback) {
    tabCamera.addEventListener('click', () => {
        tabCamera.classList.add('active');
        tabFeedback.classList.remove('active');
        cameraPanel.classList.remove('mobile-hidden');
        feedbackPanel.classList.add('mobile-hidden');
    });

    tabFeedback.addEventListener('click', () => {
        tabFeedback.classList.add('active');
        tabCamera.classList.remove('active');
        feedbackPanel.classList.remove('mobile-hidden');
        cameraPanel.classList.add('mobile-hidden');
    });
}

// Obsługa wysuwanego panelu ustawień
const btnToggleSettings = document.getElementById('btn-toggle-settings');
const btnCloseSettings = document.getElementById('btn-close-settings');
const drawerOverlay = document.getElementById('drawer-overlay');
const settingsDrawer = document.getElementById('settings-drawer');

function openSettings() {
    settingsDrawer.classList.add('active');
    drawerOverlay.classList.add('active');
}

function closeSettings() {
    settingsDrawer.classList.remove('active');
    drawerOverlay.classList.remove('active');
}

if (btnToggleSettings) {
    btnToggleSettings.addEventListener('click', openSettings);
}
if (btnCloseSettings) {
    btnCloseSettings.addEventListener('click', closeSettings);
}
if (drawerOverlay) {
    drawerOverlay.addEventListener('click', closeSettings);
}

// Obsługa baneru ostrzegawczego backendu
const backendWarningBanner = document.getElementById('backend-warning-banner');
const btnConfigureBackendShortcut = document.getElementById('btn-configure-backend-shortcut');

if (btnConfigureBackendShortcut) {
    btnConfigureBackendShortcut.addEventListener('click', openSettings);
}

if (backendUrlInput) {
    backendUrlInput.addEventListener('input', () => {
        const val = backendUrlInput.value.trim();
        if (val) {
            localStorage.setItem('squash_backend_url', val);
            if (backendWarningBanner) {
                backendWarningBanner.classList.add('hidden');
            }
        }
    });
}

// Inicjalizacja przy załadowaniu strony
window.addEventListener('DOMContentLoaded', () => {
    initSession();
    getCameras();
    
    // Sprawdzenie konfiguracji backendu (pierwsze wejście)
    const savedUrl = localStorage.getItem('squash_backend_url');
    if (!savedUrl) {
        if (backendWarningBanner) {
            backendWarningBanner.classList.remove('hidden');
        }
    }
    
    // Sprawdzenie, czy to pierwsze wejście (brak konfiguracji graczy)
    if (!playersConfig) {
        statusMessage.innerHTML = '<span style="color: var(--accent-color); font-weight: 600;">⚠️ Konfiguracja graczy wymagana:</span> Kliknij "Skonfiguruj Graczy", aby podać imiona i ubiór.';
        setTimeout(() => {
            playersModal.classList.remove('hidden');
        }, 800);
    } else {
        statusMessage.textContent = "Skonfigurowano graczy. Gotowy do rozpoczęcia treningu.";
    }
    
    // Podłącz na dzień dobry po załadowaniu
    setTimeout(connectWebSocket, 1000);
});
