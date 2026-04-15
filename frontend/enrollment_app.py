from nicegui import ui
import httpx

API_BASE = "http://localhost:8000/api/v1"

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
    ui.run(host='127.0.0.1', port=8080, reload=False)