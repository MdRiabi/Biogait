from nicegui import ui
from frontend.theme import apply_theme
from frontend.auth import login_register_pages
from frontend.pages.monitoring import monitoring_page
from frontend.pages.statistics import statistics_page
from frontend.pages.management import management_page
from frontend.pages.alerts import alerts_page

def init_frontend():
    """Initialise l'ensemble de l'interface BioGait."""
    # Appliquer le thème global (CSS/Tailwind)
    apply_theme()
    
    # Enregistrement des pages
    login_register_pages()
    monitoring_page()      # URL: /
    statistics_page()      # URL: /stats
    management_page()      # URL: /users
    alerts_page()          # URL: /alerts
    
    print("Interface BioGait initialisee.")
