from nicegui import ui
from frontend.theme import THEME, cyber_card
from frontend.components.sidebar import sidebar
from frontend.auth import check_auth
from app.db.session import SessionLocal
from app.models.audit import AuditLog
from sqlalchemy.future import select
from sqlalchemy import desc

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
            ui.button('EXPORTER ANALYSE (PDF)', icon='print', color='warning').classes('ml-auto')

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

def alerts_page():
    @ui.page('/alerts')
    async def page():
        p = AlertsPage()
        await p.content()
