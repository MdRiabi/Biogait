# Fichier d'état centralisé pour BioGait

# Mapping camera_id -> base64_image
# Utilisé pour partager les frames entre les WebSockets de capture et le polling du Dashboard
latest_frames = {}
