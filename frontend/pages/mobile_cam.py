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
            
            # Script JavaScript pour la capture et le streaming
            # Analyse espacée : On envoie une image toutes les 500ms (2 FPS) pour la stabilité
            ui.add_body_html('''
            <script>
            let stream = null;
            let ws = null;
            let timer = null;
            let isRecording = false;

            async function startStreaming() {
                try {
                    stream = await navigator.mediaDevices.getUserMedia({ 
                        video: { facingMode: "environment" }, // Caméra arrière
                        audio: false 
                    });
                    document.getElementById('mobile_video').srcObject = stream;
                    
                    // Connexion WebSocket locale au serveur BioGait
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/recognition/ws/mobile`);
                    
                    ws.onopen = () => {
                        console.log("Connecté au serveur PC");
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
                            console.error("Erreur lecture message serveur", e);
                        }
                    };
                } catch (err) {
                    alert("Erreur accès caméra : " + err.message);
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
                
                // Envoi de l'image en Base64
                const data = canvas.toDataURL('image/jpeg', 0.6); // Qualité 60%
                ws.send(JSON.stringify({
                    camera_id: "mobile_phone_01",
                    image: data
                }));
            }

            function getStatusElement() { return document.getElementById("mobile_status"); }
            function getResultElement() { return document.getElementById("mobile_result"); }

            async function toggleRecording() {
                if (!stream || !ws || ws.readyState !== WebSocket.OPEN) {
                    await startStreaming();
                }
                if (!ws || ws.readyState !== WebSocket.OPEN) return;

                const statusEl = getStatusElement();
                const resultEl = getResultElement();
                const buttonEl = document.getElementById("mobile_toggle_btn");

                if (!isRecording) {
                    if (resultEl) resultEl.textContent = "";
                    ws.send(JSON.stringify({ camera_id: "mobile_phone_01", action: "start" }));
                    timer = setInterval(captureFrame, 500);
                    isRecording = true;
                    if (statusEl) statusEl.textContent = "Enregistrement en cours...";
                    if (buttonEl) buttonEl.textContent = "STOP & ANALYZE";
                } else {
                    if (timer) {
                        clearInterval(timer);
                        timer = null;
                    }
                    ws.send(JSON.stringify({ camera_id: "mobile_phone_01", action: "stop" }));
                    isRecording = false;
                    if (statusEl) statusEl.textContent = "Analyse en cours...";
                    if (buttonEl) buttonEl.textContent = "TAP TO START";
                }
            }

            window.toggleBioGaitRecording = toggleRecording;
            
            </script>
            ''')
            
            def on_tap():
                ui.run_javascript('window.toggleBioGaitRecording && window.toggleBioGaitRecording();')

            ui.button('TAP TO START', on_click=on_tap).classes('w-full mt-auto mb-8').style('background-color: #00F0FF; color: black').props('id=mobile_toggle_btn')
            ui.label('1er clic: enregistrer | 2e clic: arrêter et analyser').classes('text-[10px] opacity-50')
