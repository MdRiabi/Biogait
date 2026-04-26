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

def mobile_qr_component():
    """Crée l'interface QR Code pour le Dashboard."""
    #ip = get_local_ip()
     
    ip = get_local_ip() 
    port = 8088  # Port du serveur NiceGUI
    url = f"http://{ip}:{port}/mobile-cam"
    
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
        ui.label(ip).classes('text-[8px] text-primary mt-1 opacity-50')
