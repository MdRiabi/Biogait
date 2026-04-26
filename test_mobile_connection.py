import asyncio
import websockets
import json
import logging
from datetime import datetime

# Configuration du Logging
# Ce fichier sera créé dans le même dossier que ce script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Ceci force l'affichage dans la console
    ]
)

# --- CONFIGURATION ---
# IMPORTANT: Vérifiez que l'IP et le PORT correspondent exactement à votre serveur
# Si votre serveur est en local sur le port 8000 (Backend FastAPI)
SERVER_IP = "127.0.0.1" 
SERVER_PORT = 8000 
URI = f"ws://{SERVER_IP}:{SERVER_PORT}/api/v1/recognition/ws/mobile"

async def test_connection():
    logging.info(f"--- DÉBUT DU TEST DE CONNEXION ---")
    logging.info(f"Cible : {URI}")
    
    try:
        logging.info("Tentative de connexion WebSocket...")
        # timeout=5 pour ne pas attendre indéfiniment si le port est fermé
        async with websockets.connect(URI) as websocket:

            logging.info("✅ CONNEXION RÉUSSIE ! Le serveur a accepté la requête.")
            
            # 1. Test d'envoi d'action 'start'
            logging.info("Envoi de l'action 'start'...")
            payload_start = {
                "camera_id": "test_mobile_debug",
                "action": "start"
            }
            await websocket.send(json.dumps(payload_start))
            logging.info(f"Message envoyé : {payload_start}")
            
            # 2. Écoute de la réponse (timeout 2 secondes)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logging.info(f"📨 RÉPONSE DU SERVEUR REÇUE : {response}")
                data = json.loads(response)
                if data.get("status") == "recording_started":
                    logging.info("✅ Le serveur a bien compris l'action 'start'.")
            except asyncio.TimeoutError:
                logging.warning("⚠️ Aucune réponse du serveur après 2 secondes (Timeout).")

            # 3. Simulation d'envoi d'image (fausse image base64 pour tester le canal)
            logging.info("Envoi d'une image de test...")
            fake_image_b64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCgAB//2Q=="
            payload_img = {
                "camera_id": "test_mobile_debug",
                "image": fake_image_b64
            }
            await websocket.send(json.dumps(payload_img))
            logging.info("Image de test envoyée.")

            # 4. Écoute éventuelle (optionnel)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                logging.info(f"Réponse après image : {response}")
            except asyncio.TimeoutError:
                logging.info("Pas de réponse immédiate après l'image (Normal).")

            logging.info("--- TEST TERMINÉ AVEC SUCCÈS ---")

    except ConnectionRefusedError:
        logging.error("❌ ERREUR : CONNEXION REFUSÉE.")
        logging.error("Le serveur est actif, mais il refuse la connexion sur ce port.")
        logging.error("Vérifiez : 1. Le pare-feu Windows. 2. Que le serveur écoute bien sur ce port (0.0.0.0).")
    except OSError as e:
        logging.error(f"❌ ERREUR RÉSEAU : {e}")
        logging.error("L'adresse IP est injoignable ou le port est fermé.")
    except websockets.exceptions.InvalidStatus as e:
        logging.error(f"❌ ERREUR HTTP STATUS : {e}")
        logging.error("Le serveur a répondu, mais avec une erreur (ex: 404 Not Found).")
        logging.error("Vérifiez que l'URL est correcte : /api/v1/recognition/ws/mobile")
    except Exception as e:
        logging.error(f"❌ ERREUR INATTENDUE : {e}")

if __name__ == "__main__":
    # Lancer le test
    asyncio.run(test_connection())
