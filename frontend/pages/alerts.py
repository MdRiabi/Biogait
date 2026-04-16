from nicegui import ui
from frontend.theme import THEME, cyber_card
from frontend.components.sidebar import sidebar
from frontend.auth import check_auth
from app.db.session import SessionLocal
from app.models.audit import AuditLog
from sqlalchemy.future import select
from sqlalchemy import desc
from app.core.ia.reporting import generate_report
import os
import tempfile
from nicegui import app

class AlertsPage:
    async def get_alerts(self):
        """Récupère les logs d'audit depuis la base de données."""
        async with SessionLocal() as db:
            result = await db.execute(select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(100))
            logs = result.scalars().all()
            return [
                {
                    "timestamp": l.timestamp.strftime("%H:%M:%S"),
                    "action": l.action,
                    "resource": l.resource,
                    "status": l.status_code,
                    "details": l.details
                }
                for l in logs
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
                {'name': 'timestamp', 'label': 'Heure', 'field': 'timestamp', 'align': 'left'},
                {'name': 'action', 'label': 'Action', 'field': 'action', 'align': 'left'},
                {'name': 'resource', 'label': 'Route', 'field': 'resource'},
                {'name': 'status', 'label': 'Code', 'field': 'status', 'align': 'center'},
                {'name': 'details', 'label': 'Détails', 'field': 'details', 'align': 'left'},
            ]
            ui.table(columns=columns, rows=rows, row_key='timestamp').classes('w-full bg-transparent text-white')

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
