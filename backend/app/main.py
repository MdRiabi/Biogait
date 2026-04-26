from nicegui import ui
from frontend.auth import login_register_pages
from frontend.pages.monitoring import monitoring_page
from frontend.pages.statistics import statistics_page
from frontend.pages.management import management_page
from frontend.pages.alerts import alerts_page
from frontend.pages.mobile_cam import mobile_cam_page

# On appelle directement les fonctions d'enregistrement ici.
# Cela s'exécutera une seule fois au démarrage du script.
login_register_pages()
monitoring_page()      # Ceci enregistre la route '/'
statistics_page()      # URL: /stats
management_page()      # URL: /users
alerts_page()          # URL: /alerts
mobile_cam_page()      # URL: /mobile-cam

print("Interface BioGait initialisee.")

# Lancement de l'application
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='BioGait Admin Dashboard',
        port=8088,
        host='0.0.0.0',
        reload=True,
        dark=True,
        storage_secret='biogait_secret_key_change_in_production',
    )
