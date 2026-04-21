from nicegui import ui
from frontend.theme import THEME, cyber_card
from frontend.components.sidebar import sidebar
from frontend.auth import check_auth
from app.db.session import SessionLocal
from app.models.alert import DetectionAlert
from app.models.audit import AuditLog
from sqlalchemy.future import select
from sqlalchemy import desc
from datetime import datetime
from app.core.ia.reporting import generate_report
import os
import tempfile
from nicegui import app

class AlertsPage:
    async def get_alerts(self):
        """Récupère les alertes de détection réelles de la DB."""
        async with SessionLocal() as db:
            result = await db.execute(select(DetectionAlert).order_by(desc(DetectionAlert.timestamp)).limit(50))
            alerts = result.scalars().all()
            return [
                {
                    "timestamp": a.timestamp.strftime("%H:%M:%S") if a.timestamp else "N/A",
                    "camera_id": a.camera_id,
                    "username": a.username or "Inconnu",
                    "status": "DÉTECTÉ" if a.identified else "INCONNU",
                    "confidence": f"{a.confidence*100:.1f}%" if a.confidence else "0%",
                    "anomalie": "OUI" if a.is_anomaly else "NON"
                } for a in alerts
            ]

    async def content(self):
        check_auth()
        sidebar()
        
        ui.label('JOURNAL DES ALERTES SÉCURITÉ').classes('text-2xl font-bold mb-6 text-warning')
        
        with ui.row().classes('w-full items-center mb-4'):
            ui.select(['INFO', 'ATTENTION', 'CRITIQUE'], label='Filtrer par niveau').classes('w-64')
            ui.button('EXPORTER ANALYSE (PDF)', icon='print', color='warning', on_click=lambda: self.export_pdf()).classes('ml-auto')

        with cyber_card().classes('w-full'):
            rows = await self.get_alerts()
            columns = [
                {'name': 'timestamp', 'label': 'HEURE', 'field': 'timestamp', 'align': 'left'},
                {'name': 'camera_id', 'label': 'CAMÉRA', 'field': 'camera_id', 'align': 'left'},
                {'name': 'username', 'label': 'SUJET', 'field': 'username', 'align': 'left'},
                {'name': 'status', 'label': 'STATUT', 'field': 'status', 'align': 'center'},
                {'name': 'confidence', 'label': 'CONFIANCE', 'field': 'confidence', 'align': 'center'},
                {'name': 'anomalie', 'label': 'ANOMALIE', 'field': 'anomalie', 'align': 'center'},
            ]
            table = ui.table(columns=columns, rows=rows, row_key='timestamp').classes('w-full bg-transparent text-white')

            async def refresh():
                table.rows = await self.get_alerts()
            
            # Rafraîchissement automatique toutes les 2 secondes
            ui.timer(2.0, refresh)

    async def export_pdf(self):
        """Déclenche la génération et le téléchargement du PDF."""
        logs = await self.get_alerts()
        if not logs:
            ui.notify("Aucun log à exporter.", type='warning')
            return
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_path = tmp.name
        
        try:
            generate_report(logs, tmp_path)
            ui.notify("Rapport PDF généré avec succès.", type='positive')
            # NiceGUI download
            ui.download(tmp_path, filename=f"biogait_audit_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf")
        except Exception as e:
            ui.notify(f"Erreur export : {str(e)}", type='negative')

def alerts_page():
    @ui.page('/alerts')
    async def page():
        p = AlertsPage()
        await p.content()
