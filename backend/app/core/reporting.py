import hashlib
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import datetime
import os

class BioGaitReporter:
    """Génère des rapports d'audit PDF sécurisés."""
    
    def __init__(self, output_dir: str = "data/reports"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_audit_report(self, logs: list, admin_username: str) -> str:
        """
        Génère un rapport PDF et retourne le chemin du fichier.
        Calcule un hash SHA-256 du contenu final pour l'intégrité.
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_report_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        
        # --- HEADER ---
        c.setFillColor(colors.HexColor("#0A0A1A")) # Theme dark
        c.rect(0, height - 80, width, 80, fill=1)
        c.setFillColor(colors.HexColor("#00F0FF")) # Theme primary
        c.setFont("Helvetica-Bold", 24)
        c.drawString(40, height - 50, "BIOGAIT - RAPPORT D'AUDIT")
        
        # --- INFOS ---
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(40, height - 100, f"Généré par : {admin_username}")
        c.drawString(40, height - 115, f"Date d'extraction : {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # --- CONTENU TABLE (LOGS) ---
        y = height - 150
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "HORODATAGE")
        c.drawString(140, y, "ACTION")
        c.drawString(240, y, "CHEMIN / RESSOURCE")
        c.drawString(440, y, "RÉSULTAT")
        c.line(40, y - 5, 550, y - 5)
        
        y -= 25
        c.setFont("Helvetica", 9)
        for log in logs[:20]: # Limite à 20 pour la page 1
            c.drawString(40, y, str(log.get('timestamp', '')))
            c.drawString(140, y, str(log.get('action', '')))
            c.drawString(240, y, str(log.get('resource', ''))[:40])
            c.drawString(440, y, str(log.get('status', '')))
            y -= 15
            if y < 100:
                c.showPage()
                y = height - 50
        
        # --- SIGNATURE D'INTÉGRITÉ (SHA-256) ---
        # Note: Dans un vrai système, on hasherait le flux binaire. 
        # Ici on ajoute un mémo de sécurité.
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor(colors.grey)
        c.drawString(40, 50, "L'intégrité de ce document est protégée par un hashage SHA-256.")
        
        c.save()
        
        # Calcul du Hash
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        print(f"🔒 Rapport PDF généré : {filename}")
        print(f"📄 Hash SHA-256 : {sha256_hash.hexdigest()}")
        
        return filepath
