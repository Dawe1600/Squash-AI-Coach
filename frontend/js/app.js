// Squash AI Coach - Main Logic

// Stan aplikacji
let stream = null;
let mediaRecorder = null;
let socket = null;
let chunkInterval = null;
let sessionId = "";
let recordingActive = false;
let audioCtx = null; // Web Audio API Context
let currentLanguage = "pl";

// Słownik tłumaczeń interfejsu
const UI_TRANSLATIONS = {
    pl: {
        title: "Squash AI Coach",
        statusDisconnected: "Rozłączony",
        statusConnected: "Połączono",
        statusConnecting: "Łączenie...",
        statusError: "Błąd",
        btnConfigPlayers: "👤 Skonfiguruj Graczy",
        btnStart: "▶ Uruchom Trening",
        btnStop: "⏹ Zatrzymaj",
        cameraPanelTitle: "Podgląd z kortu",
        feedbackPanelTitle: "Status Analizy & Uwagi",
        statusMessageDefault: "Podłącz się i kliknij Uruchom, aby rozpocząć analizę...",
        statusMessageRecording: "Trwa nagrywanie kortu. AI nasłuchuje końca wymiany...",
        statusMessageStopped: "Sesja treningowa zatrzymana.",
        statusMessageConfigRequired: '<span style="color: var(--accent-color); font-weight: 600;">⚠️ Konfiguracja graczy wymagana:</span> Kliknij "Skonfiguruj Graczy", aby podać imiona i ubiór.',
        statusMessageConfigSaved: "Zapisano konfigurację graczy. Gotowy do rozpoczęcia treningu.",
        statusMessageReady: "Gotowy do rozpoczęcia treningu.",
        statusMessageConnectionInterrupted: "Połączenie z serwerem przerwane. Próba ponownego połączenia...",
        warningBannerText: "Serwer backend (FastAPI) nie został skonfigurowany. Zweryfikuj adres połączenia, aby rozpocząć trening.",
        warningBannerBtn: "Skonfiguruj",
        modalTitle: "Konfiguracja Graczy",
        modalDesc: "Aby trener AI zwracał się po imieniu, opisz wygląd graczy.",
        modalPlayerAName: "Imię",
        modalPlayerAGender: "Płeć",
        modalPlayerALook: "Charakterystyczny ubiór",
        modalSave: "Zapisz",
        modalCancel: "Anuluj",
        genderMale: "Mężczyzna",
        genderFemale: "Kobieta",
        drawerTitle: "Ustawienia",
        drawerBackendLabel: "Serwer Backend (FastAPI):",
        drawerSessionLabel: "ID Sesji:",
        coachBubbleIntro: "<strong>Trener AI:</strong> Zaczynamy! Grajcie normalnie, a ja będę rzucał krótkie uwagi co jakiś czas, jeśli zauważę powtarzający się błąd.",
        tabCameraBtn: "Kamera & Sterowanie",
        tabFeedbackBtn: "Uwagi Trenera",
        warningConnectionLost: "Połączenie z serwerem backend (FastAPI) zostało przerwane lub nie mogło zostać nawiązane.",
        warningConnectionError: "Błąd połączenia z serwerem backend. Upewnij się, że serwer działa.",
        errorPrefix: "Błąd: ",
        recordingText: "NAGRYWANIE",
        coachName: "Trener AI",
        targetTo: "Do",
        instructions: `
            <h3>Jak uruchomić backend?</h3>
            <p>Aby uruchomić własny serwer analizy AI:</p>
            <ol>
                <li>Pobierz kod projektu:
                    <code>git clone https://github.com/Dawe1600/Squash-AI-Coach.git</code>
                </li>
                <li>Zainstaluj wymagane biblioteki:
                    <code>pip install -r requirements.txt</code>
                </li>
                <li>Uruchom serwer lokalnie:
                    <code>uvicorn backend.app.main:app --port 8080 --reload</code>
                </li>
                <li><strong>Alternatywa (Hosting za darmo):</strong> Możesz utworzyć "Space" na platformie <strong>Hugging Face Spaces</strong> (jako Docker), skopiować pliki backendu i podłączyć wygenerowany stamtąd link URL do aplikacji.
                </li>
            </ol>
            <div class="repo-link-wrapper">
                <a href="https://github.com/Dawe1600/Squash-AI-Coach" target="_blank" class="repo-link">
                    <span>📖</span> Dokumentacja na GitHubie
                </a>
            </div>
        `
    },
    en: {
        title: "Squash AI Coach",
        statusDisconnected: "Disconnected",
        statusConnected: "Connected",
        statusConnecting: "Connecting...",
        statusError: "Error",
        btnConfigPlayers: "👤 Configure Players",
        btnStart: "▶ Start Training",
        btnStop: "⏹ Stop",
        cameraPanelTitle: "Court Preview",
        feedbackPanelTitle: "Analysis Status & Tips",
        statusMessageDefault: "Connect and click Start to begin analysis...",
        statusMessageRecording: "Recording court. AI is listening for the end of the rally...",
        statusMessageStopped: "Training session stopped.",
        statusMessageConfigRequired: '<span style="color: var(--accent-color); font-weight: 600;">⚠️ Player configuration required:</span> Click "Configure Players" to provide names and clothing.',
        statusMessageConfigSaved: "Player configuration saved. Ready to start training.",
        statusMessageReady: "Ready to start training.",
        statusMessageConnectionInterrupted: "Connection to the server interrupted. Attempting to reconnect...",
        warningBannerText: "Backend server (FastAPI) is not configured. Verify connection address to start training.",
        warningBannerBtn: "Configure",
        modalTitle: "Player Configuration",
        modalDesc: "To have the AI coach address players by name, describe their appearance.",
        modalPlayerAName: "Name",
        modalPlayerAGender: "Gender",
        modalPlayerALook: "Distinctive clothing",
        modalSave: "Save",
        modalCancel: "Cancel",
        genderMale: "Male",
        genderFemale: "Female",
        drawerTitle: "Settings",
        drawerBackendLabel: "Backend Server (FastAPI):",
        drawerSessionLabel: "Session ID:",
        coachBubbleIntro: "<strong>AI Coach:</strong> Let's start! Play normally and I will give brief tips every now and then if I notice a recurring mistake.",
        tabCameraBtn: "Camera & Controls",
        tabFeedbackBtn: "Coach Feedback",
        warningConnectionLost: "Connection to the backend server (FastAPI) was lost or could not be established.",
        warningConnectionError: "Connection error to the backend server. Make sure the server is running.",
        errorPrefix: "Error: ",
        recordingText: "RECORDING",
        coachName: "AI Coach",
        targetTo: "To",
        instructions: `
            <h3>How to run the backend?</h3>
            <p>To run your own AI analysis server:</p>
            <ol>
                <li>Clone the project repository:
                    <code>git clone https://github.com/Dawe1600/Squash-AI-Coach.git</code>
                </li>
                <li>Install required packages:
                    <code>pip install -r requirements.txt</code>
                </li>
                <li>Run the server locally:
                    <code>uvicorn backend.app.main:app --port 8080 --reload</code>
                </li>
                <li><strong>Alternative (Free Hosting):</strong> You can create a "Space" on the <strong>Hugging Face Spaces</strong> platform (as Docker), copy the backend files, and connect the generated URL to this app.
                </li>
            </ol>
            <div class="repo-link-wrapper">
                <a href="https://github.com/Dawe1600/Squash-AI-Coach" target="_blank" class="repo-link">
                    <span>📖</span> Documentation on GitHub
                </a>
            </div>
        `
    }
};

// Funkcja aplikująca tłumaczenia do DOM
function applyLanguage(lang) {
    currentLanguage = lang;
    localStorage.setItem('squash_language', lang);
    const trans = UI_TRANSLATIONS[lang];

    // Tytuł strony i nagłówek
    document.title = trans.title;
    const logoTitle = document.querySelector('.logo-area h1');
    if (logoTitle) {
        logoTitle.innerHTML = lang === 'pl' ? 'Squash <span class="accent-text">AI Coach</span>' : 'Squash <span class="accent-text">AI Coach</span>';
    }
    
    // Status połączenia
    const connectionTextEl = connectionStatus ? connectionStatus.querySelector('.status-text') : null;
    if (connectionStatus && connectionTextEl) {
        if (connectionStatus.classList.contains('connected')) {
            connectionTextEl.textContent = trans.statusConnected;
        } else if (connectionStatus.classList.contains('disconnected')) {
            const currentTxt = connectionTextEl.textContent;
            if (currentTxt === UI_TRANSLATIONS.pl.statusConnecting || currentTxt === UI_TRANSLATIONS.en.statusConnecting || currentTxt === 'Łączenie...') {
                connectionTextEl.textContent = trans.statusConnecting;
            } else if (currentTxt === UI_TRANSLATIONS.pl.statusError || currentTxt === UI_TRANSLATIONS.en.statusError || currentTxt === 'Błąd') {
                connectionTextEl.textContent = trans.statusError;
            } else {
                connectionTextEl.textContent = trans.statusDisconnected;
            }
        }
    }

    // Przyciski główne
    if (btnConfigPlayers) btnConfigPlayers.innerHTML = `<span class="btn-icon">👤</span> ${lang === 'pl' ? 'Skonfiguruj Graczy' : 'Configure Players'}`;
    if (btnStart) btnStart.innerHTML = `<span class="btn-icon">▶</span> ${lang === 'pl' ? 'Uruchom Trening' : 'Start Training'}`;
    if (btnStop) btnStop.innerHTML = `<span class="btn-icon">⏹</span> ${lang === 'pl' ? 'Zatrzymaj' : 'Stop'}`;

    // Nagłówki paneli
    const cameraPanelHeader = document.querySelector('#camera-panel .card-header h2');
    if (cameraPanelHeader) cameraPanelHeader.textContent = trans.cameraPanelTitle;
    const feedbackPanelHeader = document.querySelector('#feedback-panel .card-header h2');
    if (feedbackPanelHeader) feedbackPanelHeader.textContent = trans.feedbackPanelTitle;

    // Komunikat statusu
    if (statusMessage) {
        const currentStatusText = statusMessage.innerHTML;
        if (currentStatusText === UI_TRANSLATIONS.pl.statusMessageDefault || currentStatusText === UI_TRANSLATIONS.en.statusMessageDefault || currentStatusText.startsWith("Podłącz się") || currentStatusText.startsWith("Connect and click")) {
            statusMessage.textContent = trans.statusMessageDefault;
        } else if (currentStatusText === UI_TRANSLATIONS.pl.statusMessageRecording || currentStatusText === UI_TRANSLATIONS.en.statusMessageRecording || currentStatusText.startsWith("Trwa nagrywanie") || currentStatusText.startsWith("Recording court")) {
            statusMessage.textContent = trans.statusMessageRecording;
        } else if (currentStatusText === UI_TRANSLATIONS.pl.statusMessageStopped || currentStatusText === UI_TRANSLATIONS.en.statusMessageStopped || currentStatusText.startsWith("Sesja treningowa") || currentStatusText.startsWith("Training session")) {
            statusMessage.textContent = trans.statusMessageStopped;
        } else if (currentStatusText === UI_TRANSLATIONS.pl.statusMessageConfigSaved || currentStatusText === UI_TRANSLATIONS.en.statusMessageConfigSaved || currentStatusText.startsWith("Zapisano konfigurację") || currentStatusText.startsWith("Player configuration saved")) {
            statusMessage.textContent = trans.statusMessageConfigSaved;
        } else if (currentStatusText === UI_TRANSLATIONS.pl.statusMessageReady || currentStatusText === UI_TRANSLATIONS.en.statusMessageReady || currentStatusText.startsWith("Gotowy do") || currentStatusText.startsWith("Ready to start")) {
            statusMessage.textContent = trans.statusMessageReady;
        } else if (currentStatusText === UI_TRANSLATIONS.pl.statusMessageConnectionInterrupted || currentStatusText === UI_TRANSLATIONS.en.statusMessageConnectionInterrupted || currentStatusText.startsWith("Połączenie z serwerem przerwane") || currentStatusText.startsWith("Connection to the server")) {
            statusMessage.textContent = trans.statusMessageConnectionInterrupted;
        } else if (currentStatusText.includes("Konfiguracja graczy wymagana") || currentStatusText.includes("Player configuration required")) {
            statusMessage.innerHTML = trans.statusMessageConfigRequired;
        }
    }

    // Baner ostrzegawczy backendu
    if (backendWarningBanner) {
        const warningText = backendWarningBanner.querySelector('.warning-banner-text');
        if (warningText) {
            const currentBannerText = warningText.textContent;
            if (currentBannerText === UI_TRANSLATIONS.pl.warningConnectionLost || currentBannerText === UI_TRANSLATIONS.en.warningConnectionLost || currentBannerText.includes("przerwane lub nie mogło")) {
                warningText.textContent = trans.warningConnectionLost;
            } else if (currentBannerText === UI_TRANSLATIONS.pl.warningConnectionError || currentBannerText === UI_TRANSLATIONS.en.warningConnectionError || currentBannerText.includes("Błąd połączenia z serwerem")) {
                warningText.textContent = trans.warningConnectionError;
            } else {
                warningText.textContent = trans.warningBannerText;
            }
        }
        const warningBtn = backendWarningBanner.querySelector('#btn-configure-backend-shortcut');
        if (warningBtn) warningBtn.textContent = lang === 'pl' ? 'Skonfiguruj' : 'Configure';
    }

    // Modal konfiguracji
    const modalHeader = document.querySelector('#players-modal .modal-card h2');
    if (modalHeader) modalHeader.textContent = trans.modalTitle;
    const modalDescEl = document.querySelector('#players-modal .modal-desc');
    if (modalDescEl) modalDescEl.textContent = trans.modalDesc;
    
    // Nazwy graczy w modalu
    const playerAHeader = document.querySelector('#players-modal .players-forms-container .player-config-box:nth-child(1) h3');
    if (playerAHeader) playerAHeader.textContent = lang === 'pl' ? 'Gracz A' : 'Player A';
    const playerBHeader = document.querySelector('#players-modal .players-forms-container .player-config-box:nth-child(2) h3');
    if (playerBHeader) playerBHeader.textContent = lang === 'pl' ? 'Gracz B' : 'Player B';

    // Wartości placeholderów w modalu
    const inputAName = document.getElementById('player-a-name');
    if (inputAName) inputAName.placeholder = lang === 'pl' ? 'np. Jan' : 'e.g. John';
    const inputALook = document.getElementById('player-a-look');
    if (inputALook) inputALook.placeholder = lang === 'pl' ? 'np. czarna koszulka' : 'e.g. black t-shirt';
    const inputBName = document.getElementById('player-b-name');
    if (inputBName) inputBName.placeholder = lang === 'pl' ? 'np. Anna' : 'e.g. Anna';
    const inputBLook = document.getElementById('player-b-look');
    if (inputBLook) inputBLook.placeholder = lang === 'pl' ? 'np. biała spódniczka' : 'e.g. white skirt';

    const labelNames = document.querySelectorAll('#players-modal .form-group label');
    if (labelNames.length >= 6) {
        labelNames[0].textContent = lang === 'pl' ? 'Imię' : 'Name';
        labelNames[1].textContent = lang === 'pl' ? 'Płeć' : 'Gender';
        labelNames[2].textContent = lang === 'pl' ? 'Charakterystyczny ubiór' : 'Distinctive clothing';
        labelNames[3].textContent = lang === 'pl' ? 'Imię' : 'Name';
        labelNames[4].textContent = lang === 'pl' ? 'Płeć' : 'Gender';
        labelNames[5].textContent = lang === 'pl' ? 'Charakterystyczny ubiór' : 'Distinctive clothing';
    }

    // Zmiana opcji płci w selectach
    const genderSelects = [document.getElementById('player-a-gender'), document.getElementById('player-b-gender')];
    genderSelects.forEach(select => {
        if (select) {
            const val = select.value;
            select.innerHTML = `
                <option value="${lang === 'pl' ? 'Mężczyzna' : 'Male'}">${lang === 'pl' ? 'Mężczyzna' : 'Male'}</option>
                <option value="${lang === 'pl' ? 'Kobieta' : 'Female'}">${lang === 'pl' ? 'Kobieta' : 'Female'}</option>
            `;
            // Mapowanie wartości przy zmianie języka
            if (val === 'Mężczyzna' && lang === 'en') select.value = 'Male';
            else if (val === 'Male' && lang === 'pl') select.value = 'Mężczyzna';
            else if (val === 'Kobieta' && lang === 'en') select.value = 'Female';
            else if (val === 'Female' && lang === 'pl') select.value = 'Kobieta';
            else select.value = val;
        }
    });

    const btnSavePlayersEl = document.getElementById('btn-save-players');
    if (btnSavePlayersEl) btnSavePlayersEl.textContent = lang === 'pl' ? 'Zapisz' : 'Save';
    const btnCloseModalEl = document.getElementById('btn-close-modal');
    if (btnCloseModalEl) btnCloseModalEl.textContent = lang === 'pl' ? 'Anuluj' : 'Cancel';

    // Panel boczny ustawień (Drawer)
    const drawerHeaderEl = document.querySelector('#settings-drawer .drawer-header h2');
    if (drawerHeaderEl) drawerHeaderEl.textContent = trans.drawerTitle;
    
    const drawerLabels = document.querySelectorAll('#settings-drawer .settings-group label');
    if (drawerLabels.length >= 2) {
        drawerLabels[0].textContent = lang === 'pl' ? 'Serwer Backend (FastAPI):' : 'Backend Server (FastAPI):';
        drawerLabels[1].textContent = lang === 'pl' ? 'ID Sesji:' : 'Session ID:';
    }

    // Placeholdery panelu bocznego
    const backendUrlInputEl = document.getElementById('backend-url');
    if (backendUrlInputEl) {
        backendUrlInputEl.placeholder = lang === 'pl' ? 'np. https://twoja-przestrzen.hf.space' : 'e.g. https://your-space.hf.space';
    }

    // Tytuły i podpowiedzi przycisków (Tooltips)
    const settingsBtn = document.getElementById('btn-toggle-settings');
    if (settingsBtn) settingsBtn.title = lang === 'pl' ? 'Ustawienia' : 'Settings';
    const closeSettingsBtn = document.getElementById('btn-close-settings');
    if (closeSettingsBtn) closeSettingsBtn.title = lang === 'pl' ? 'Zamknij' : 'Close';
    const regenSessionBtn = document.getElementById('btn-regen-session');
    if (regenSessionBtn) regenSessionBtn.title = lang === 'pl' ? 'Generuj nowe ID' : 'Generate new ID';

    // Tekst wskaźnika nagrywania
    const recordingTextEl = document.getElementById('recording-text');
    if (recordingTextEl) {
        recordingTextEl.textContent = trans.recordingText;
    }

    // Dynamiczna zmiana sugerowanej odzieży (datalist)
    const clothingSuggestions = {
        pl: [
            "czarna koszulka",
            "biała koszulka",
            "niebieska koszulka",
            "czerwona koszulka",
            "czarne spodenki",
            "białe spodenki",
            "biała spódniczka",
            "czarna spódniczka",
            "jasne buty",
            "ciemne buty",
            "rakieta z czerwoną owijką",
            "opaska na głowie"
        ],
        en: [
            "black t-shirt",
            "white t-shirt",
            "blue t-shirt",
            "red t-shirt",
            "black shorts",
            "white shorts",
            "white skirt",
            "black skirt",
            "light shoes",
            "dark shoes",
            "racket with red grip",
            "headband"
        ]
    };
    const datalist = document.getElementById('clothing-options');
    if (datalist) {
        datalist.innerHTML = clothingSuggestions[lang].map(item => `<option value="${item}">`).join('');
    }

    // Instrukcje w panelu bocznym
    const instructionsBlock = document.querySelector('#settings-drawer .drawer-instructions');
    if (instructionsBlock) {
        instructionsBlock.innerHTML = trans.instructions;
    }

    // Dymek powitalny trenera (jeśli istnieje w kanale)
    const introBubbleContent = document.querySelector('.coach-bubble.intro .bubble-content');
    if (introBubbleContent) {
        introBubbleContent.innerHTML = trans.coachBubbleIntro;
    }

    // Zakładki mobilne
    if (tabCamera) tabCamera.textContent = trans.tabCameraBtn;
    if (tabFeedback) tabFeedback.textContent = trans.tabFeedbackBtn;
}

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
const backendWarningBanner = document.getElementById('backend-warning-banner');
const btnConfigureBackendShortcut = document.getElementById('btn-configure-backend-shortcut');

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

    // Odczyt zapisanego języka
    currentLanguage = localStorage.getItem('squash_language') || 'pl';
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) {
        languageSelect.value = currentLanguage;
    }
    applyLanguage(currentLanguage);

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
    return 'session_' + (crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 11));
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
        socket.onclose = null;
        socket.onerror = null;
        socket.close();
    }

    const backendUrl = backendUrlInput.value.trim();
    localStorage.setItem('squash_backend_url', backendUrl);

    // Konwersja http(s) do ws(s)
    let wsUrl = backendUrl.replace(/^http/, 'ws');
    // Dodanie endpointu sesji z językiem
    wsUrl = `${wsUrl}/ws/session?session_id=${sessionId}&lang=${currentLanguage}`;
    
    // Dodanie konfiguracji graczy
    if (playersConfig) {
        wsUrl += `&players_config=${encodeURIComponent(JSON.stringify(playersConfig))}`;
    }

    updateConnectionStatus(false, UI_TRANSLATIONS[currentLanguage].statusConnecting);

    socket = new WebSocket(wsUrl);
    socket.binaryType = 'blob';

    socket.onopen = () => {
        updateConnectionStatus(true, UI_TRANSLATIONS[currentLanguage].statusConnected);
        statusMessage.textContent = UI_TRANSLATIONS[currentLanguage].statusMessageReady;
        if (backendWarningBanner) {
            backendWarningBanner.classList.add('hidden');
        }
    };

    socket.onclose = () => {
        updateConnectionStatus(false, UI_TRANSLATIONS[currentLanguage].statusDisconnected);
        if (recordingActive) {
            statusMessage.textContent = UI_TRANSLATIONS[currentLanguage].statusMessageConnectionInterrupted;
            setTimeout(connectWebSocket, 3000);
        }
        showBackendWarning(UI_TRANSLATIONS[currentLanguage].warningConnectionLost);
    };

    socket.onerror = (err) => {
        console.error("Błąd WebSocket:", err);
        updateConnectionStatus(false, UI_TRANSLATIONS[currentLanguage].statusError);
        showBackendWarning(UI_TRANSLATIONS[currentLanguage].warningConnectionError);
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

function showBackendWarning(message) {
    if (backendWarningBanner) {
        const textEl = backendWarningBanner.querySelector('.warning-banner-text');
        if (textEl) {
            textEl.textContent = message;
        }
        backendWarningBanner.classList.remove('hidden');
    }
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
}

// Odtwarzanie wskazówek głosowych (Web Audio API)
async function playAudioFeedback(blob) {
    if (!audioCtx) return;
    try {
        const arrayBuffer = await blob.arrayBuffer();
        audioCtx.decodeAudioData(arrayBuffer, (buffer) => {
            const source = audioCtx.createBufferSource();
            source.buffer = buffer;
            source.connect(audioCtx.destination);
            source.start(0);
            console.log("[Audio] Pomyślnie odtworzono wskazówki głosowe (Blob).");
        });
    } catch (err) {
        console.error("[Audio] Błąd odtwarzania przez Web Audio API:", err);
    }
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
            statusMessage.textContent = `${UI_TRANSLATIONS[currentLanguage].errorPrefix}${msg.message}`;
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
        targetHtml = `<div class="player-target">${UI_TRANSLATIONS[currentLanguage].targetTo}: ${data.target_player}</div><br>`;
    }

    bubble.innerHTML = `
        <span class="coach-avatar">🎾</span>
        <div class="bubble-content">
            ${targetHtml}
            <strong>${UI_TRANSLATIONS[currentLanguage].coachName}:</strong> ${data.tip_text}
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
    statusMessage.textContent = UI_TRANSLATIONS[currentLanguage].statusMessageRecording;
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
    statusMessage.textContent = UI_TRANSLATIONS[currentLanguage].statusMessageStopped;
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
// Obsługa przełącznika języka
const languageSelect = document.getElementById('language-select');
if (languageSelect) {
    languageSelect.addEventListener('change', () => {
        applyLanguage(languageSelect.value);
        connectWebSocket();
    });
}

btnStart.addEventListener('click', () => {
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
        statusMessage.textContent = UI_TRANSLATIONS[currentLanguage].statusMessageConfigSaved;
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
        statusMessage.innerHTML = UI_TRANSLATIONS[currentLanguage].statusMessageConfigRequired;
        setTimeout(() => {
            playersModal.classList.remove('hidden');
        }, 800);
    } else {
        statusMessage.textContent = UI_TRANSLATIONS[currentLanguage].statusMessageConfigSaved;
    }
    
    // Podłącz na dzień dobry po załadowaniu
    setTimeout(connectWebSocket, 1000);
});
