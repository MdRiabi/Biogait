from typing import Optional
from nicegui import app, ui
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password, verify_password
from sqlalchemy.future import select

# Redirection si non authentifié
login_path = '/login'
register_path = '/register'

def is_authenticated() -> bool:
    return app.storage.user.get('authenticated', False)

def check_auth():
    """Vérifie si l'utilisateur est admin ou supervisor."""
    if not is_authenticated():
        ui.navigate.to(login_path)
    role = app.storage.user.get('role')
    if role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        ui.notify('Accès refusé : Droits insuffisants.', type='negative')
        ui.navigate.to(login_path)

async def login(username_input: ui.input, password_input: ui.input) -> None:
    """Valide les identifiants contre la base de données."""
    username = username_input.value
    password = password_input.value
    
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if user and verify_password(password, user.hashed_password):
            # Vérification de l'approbation Admin (Sauf pour le rôle ADMIN qui est auto-approuvé pour éviter le blocage)
            if not user.is_approved and user.role != UserRole.ADMIN:
                ui.notify('Compte en attente de validation par un administrateur.', type='warning')
                return

            if user.role in [UserRole.ADMIN, UserRole.SUPERVISOR]:
                app.storage.user.update({
                    'username': username,
                    'authenticated': True,
                    'role': user.role
                })
                ui.navigate.to('/')
            else:
                ui.notify('Erreur : Votre rôle ne permet pas l\'accès au Dashboard.', type='warning')
        else:
            ui.notify('Identifiants invalides.', type='negative')

def logout() -> None:
    app.storage.user.update({'authenticated': False})
    ui.navigate.to(login_path)

async def register_user(username_input, password_input, confirm_input) -> None:
    """Crée un nouvel utilisateur en attente d'approbation."""
    username = username_input.value
    password = password_input.value
    confirm = confirm_input.value

    if not username or not password:
        ui.notify('Tous les champs sont requis.', type='negative')
        return
    if password != confirm:
        ui.notify('Les mots de passe ne correspondent pas.', type='negative')
        return

    async with SessionLocal() as db:
        # Vérifier si existe
        res = await db.execute(select(User).where(User.username == username))
        if res.scalar_one_or_none():
            ui.notify('Ce nom d\'utilisateur est déjà pris.', type='negative')
            return

        new_user = User(
            username=username,
            hashed_password=hash_password(password),
            role=UserRole.SUPERVISOR,
            is_approved=False
        )
        db.add(new_user)
        try:
            await db.commit()
            ui.notify('Inscription réussie ! En attente de validation Admin.', type='positive')
            ui.navigate.to(login_path)
        except Exception as e:
            await db.rollback()
            ui.notify(f'Erreur : {str(e)}', type='negative')

def login_register_pages():
    @ui.page(login_path)
    def login_screen():
        with ui.column().classes('absolute-center items-center p-8 card-cyber'):
            ui.label('BIOGAIT ADMIN').classes('text-3xl font-bold mb-4').style('color: #00F0FF')
            username = ui.input('Nom d\'utilisateur').classes('w-64')
            password = ui.input('Mot de passe', password=True).classes('w-64').on('keydown.enter', lambda: login(username, password))
            ui.button('Connexion', on_click=lambda: login(username, password)).classes('w-full mt-4').style('background-color: #00F0FF; color: black')
            
            with ui.row().classes('mt-4 text-sm'):
                ui.label('Pas de compte ?')
                ui.link('S\'inscrire ici', register_path).style('color: #00F0FF')

    @ui.page(register_path)
    def register_screen():
        with ui.column().classes('absolute-center items-center p-8 card-cyber'):
            ui.label('BIOGAIT - INSCRIPTION').classes('text-3xl font-bold mb-4').style('color: #9D00FF')
            ui.label('Nouveau compte Superviseur').classes('text-sm mb-4 italic text-muted')
            
            username = ui.input('Nom d\'utilisateur').classes('w-64')
            password = ui.input('Mot de passe', password=True).classes('w-64')
            confirm = ui.input('Confirmer le mot de passe', password=True).classes('w-64')
            
            ui.button('S\'inscrire', on_click=lambda: register_user(username, password, confirm)).classes('w-full mt-6').style('background-color: #00F0FF; color: black')
            ui.link('Retour à la connexion', login_path).classes('mt-4 text-xs')

