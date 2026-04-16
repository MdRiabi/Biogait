from nicegui import ui, app
from frontend.theme import THEME, cyber_card
from frontend.components.sidebar import sidebar
from frontend.auth import check_auth
import asyncio
import json

class MonitoringPage:
    def __init__(self):
        self.events = []
        self.event_container = None

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
            # Garder seulement les 20 derniers events
            if len(self.event_container.default_slot.children) > 20:
                self.event_container.default_slot.children.pop(0)

    def content(self):
        """Définit le contenu de la page de monitoring."""
        check_auth()
        sidebar()
        
        with ui.row().classes('w-full items-stretch'):
            # --- COLONNE GAUCHE : FLUX VIDÉO ---
            with ui.column().classes('flex-grow'):
                with cyber_card().classes('w-full'):
                    ui.label('FLUX LIVE - ENTRÉE PRINCIPALE').classes('text-sm font-bold mb-2')
                    # On utilise une image qui se rafraîchit ou on pourrait utiliser le WS
                    # Pour la démo Dashboard, on simule l'affichage
                    self.video_placeholder = ui.interactive_image().classes('w-full bg-black rounded')
                    ui.label('Anonymisation active ✅').classes('text-xs italic text-success mt-1')

            # --- COLONNE DROITE : ALERTES EN DIRECT ---
            with ui.column().classes('w-80'):
                with cyber_card().classes('w-full h-full'):
                    ui.label('ÉVÉNEMENTS RÉCENTS').classes('text-sm font-bold mb-4')
                    self.event_container = ui.column().classes('w-full overflow-y-auto').style('max-height: 500px')

        # Démarrage de la boucle asynchrone pour écouter les alertes backend si nécessaire
        # En production, on utiliserait le DashboardConnectionManager du backend
        # Ici on simule ou on se connecte au WS local
        ui.timer(2.0, lambda: self.fake_event(), once=True)

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
