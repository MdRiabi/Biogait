import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import os

def generate_report(logs, output_path):
    """Génère un rapport PDF d'audit avec signature SHA-256."""
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Titre
    title_style = ParagraphStyle(
        'CyberTitle',
        parent=styles['Heading1'],
        textColor=colors.HexColor("#00F0FF"),
        alignment=1,
        fontSize=24,
        spaceAfter=20
    )
    elements.append(Paragraph("BIOGAIT - RAPPORT D'AUDIT SÉCURITÉ", title_style))
    elements.append(Paragraph(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Tableau de données
    data = [["HEURE", "CAMÉRA", "SUJET", "STATUT", "CONFIANCE"]]
    for log in logs:
        data.append([
            log.get("timestamp") or "N/A",
            log.get("camera_id") or "Mobile",
            log.get("username") or "Inconnu",
            log.get("status") or "DÉTECTÉ",
            log.get("confidence") or "0%"
        ])

    table = Table(data, colWidths=[60, 80, 100, 80, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#111827")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#00F0FF")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 40))

    # Signature de sécurité
    log_string = "".join([str(l) for l in logs])
    report_hash = hashlib.sha256(log_string.encode()).hexdigest()
    
    elements.append(Paragraph("<b>CERTIFICATION D'INTÉGRITÉ :</b>", styles['Normal']))
    elements.append(Paragraph(f"<font color='#9D00FF' size='8'>SHA-256: {report_hash}</font>", styles['Normal']))
    elements.append(Paragraph("Ce document est généré par le système BioGait. Toute modification du contenu invalidera la signature numérique ci-dessus.", styles['Italic']))

    doc.build(elements)
    return report_hash
