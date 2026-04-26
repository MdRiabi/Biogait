from nicegui import ui, app
import socket

def mobile_cam_page():
    """Page optimisée pour smartphone pour servir de caméra distante."""
    @ui.page('/mobile-cam')
    def page():
        # Configuration spécifique mobile
        ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">')
        ui.add_head_html('<style>body { background-color: #0A0A1A; color: #E0E0FF; overflow: hidden; }</style>')
        
        with ui.column().classes('w-full h-full items-center p-4'):
            ui.label('BIOGAIT MOBILE').classes('text-2xl font-bold text-primary mt-4 tracking-widest')
            ui.label('CAPTEUR NOMADE ACTIF').classes('text-xs text-secondary mb-8')
            
            # Zone Aperçu Caméra
            video_view = ui.html('<video id="mobile_video" autoplay playsinline style="width: 100%; border-radius: 10px; border: 2px solid #00F0FF;"></video>')
            
            # Status
            status = ui.label('Prêt à transmettre').classes('text-sm mt-4 italic').props('id=mobile_status')
            result = ui.label('').classes('text-sm mt-2 font-bold').props('id=mobile_result')
            
            # Réception des logs du téléphone vers le terminal Python
            ui.on('mobile_log', lambda e: print(f"📱 [PHONE LOG]: {e.args}", flush=True))

            # Script JavaScript pour la capture et le streaming
            # Analyse espacée : On envoie une image toutes les 500ms (2 FPS) pour la stabilité
            ui.add_body_html('''
            <script>
            let stream = null;
            let ws = null;
            let timer = null;
            let isRecording = false;

            function logDebug(msg) {
                const logEl = document.getElementById("mobile_debug_log");
                if (logEl) {
                    logEl.innerHTML += `<div>[${new Date().toLocaleTimeString()}] ${msg}</div>`;
                    logEl.scrollTop = logEl.scrollHeight;
                }
                console.log(msg);
                try {
                    if (window.NiceGUI) {
                        window.NiceGUI.emit('mobile_log', msg);
                    }
                } catch(e) {}
            }

            async function startStreaming() {
                logDebug("startStreaming: Initialisation...");
                try {
                    if (navigator.mediaDevices === undefined) {
                        throw new Error("navigator.mediaDevices est undefined (le site n'est probablement pas en HTTPS ?)");
                    }
                    logDebug("startStreaming: Demande d'accès caméra...");
                    stream = await navigator.mediaDevices.getUserMedia({ 
                        video: { facingMode: "environment" }, 
                        audio: false 
                    });
                    logDebug("startStreaming: Caméra obtenue !");
                    document.getElementById('mobile_video').srcObject = stream;
                    
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/api/v1/recognition/ws/mobile`;
                    logDebug(`startStreaming: Connexion WebSocket -> ${wsUrl}`);
                    
                    ws = new WebSocket(wsUrl);
                    
                    ws.onopen = () => {
                        logDebug("WebSocket: CONNECTÉ au serveur PC");
                    };

                    ws.onmessage = (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            if (data.type === "mobile_status" && data.status === "recording_started") {
                                const s = getStatusElement();
                                if (s) s.textContent = "Enregistrement en cours...";
                            }
                            if (data.type === "mobile_result" && data.status === "analysis_done") {
                                const s = getStatusElement();
                                const r = getResultElement();
                                const rec = data.result || {};
                                const conf = Number(rec.confidence || 0).toFixed(1);
                                if (s) s.textContent = "Analyse terminée";
                                if (r) {
                                    if (rec.identified) {
                                        r.textContent = `Personne identifiée (${conf}%)`;
                                        r.style.color = "#00FF88";
                                    } else {
                                        r.textContent = `Personne inconnue / non identifiée (${conf}%)`;
                                        r.style.color = "#FF4D4D";
                                    }
                                }
                            }
                        } catch (e) {
                            logDebug("WebSocket Erreur lecture: " + e.message);
                        }
                    };
                    ws.onerror = (e) => {
                        logDebug("WebSocket Erreur !");
                    };
                    ws.onclose = () => {
                        logDebug("WebSocket Fermé !");
                    };
                } catch (err) {
                    logDebug("❌ ERREUR CAMÉRA: " + err.message + " (" + err.name + ")");
                }
            }

            function captureFrame() {
                if (!ws || ws.readyState !== WebSocket.OPEN) return;
                
                const video = document.getElementById('mobile_video');
                const canvas = document.createElement('canvas');
                canvas.width = video.videoWidth / 2; // Compression légère
                canvas.height = video.videoHeight / 2;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                
                const data = canvas.toDataURL('image/jpeg', 0.6); 
                ws.send(JSON.stringify({
                    camera_id: "mobile_phone_01",
                    image: data
                }));
            }

            function getStatusElement() { return document.getElementById("mobile_status"); }
            function getResultElement() { return document.getElementById("mobile_result"); }

            async function toggleRecording() {
                logDebug("=== Bouton cliqué ===");
                try {
                    if (!stream || !ws || ws.readyState !== WebSocket.OPEN) {
                        logDebug("toggleRecording: streaming non actif, lancement...");
                        await startStreaming();
                    }
                    if (!ws || ws.readyState !== WebSocket.OPEN) {
                        logDebug("toggleRecording: Abandon, WebSocket non ouvert.");
                        return;
                    }

                    const statusEl = getStatusElement();
                    const resultEl = getResultElement();
                    const buttonEl = document.getElementById("mobile_toggle_btn");

                    if (!isRecording) {
                        if (resultEl) resultEl.textContent = "";
                        ws.send(JSON.stringify({ camera_id: "mobile_phone_01", action: "start" }));
                        timer = setInterval(captureFrame, 500);
                        isRecording = true;
                        if (statusEl) statusEl.textContent = "Enregistrement en cours...";
                        if (buttonEl) buttonEl.innerText = "STOP & ANALYZE";
                        logDebug("Action: START envoyée");
                    } else {
                        if (timer) {
                            clearInterval(timer);
                            timer = null;
                        }
                        ws.send(JSON.stringify({ camera_id: "mobile_phone_01", action: "stop" }));
                        isRecording = false;
                        if (statusEl) statusEl.textContent = "Analyse en cours...";
                        if (buttonEl) buttonEl.innerText = "TAP TO START";
                        logDebug("Action: STOP envoyée");
                    }
                } catch(e) {
                    logDebug("❌ ERREUR TOGGLE: " + e.message);
                }
            }

            const attachBtn = () => {
                const btn = document.getElementById("mobile_toggle_btn");
                if (btn) {
                    btn.removeEventListener("click", toggleRecording);
                    btn.addEventListener("click", toggleRecording);
                    logDebug("Evénement bouton attaché avec succès.");
                } else {
                    setTimeout(attachBtn, 200);
                }
            };
            attachBtn();
            
            </script>
            ''')
            
            ui.html('''
            <button id="mobile_toggle_btn" style="width: 100%; margin-top: auto; margin-bottom: 1rem; background-color: #00F0FF; color: black; padding: 12px; font-weight: bold; border-radius: 4px; border: none; font-size: 16px; cursor: pointer; text-transform: uppercase; box-shadow: 0 4px 6px rgba(0, 240, 255, 0.3);">
                TAP TO START
            </button>
            <div id="mobile_debug_log" style="width: 100%; height: 100px; overflow-y: auto; background-color: #111; color: #0f0; font-family: monospace; font-size: 10px; padding: 5px; margin-bottom: 1rem; border: 1px solid #333;">
                [Log initialisé]
            </div>
            ''')
            ui.label('1er clic: enregistrer | 2e clic: arrêter et analyser').classes('text-[10px] opacity-50')
