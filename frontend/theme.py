from nicegui import ui

# COULEURS DU THÈME CYBERPUNK
THEME = {
    'background': '#0A0A1A',
    'surface': '#111827',
    'primary': '#00F0FF',
    'secondary': '#9D00FF',
    'success': '#00FF88',
    'warning': '#FF5500',
    'error': '#FF0055',
    'skeleton': '#39FF14',
    'text': '#E0E0FF',
    'textMuted': '#6B7280'
}

def apply_theme():
    """Applique le thème personnalisé au Dashboard via Tailwind et CSS injection."""
    
    # 1. Configuration de Tailwind (NiceGUI supporte config_tailwind)
    # Note: On injecte surtout via CSS car NiceGUI n'expose pas directement toute la config tailwind
    ui.add_head_html(f'''
    <style>
        :root {{
            --bg-color: {THEME['background']};
            --surface-color: {THEME['surface']};
            --primary-color: {THEME['primary']};
            --secondary-color: {THEME['secondary']};
            --text-color: {THEME['text']};
        }}
        body {{
            background-color: {THEME['background']} !important;
            color: {THEME['text']} !important;
        }}
        .nicegui-content {{
            background-color: {THEME['background']};
        }}
        .q-drawer {{
            background-color: {THEME['surface']} !important;
            border-right: 1px solid {THEME['primary']}44;
        }}
        .q-header {{
            background-color: {THEME['surface']} !important;
            border-bottom: 1px solid {THEME['primary']}44;
        }}
        .card-cyber {{
            background-color: {THEME['surface']};
            border: 1px solid {THEME['primary']}22;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 240, 255, 0.05);
            transition: all 0.3s ease;
        }}
        .card-cyber:hover {{
            border-color: {THEME['primary']};
            box-shadow: 0 4px 20px rgba(0, 240, 255, 0.15);
        }}
        .text-primary {{ color: {THEME['primary']} !important; }}
        .text-secondary {{ color: {THEME['secondary']} !important; }}
        .text-success {{ color: {THEME['success']} !important; }}
        .text-warning {{ color: {THEME['warning']} !important; }}
        .text-error {{ color: {THEME['error']} !important; }}
        
        /* Personnalisation Quasar (NiceGUI repose sur Quasar) */
        .q-btn {{
            text-transform: none;
            font-weight: 600;
        }}
    </style>
    ''')

def cyber_card():
    """Crée un conteneur style card cyberpunk."""
    return ui.card().classes('card-cyber p-4')
