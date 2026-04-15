import cv2
import numpy as np

class VideoAnonymizer:
    """Classe chargée de l'anonymisation des flux vidéos en temps réel."""

    def __init__(self):
        import tempfile
        import os
        import shutil
        import cv2

        self.cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
        
        # OpenCV C++ crashes on paths with accents ('é'). We copy it to a safe temp dir.
        temp_dir = tempfile.gettempdir()
        safe_path = os.path.join(temp_dir, 'haarcascade_frontalface_default_temp.xml')
        
        if not os.path.exists(safe_path):
            # Copie via le module Python qui lui supporte les accents
            shutil.copy2(self.cascade_path, safe_path)
            
        self.face_cascade = cv2.CascadeClassifier(safe_path)

    def blur_faces(self, frame: np.ndarray) -> np.ndarray:
        """
        Détecte et floute les visages sur la frame pour s'assurer qu'aucune
        biométrie faciale ne puisse être extraite ou stockée (RGPD).
        """
        # Conversion en N&B pour accélerer la détection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Détection des visages
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        for (x, y, w, h) in faces:
            # Récupère la ROI (Region of Interest)
            face_roi = frame[y:y+h, x:x+w]
            
            # Applique un flou gaussien massif
            face_roi = cv2.GaussianBlur(face_roi, (99, 99), 30)
            
            # Repositionne le ROI flouté
            frame[y:y+h, x:x+w] = face_roi

        return frame
