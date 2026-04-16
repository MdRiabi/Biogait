from nicegui import ui
from frontend.theme import THEME
from frontend.auth import logout

def sidebar():
    """Crée la barre latérale de navigation."""
    with ui.left_drawer(value=True).classes('w-64') as drawer:
        with ui.column().classes('w-full items-center p-4'):
            ui.icon('radar', size='56px').style(f'color: {THEME["primary"]}')
            ui.label('BIOGAIT').classes('text-2xl font-bold tracking-widest mt-2')
            ui.separator().classes('my-4').style(f'background-color: {THEME["primary"]}22')
            
        with ui.column().classes('w-full mt-4'):
            ui.button('Supervision', icon='videocam', on_click=lambda: ui.navigate.to('/')).classes('w-full text-left').props('flat')
            ui.button('Statistiques', icon='insights', on_click=lambda: ui.navigate.to('/stats')).classes('w-full text-left').props('flat')
            ui.button('Utilisateurs', icon='people', on_click=lambda: ui.navigate.to('/users')).classes('w-full text-left').props('flat')
            ui.button('Alertes', icon='notifications', on_click=lambda: ui.navigate.to('/alerts')).classes('w-full text-left').props('flat')
        
        with ui.column().classes('absolute-bottom w-full p-4'):
            ui.button('Déconnexion', icon='logout', on_click=logout).classes('w-full').style(f'color: {THEME["error"]}')
