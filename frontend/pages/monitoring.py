from nicegui import ui, app
from frontend.theme import THEME, cyber_card
from frontend.components.sidebar import sidebar
from frontend.auth import check_auth
from frontend.components.qr_generator import mobile_qr_component
from app.core.state import latest_frames
import asyncio
import json

class MonitoringPage:
    def __init__(self):
        self.events = []
        self.event_container = None
        self.confidence_threshold = 0.85

    def handle_socket_msg(self, data: dict):
        """Répartit les messages selon leur type (alerte ou image)."""
        msg_type = data.get('type')
        if msg_type == 'alert':
            res = data.get('recognition_result', {})
            conf = res.get('confidence', 0) / 100.0
            identified = res.get('identified', False)
            person = res.get('user_id', 'Inconnu')
            
            self.add_event(data)
            
            if identified:
                ui.notify(f"ACCÈS AUTORISÉ : {person} ({conf*100:.1f}%)", position='top-right', type='positive')
            elif conf > 0.4:
                ui.notify(f"SUJET NON IDENTIFIÉ ⚠️ ({conf*100:.1f}%)", position='top-right', type='warning')
        elif msg_type == 'frame':
            self.video_placeholder.set_source(data.get('image'))

    def add_event(self, event_data: dict):
        """Ajoute un événement à la liste en direct."""
        res = event_data.get('recognition_result', {})
        user_id = res.get('user_id', 'Inconnu')
        confidence = res.get('confidence', 0)
        identified = res.get('identified', False)
        
        status_color = THEME['success'] if identified else THEME['error']
        status_text = "AUTORISÉ" if identified else "REJETÉ"
        
        event_html = f'''
        <div class="p-2 mb-2 border-l-4" style="border-color: {status_color}; background: {THEME['surface']}">
            <div class="flex justify-between">
                <span class="font-bold text-xs" style="color: {THEME['textMuted']}">CAMERA: {event_data.get('camera_id')}</span>
                <span class="font-bold text-xs" style="color: {status_color}">{status_text}</span>
            </div>
            <div class="text-sm"><b>{user_id}</b> ({confidence:.1f}%)</div>
        </div>
        '''
        
        if self.event_container:
            with self.event_container:
                ui.html(event_html)
            if len(self.event_container.default_slot.children) > 20:
                self.event_container.default_slot.children.pop(0)

    def content(self):
        """Définit le contenu de la page de monitoring."""
        check_auth()
        sidebar()
        
        ui.add_body_html('''
        <script>
        const alertWs = new WebSocket(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/recognition/ws/dashboard/alerts`);
        alertWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            NiceGUI.emit('biogait_event', data);
        };
        </script>
        ''')
        
        ui.on('biogait_event', lambda msg: self.handle_socket_msg(msg.args))
        
        with ui.row().classes('w-full items-stretch'):
            with ui.column().classes('flex-grow'):
                with cyber_card().classes('w-full'):
                    ui.label('FLUX LIVE - ENTRÉE PRINCIPALE').classes('text-sm font-bold mb-2')
                    self.video_placeholder = ui.interactive_image().classes('w-full bg-black rounded')
                    with ui.row().classes('items-center'):
                        self.traffic_led = ui.icon('circle', color='grey').classes('text-[10px]')
                        ui.label('Anonymisation active ✅').classes('text-xs italic text-success mt-1')

            with ui.column().classes('w-80'):
                with cyber_card().classes('w-full h-full'):
                    ui.label('ÉVÉNEMENTS RÉCENTS').classes('text-sm font-bold mb-4')
                    self.event_container = ui.column().classes('w-full overflow-y-auto').style('max-height: 400px')
                
                mobile_qr_component()
                
                with cyber_card().classes('w-full mt-4'):
                    ui.label('PARAMÈTRES SÉCURITÉ').classes('text-xs font-bold mb-2 text-primary')
                    ui.label(f'Seuil de confiance').classes('text-[10px] text-muted')
                    threshold_label = ui.label(f'{int(self.confidence_threshold*100)}%').classes('text-xs font-bold')
                    
                    def update_threshold(e):
                        self.confidence_threshold = e.value / 100.0
                        threshold_label.set_text(f'{e.value}%')
                        
                    ui.slider(min=50, max=99, value=int(self.confidence_threshold*100), on_change=update_threshold).classes('w-full')
                    ui.label('Mode RGPD: ACTIF').classes('text-[8px] text-success italic mt-1')

        ui.timer(0.5, self.update_live_feed)

    def update_live_feed(self):
        """Récupère la dernière image reçue depuis le stockage global."""
        if latest_frames:
            cam_id = list(latest_frames.keys())[0]
            img_data = latest_frames[cam_id]
            self.video_placeholder.set_source(img_data)
            
            current_color = self.traffic_led.props['color']
            self.traffic_led.props(f'color={"primary" if current_color == "grey" else "grey"}')
        else:
            self.traffic_led.props('color=grey')

    def fake_event(self):
        """Simulation d'un événement pour la démo visuelle initiale."""
        self.add_event({
            "camera_id": "cam_front_door",
            "recognition_result": {
                "user_id": "test_user_01",
                "confidence": 89.5,
                "identified": True
            }
        })

def monitoring_page():
    @ui.page('/')
    def page():
        p = MonitoringPage()
        p.content()
