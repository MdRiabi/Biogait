from nicegui import ui
import httpx
import socket  # Import nécessaire pour récupérer l'IP

# Fonction pour récupérer l'IP locale
def get_local_ip():
    """Récupère l'adresse IP locale de la machine serveur."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # N'a pas besoin de se connecter réellement
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# Utilisation de l'IP dynamique pour l'API
API_BASE = f"http://{get_local_ip()}:8088/api/v1"

def show_status(msg: str, type: str = 'info'):
    ui.notify(msg, type=type, position='top')

def on_enroll(username: str, upload):
    if not username:
        show_status("Veuillez entrer un nom d'utilisateur", 'warning')
        return
    if not upload:
        show_status("Veuillez sélectionner une vidéo", 'warning')
        return

    try:
        with httpx.Client() as client:
            files = {'video_file': (upload.name, open(upload.name, 'rb'), 'video/mp4')}
            response = client.post(f"{API_BASE}/enrollment/register", files=files, params={'username': username})
            
            if response.status_code == 201:
                show_status(f"✅ Enrôlement de {username} réussi !", 'positive')
            else:
                show_status(f"❌ Erreur: {response.json().get('detail', 'Inconnue')}", 'negative')
    except Exception as e:
        show_status(f"❌ Erreur réseau: {str(e)}", 'negative')

@ui.page('/enrollment')
def enrollment_page():
    with ui.card().style('width: 400px; margin: auto'):
        ui.label('Module d\'Enrôlement Biométrique').style('font-size: 1.5rem; margin-bottom: 20px')
        
        username_input = ui.input(label='Nom d\'utilisateur (ex: USER_042)').props('filled')
        video_upload = ui.upload(label='Uploader Vidéo (mp4)', auto_upload=False).style('width: 100%')
        
        ui.button('ENRÔLER', on_click=lambda: on_enroll(username_input.value, video_upload.value)) \
            .props('unelevated color=primary').style('width: 100%; margin-top: 20px')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(host='0.0.0.0', port=8080, reload=False)
