import segno
import socket
import io
from nicegui import ui

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

import httpx

def get_ngrok_url():
    """Tente de récupérer l'URL publique si ngrok est en cours d'exécution localement."""
    try:
        response = httpx.get("http://127.0.0.1:4040/api/tunnels", timeout=1.0)
        if response.status_code == 200:
            data = response.json()
            for tunnel in data.get("tunnels", []):
                if tunnel.get("proto") == "https":
                    return tunnel.get("public_url")
    except Exception:
        pass
    return None

def mobile_qr_component():
    """Crée l'interface QR Code pour le Dashboard."""
    ngrok_url = get_ngrok_url()
    
    if ngrok_url:
        url = f"{ngrok_url}/mobile-cam"
        display_text = "NGROK SÉCURISÉ (HTTPS)"
    else:
        ip = get_local_ip() 
        port = 8088  # Port du serveur NiceGUI
        url = f"http://{ip}:{port}/mobile-cam"
        display_text = f"{ip}:{port}"
    
    # Génération du QR Code
    qr = segno.make(url)
    out = io.BytesIO()
    qr.save(out, kind='png', scale=5, dark="#00F0FF", light="#0A0A1A")
    import base64
    content = base64.b64encode(out.getvalue()).decode()
    
    with ui.column().classes('items-center p-4 card-cyber'):
        ui.label('CAMÉRA NOMADE').classes('text-xs font-bold mb-2 text-primary')
        ui.image(f'data:image/png;base64,{content}').classes('w-32 h-32 rounded')
        ui.label('Scannez pour connecter').classes('text-[10px] text-muted mt-2 uppercase tracking-tighter')
        ui.label(display_text).classes('text-[8px] text-primary mt-1 opacity-70')
