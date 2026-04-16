from nicegui import ui
from frontend.theme import THEME, cyber_card
from frontend.components.sidebar import sidebar
from frontend.auth import check_auth
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from sqlalchemy.future import select

from app.core.ia.video_processor import VideoProcessor
import tempfile
import os

class ManagementPage:
    def __init__(self):
        self.user_table = None
        self.uploaded_files = [] # Liste pour stocker temporairement les vidéos

    async def get_users(self):
        """Récupère la liste des utilisateurs de la DB."""
        async with SessionLocal() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()
            return [
                {
                    "id": u.id,
                    "username": u.username,
                    "role": u.role,
                    "is_enrolled": "✅" if u.is_enrolled else "❌",
                    "id": u.id,
                    "is_approved": u.is_approved,
                    "status": "APPROVED" if u.is_approved else "PENDING",
                    "created_at": u.created_at.strftime("%Y-%m-%d %H:%M")
                }
                for u in users
            ]

    async def refresh_table(self):
        """Rafraîchit les données de la table."""
        if self.user_table:
            self.user_table.rows = await self.get_users()

    async def content(self):
        check_auth()
        sidebar()
        
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('GESTION DES UTILISATEURS').classes('text-2xl font-bold text-primary')
            ui.button('NOUVEAU SUJET', icon='add', on_click=lambda: self.enrollment_dialog()).classes('bg-primary text-black')

        with cyber_card().classes('w-full'):
            rows = await self.get_users()
            columns = [
                {'name': 'username', 'label': 'Utilisateur', 'field': 'username', 'required': True, 'align': 'left'},
                {'name': 'role', 'label': 'Rôle', 'field': 'role', 'align': 'left'},
                {'name': 'status', 'label': 'Statut', 'field': 'status', 'align': 'left'},
                {'name': 'is_enrolled', 'label': 'Enrôlé (IA)', 'field': 'is_enrolled', 'align': 'center'},
                {'name': 'created_at', 'label': 'Créé le', 'field': 'created_at', 'align': 'left'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'right'},
            ]
            self.user_table = ui.table(columns=columns, rows=rows, row_key='username').classes('w-full bg-transparent text-white')
            self.user_table.add_slot('body-cell-status', '''
                <q-td :props="props">
                    <q-badge :color="props.value === 'APPROVED' ? 'positive' : 'warning'">
                        {{ props.value }}
                    </q-badge>
                </q-td>
            ''')
            self.user_table.add_slot('body-cell-actions', f'''
                <q-td :props="props" class="text-right">
                    <q-btn v-if="!props.row.is_approved" flat round icon="check_circle" color="positive" @click="() => $parent.$emit('approve', props.row.id)">
                        <q-tooltip>Approuver l'utilisateur</q-tooltip>
                    </q-btn>
                    <q-btn flat round icon="delete" color="negative" @click="() => $parent.$emit('delete', props.row.id)" />
                </q-td>
            ''')
            self.user_table.on('approve', lambda msg: self.approve_user(msg.args))
            self.user_table.on('delete', lambda msg: self.delete_user(msg.args))

    def enrollment_dialog(self):
        """Ouvre une popup pour l'enrôlement."""
        self.uploaded_files = []
        with ui.dialog() as dialog, cyber_card().classes('w-96'):
            ui.label('ENRÔLEMENT BIOMÉTRIQUE').classes('text-lg font-bold mb-4 text-primary')
            name = ui.input('Nom de l\'utilisateur').classes('w-full')
            ui.label('Vidéos de démarche (min 1)').classes('text-xs text-muted mt-2')
            
            def handle_upload(e):
                self.uploaded_files.append(e.content.read())
                ui.notify(f'Vidéo {e.name} chargée ({len(self.uploaded_files)} au total)')

            ui.upload(label='Uploader Vidéos .mp4', on_upload=handle_upload, multiple=True).classes('w-full mt-2')
            
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('ANNULER', on_click=dialog.close).props('flat')
                ui.button('LANCER L\'ANALYSE', on_click=lambda: self.process_enroll(name.value, dialog)).classes('bg-primary text-black')
        dialog.open()

    async def approve_user(self, user_id):
        """Approuve un utilisateur en attente."""
        async with SessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.is_approved = True
                await db.commit()
                ui.notify(f"Utilisateur {user.username} approuvé !")
                await self.refresh_table()

    async def delete_user(self, user_id):
        """Supprime un utilisateur."""
        async with SessionLocal() as db:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                await db.delete(user)
                await db.commit()
                ui.notify("Utilisateur supprimé.")
                await self.refresh_table()

    async def process_enroll(self, username, dialog):
        if not username or not self.uploaded_files:
            ui.notify("Nom et vidéos requis !", type='warning')
            return
            
        ui.notify(f"Démarrage de l'analyse IA pour {username}...", type='info')
        
        try:
            # 1. Traitement de la première vidéo (pour la démo)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(self.uploaded_files[0])
                tmp_path = tmp.name
            
            processor = VideoProcessor()
            vector = processor.process_video_file(tmp_path)
            
            # 2. Mise à jour de l'utilisateur (ou création)
            async with SessionLocal() as db:
                result = await db.execute(select(User).where(User.username == username))
                user = result.scalar_one_or_none()
                
                if user:
                    user.gait_template = vector.astype('float32').tobytes()
                    user.is_enrolled = True
                    await db.commit()
                    ui.notify(f"Profil biométrique de {username} mis à jour !", type='positive')
                else:
                    ui.notify("Utilisateur inexistant. Créez le d'abord ou inscrivez-vous.", type='negative')
            
            os.remove(tmp_path)
            await self.refresh_table()
            dialog.close()
            
        except Exception as e:
            ui.notify(f"Erreur IA : {str(e)}", type='negative')

def management_page():
    @ui.page('/users')
    async def page():
        p = ManagementPage()
        await p.content()
