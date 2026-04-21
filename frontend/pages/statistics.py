from nicegui import ui
from frontend.theme import THEME, cyber_card
from frontend.components.sidebar import sidebar
from frontend.auth import check_auth
from app.db.session import SessionLocal
from app.models.alert import DetectionAlert
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta

class StatisticsPage:
    def __init__(self):
        self.score_chart = None
        self.timeline_chart = None
        self.donut_chart = None

    async def get_stats_data(self):
        """Récupère les données réelles de la base de données."""
        async with SessionLocal() as db:
            # 1. Distribution de confiance
            # On compte par tranches de 20%
            confidence_data = [0] * 5
            result = await db.execute(select(DetectionAlert.confidence))
            scores = result.scalars().all()
            for s in scores:
                # On multiplie par 100 car les scores sont entre 0 et 1 dans la DB
                score_100 = s * 100 if s <= 1.0 else s
                idx = min(int(score_100 // 20), 4)
                confidence_data[idx] += 1

            # 2. Activité (Timeline 24h)
            # On groupe par heure
            timeline_data = []
            yesterday = datetime.now() - timedelta(days=1)
            result = await db.execute(
                select(func.strftime('%H', DetectionAlert.timestamp), func.count(DetectionAlert.id))
                .where(DetectionAlert.timestamp >= yesterday)
                .group_by(func.strftime('%H', DetectionAlert.timestamp))
            )
            timeline_rows = result.all()
            # Transformation en liste ordonnée
            hours = {f"{i:02d}h": 0 for i in range(24)}
            for hour_str, count in timeline_rows:
                hours[f"{hour_str}h"] = count
            
            return {
                "confidence": confidence_data,
                "timeline": list(hours.values()),
                "timeline_labels": list(hours.keys()),
                "total": len(scores)
            }

    async def content(self):
        check_auth()
        sidebar()
        
        data = await self.get_stats_data()

        ui.label('ANALYSE DE PERFORMANCE IA').classes('text-2xl font-bold mb-6 text-primary')
        
        # --- CARTES KPI ---
        with ui.row().classes('w-full mb-6'):
            with cyber_card().classes('flex-grow text-center'):
                ui.label('TOTAL DÉTECTIONS').classes('text-xs text-muted')
                ui.label(str(data['total'])).classes('text-3xl font-bold text-primary')
            
            with cyber_card().classes('flex-grow text-center'):
                ui.label('SYSTÈME').classes('text-xs text-muted')
                ui.label('OPÉRATIONNEL').classes('text-xl font-bold text-success')

        with ui.row().classes('w-full items-stretch'):
            # --- GRAPH 1 : DISTRIBUTION RÉELLE ---
            with ui.column().classes('w-full md:w-1/2'):
                with cyber_card().classes('h-full'):
                    ui.label('Distribution Réelle de Confiance').classes('font-bold mb-4')
                    self.score_chart = ui.highchart({
                        'title': False,
                        'chart': {'type': 'column', 'backgroundColor': 'transparent'},
                        'xAxis': {'categories': ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'], 'labels': {'style': {'color': '#fff'}}},
                        'yAxis': {'title': {'text': 'Alertes'}, 'gridLineColor': '#ffffff11', 'labels': {'style': {'color': '#fff'}}},
                        'series': [{'name': 'Identifications', 'data': data['confidence'], 'color': THEME['primary']}],
                        'legend': {'enabled': False}
                    }).classes('w-full h-64')

            # --- GRAPH 2 : TIMELINE DYNAMIQUE ---
            with ui.column().classes('w-full md:w-1/2'):
                with cyber_card().classes('h-full'):
                    ui.label('Volume d\'Activité (24h)').classes('font-bold mb-4')
                    self.timeline_chart = ui.highchart({
                        'title': False,
                        'chart': {'type': 'areaspline', 'backgroundColor': 'transparent'},
                        'xAxis': {'categories': data['timeline_labels'], 'labels': {'style': {'color': '#fff'}}},
                        'yAxis': {'title': {'text': 'Détections'}, 'gridLineColor': '#ffffff11', 'labels': {'style': {'color': '#fff'}}},
                        'series': [{'name': 'Activité', 'data': data['timeline'], 'color': THEME['secondary']}],
                        'legend': {'enabled': False}
                    }).classes('w-full h-64')

        # Rafraîchissement automatique
        ui.timer(30, self.refresh_stats)

    async def refresh_stats(self):
        """Met à jour les graphiques sans recharger la page."""
        data = await self.get_stats_data()
        self.score_chart.options['series'][0]['data'] = data['confidence']
        self.timeline_chart.options['series'][0]['data'] = data['timeline']
        self.score_chart.update()
        self.timeline_chart.update()

def statistics_page():
    @ui.page('/stats')
    async def page():
        p = StatisticsPage()
        await p.content()
