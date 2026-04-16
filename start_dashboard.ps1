# BioGait - Lancement automatique du Dashboard
# Usage : Exécutez ce script depuis PowerShell à la racine du projet

Write-Host "--- Démarrage de BioGait Admin Dashboard ---" -ForegroundColor Cyan

# 1. Vérification du dossier backend
if (-Not (Test-Path "backend")) {
    Write-Host "ERREUR : Chemin 'backend' non trouvé. Veuillez lancer le script depuis la racine du projet." -ForegroundColor Red
    Pause
    exit
}

# 2. Préparation du chemin Python AVANT de changer de dossier
$PythonExe = (Join-Path (Get-Location) ".venv\Scripts\python.exe")

if (-Not (Test-Path $PythonExe)) {
    Write-Host "ERREUR : Environnement virtuel non trouvé dans .venv\" -ForegroundColor Red
    Pause
    exit
}

cd backend
Write-Host "Lancement du serveur BioGait..." -ForegroundColor Green
Write-Host " -> Accès local : http://127.0.0.1:8088" -ForegroundColor Cyan
Write-Host " -> Accès mobile : http://192.168.1.6:8088 (via QR Code)" -ForegroundColor Cyan
& $PythonExe -m uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
