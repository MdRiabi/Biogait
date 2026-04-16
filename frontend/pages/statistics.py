from nicegui import ui
from frontend.theme import THEME, cyber_card
from frontend.components.sidebar import sidebar
from frontend.auth import check_auth

class StatisticsPage:
    def content(self):
        check_auth()
        sidebar()
        
        ui.label('ANALYSE DE PERFORMANCE IA').classes('text-2xl font-bold mb-6 text-primary')
        
        with ui.row().classes('w-full items-stretch'):
            # --- GRAPH 1 : DISTRIBUTION DES SCORES ---
            with ui.column().classes('flex-grow'):
                with cyber_card():
                    ui.label('Distribution des Scores de Confiance').classes('font-bold mb-4')
                    self.create_chart_js_canvas('scoreDistributionChart')

            # --- GRAPH 2 : COURBE ROC (PRÉCISION) ---
            with ui.column().classes('flex-grow'):
                with cyber_card():
                    ui.label('Courbe ROC (FAR vs FRR)').classes('font-bold mb-4')
                    self.create_chart_js_canvas('rocCurveChart')

        # Injection du script Chart.js et initialisation
        ui.add_head_html('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>')
        ui.timer(0.5, self.init_charts, once=True)

    def create_chart_js_canvas(self, canvas_id: str):
        """Crée un élément canvas HTML pour Chart.js."""
        ui.html(f'<canvas id="{canvas_id}" style="width: 100%; height: 300px;"></canvas>')

    def init_charts(self):
        """Initialise les graphiques via JavaScript."""
        # Chart 1 : Score Distribution
        ui.run_javascript(f'''
            new Chart(document.getElementById('scoreDistributionChart'), {{
                type: 'bar',
                data: {{
                    labels: ['0-20', '20-40', '40-60', '60-80', '80-100'],
                    datasets: [{{
                        label: 'Nombre d\\'identifications',
                        data: [5, 12, 19, 45, 120],
                        backgroundColor: '{THEME['primary']}88',
                        borderColor: '{THEME['primary']}',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{ beginAtZero: true, grid: {{ color: '#ffffff11' }} }},
                        x: {{ grid: {{ color: '#ffffff11' }} }}
                    }},
                    plugins: {{ legend: {{ labels: {{ color: '{THEME['text']}' }} }} }}
                }}
            }});
        ''')
        
        # Chart 2 : ROC Curve
        ui.run_javascript(f'''
            new Chart(document.getElementById('rocCurveChart'), {{
                type: 'line',
                data: {{
                    labels: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1],
                    datasets: [{{
                        label: 'FAR / FRR',
                        data: [1, 0.8, 0.6, 0.45, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01, 0],
                        borderColor: '{THEME['secondary']}',
                        backgroundColor: '{THEME['secondary']}33',
                        fill: true,
                        tension: 0.4
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{ beginAtZero: true, grid: {{ color: '#ffffff11' }} }},
                        x: {{ grid: {{ color: '#ffffff11' }} }}
                    }},
                    plugins: {{ legend: {{ labels: {{ color: '{THEME['text']}' }} }} }}
                }}
            }});
        ''')

def statistics_page():
    @ui.page('/stats')
    def page():
        p = StatisticsPage()
        p.content()
