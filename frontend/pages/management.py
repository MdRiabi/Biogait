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
from datetime import datetime
import time
import asyncio
import cv2
from pathlib import Path

class ManagementPage:
    def __init__(self):
        self.user_table = None
        self.enrolled_video_paths = [] 
        self.status_label = None 
        self.debug_log = None # Console de diagnostic UI

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
                    "is_approved": u.is_approved,
                    "status": "APPROVED" if u.is_approved else "PENDING",
                    "created_at": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "N/A"
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
        self.enrolled_video_paths = []
        with ui.dialog() as dialog, cyber_card().classes('w-96'):
            ui.label('ENRÔLEMENT BIOMÉTRIQUE').classes('text-lg font-bold mb-4 text-primary')
            name = ui.input('Nom de l\'utilisateur').classes('w-full')
            
            with ui.row().classes('items-center mb-2'):
                ui.icon('folder_zip', color='primary')
                self.status_label = ui.label('Aucune vidéo prête').classes('text-xs italic text-muted')

            ui.upload(label='Uploader Vidéos .mp4', 
                      on_upload=lambda e: self.on_video_upload(e), 
                      on_rejected=lambda e: self.log_debug(f"REJETÉ: {e}"),
                      multiple=True, auto_upload=True).classes('w-full mt-2')
            
            # --- CONSOLE DE DEBUG (Invisible par défaut, mais utile ici) ---
            ui.label('CONSOLE DE DIAGNOSTIC').classes('text-[10px] mt-4 text-warning font-bold')
            self.debug_log = ui.log().classes('w-full h-32 text-[10px] bg-black text-white p-2 border border-warning')
            self.log_debug("Prêt pour diagnostic. Veuillez uploader une vidéo...")

            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('ANNULER', on_click=dialog.close).props('flat')
                ui.button('LANCER L\'ANALYSE', on_click=lambda: self.process_enroll(name.value, dialog)).classes('bg-primary text-black')
        dialog.open()

    def log_debug(self, msg):
        """Ajoute un message à la console de debug."""
        if self.debug_log:
            self.debug_log.push(f"[{time.strftime('%H:%M:%S')}] {msg}")
        print(f"[UI-DEBUG] {msg}")

    async def on_video_upload(self, e):
        """Callback universel asynchrone avec traçage profond."""
        self.log_debug("--- DÉBUT UPLOAD ---")
        try:
            # Inspection de l'objet e
            attrs = [a for a in dir(e) if not a.startswith('__')]
            self.log_debug(f"Attributs détectés sur l'événement: {attrs}")
            
            # Récupération sécurisée du nom
            filename = getattr(e, 'name', None) or getattr(e, 'filename', None)
            if not filename:
                # Sur votre version, le nom est probablement dans e.file.filename ou e.file.name
                filename = getattr(e.file, 'filename', None) or getattr(e.file, 'name', None) or f"video_{int(time.time())}.mp4"
            
            self.log_debug(f"Nom de fichier retenu: {filename}")
            
            # Lecture du buffer (Double sécurité asynchrone)
            self.log_debug("Tentative de lecture profonde...")
            raw_data = e.file.read()
            if asyncio.iscoroutine(raw_data):
                content = await raw_data
            else:
                content = raw_data
                
            self.log_debug(f"Résultat obtenu, type: {type(content)}")
            self.log_debug(f"Taille du contenu lu: {len(content)} octets")
            
            if len(content) == 0:
                self.log_debug("❌ ERREUR: Le fichier lu est vide (0 octets).")
                return

            save_dir = os.path.join("data", "uploads")
            if not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
                
            file_path = os.path.abspath(os.path.join(save_dir, filename))
            with open(file_path, "wb") as f:
                f.write(content)
            
            if file_path not in self.enrolled_video_paths:
                self.enrolled_video_paths.append(file_path)
            
            self.log_debug(f"✅ Succès: Ecriture sur {file_path}")
            
            if self.status_label:
                self.status_label.set_text(f"✅ {len(self.enrolled_video_paths)} fichier(s) validé(s)")
                self.status_label.style('color: #00FF00; font-weight: bold;')
            
            ui.notify(f'Fichier {filename} prêt.', type='positive')
        except Exception as ex:
            self.log_debug(f"❌ CRASH UPLOAD: {str(ex)}")
            ui.notify(f"Erreur technique : {str(ex)}", type='negative')

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
        print(f"[DEBUG] Tentative d'enrôlement pour '{username}'. Fichiers sur disque: {len(self.enrolled_video_paths)}")
        if not username:
            ui.notify("Veuillez saisir un nom d'utilisateur !", type='warning')
            return
        if len(self.enrolled_video_paths) < 3:
            ui.notify("Veuillez uploader au moins 3 vidéos !", type='warning')
            return
            
        ui.notify(f"Démarrage de l'analyse multi-vidéo pour {username}...", type='info')
        
        try:
            # 1. Préparation des données pour le pipeline d'enrôlement
            from app.core.ia.realtime_processor import realtime_manager
            
            video_paths = []
            frame_shapes = []
            
            for p in self.enrolled_video_paths:
                # Capture des dimensions de chaque vidéo
                cap = cv2.VideoCapture(p)
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                
                video_paths.append(Path(p))
                frame_shapes.append((h, w))
            
            # 2. Appel au moteur d'enrôlement robuste (Multi-séquences)
            # On exécute dans un thread pour ne pas geler l'UI
            res = await asyncio.to_thread(realtime_manager.pipeline.enroll_user, username, video_paths, frame_shapes)
            
            if "error" in res:
                ui.notify(f"Échec Enrôlement : {res['error']}", type='negative')
                return

            profile_vector = res.get("profile_vector")

            # 3. Sauvegarde en Base de Données
            async with SessionLocal() as db:
                result = await db.execute(select(User).where(User.username == username))
                user = result.scalar_one_or_none()
                
                if user:
                    user.gait_template = profile_vector.astype('float32').tobytes()
                    user.is_enrolled = True
                    await db.commit()
                    ui.notify(f"PROFIL BLINDÉ : {username} identifié avec succès !", type='positive')
                else:
                    ui.notify("Utilisateur inexistant dans la DB.", type='negative')
            
            # Nettoyage
            for p in self.enrolled_video_paths:
                if os.path.exists(p):
                    os.remove(p)
            self.enrolled_video_paths = []
            
            await self.refresh_table()
            
            # Synchronisation immédiate
            await realtime_manager.pipeline.synchronize_with_db()
            ui.notify("Moteur IA synchronisé. Sécurité active.", type='info')
            dialog.close()
            
        except Exception as e:
            ui.notify(f"Erreur IA : {str(e)}", type='negative')

def management_page():
    @ui.page('/users')
    async def page():
        p = ManagementPage()
        await p.content()
