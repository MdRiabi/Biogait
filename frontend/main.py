from nicegui import ui
from frontend.auth import login_register_pages
from frontend.pages.monitoring import monitoring_page
from frontend.pages.statistics import statistics_page
from frontend.pages.management import management_page
from frontend.pages.alerts import alerts_page
from frontend.pages.mobile_cam import mobile_cam_page

def init_frontend():
    """Initialise l'ensemble de l'interface BioGait."""
    # Enregistrement des pages
    login_register_pages()
    monitoring_page()      # URL: /
    statistics_page()      # URL: /stats
    management_page()      # URL: /users
    alerts_page()          # URL: /alerts
    mobile_cam_page()      # URL: /mobile-cam
    
    print("Interface BioGait initialisee.")

if __name__ in {"__main__", "__mp_main__"}:
    from nicegui import app
    from app.api.v1.recognition import router as recognition_router
    from app.api.v1.enrollment import router as enrollment_router
    from app.api.v1.auth import router as auth_router
    
    # Enregistrement des APIs Backend dans l'application NiceGUI
    app.include_router(recognition_router, prefix="/api/v1")
    app.include_router(enrollment_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")

    # Initialisation de l'interface (enregistrement des pages)
    init_frontend()
    
    # Configuration de l'application
    ui.run(
        title='BioGait Admin Dashboard',
        port=8088,
        host='0.0.0.0',
        reload=True,  # Rechargement automatique en développement
        dark=True,    # Mode sombre par défaut
        storage_secret='biogait_secret_key_change_in_production'
    )
