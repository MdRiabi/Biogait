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
            status = ui.label('Prêt à transmettre').classes('text-sm mt-4 italic')
            
            # Script JavaScript pour la capture et le streaming
            # Analyse espacée : On envoie une image toutes les 500ms (2 FPS) pour la stabilité
            ui.add_body_html('''
            <script>
            let stream = null;
            let ws = null;
            let timer = null;

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
                        // Lancer la boucle de capture (Analyse espacée - 500ms)
                        timer = setInterval(captureFrame, 500);
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
            
            // Activation au clic pour respecter les règles de sécurité navigateur
            window.addEventListener('click', () => {
                if (!stream) startStreaming();
            }, { once: true });
            </script>
            ''')
            
            ui.button('TAP TO START', on_click=lambda: status.set_text('Transmission en cours...')).classes('w-full mt-auto mb-8').style('background-color: #00F0FF; color: black')
            ui.label('Appuyez n\'importe où pour activer la caméra').classes('text-[10px] opacity-50')
