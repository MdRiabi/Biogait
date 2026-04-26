# --- Demarrage de BioGait Admin Dashboard ---

Write-Host "--- Démarrage de BioGait Admin Dashboard ---"
Write-Host "Astuce : PostgreSQL/Redis Docker -> depuis la racine : docker compose -f docker/docker-compose.yml up -d"

# 1. Recuperation automatique de l'adresse IP locale
# On cherche une adresse IPv4 qui n'est pas 127.0.0.1
$ipAddress = "127.0.0.1"
$networkAdapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -ne "127.0.0.1" -and $_.InterfaceAlias -notlike "*Loopback*" }

if ($networkAdapters) {
    # On prend la première adresse IP valide trouvée (souvent Wi-Fi ou Ethernet)
    $ipAddress = $networkAdapters[0].IPAddress
}
else {
    Write-Host "Aucune adresse IP valide trouvée. Veuillez vérifier votre connexion réseau."
}

# Ajout du dossier backend au PYTHONPATH
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptPath "backend"
$env:PYTHONPATH = "$env:PYTHONPATH;$backendPath"

Write-Host "Lancement du serveur BioGait..."
Write-Host " -> Accès local : http://127.0.0.1:8088"
Write-Host " -> Accès mobile : http://$ipAddress:8088 (via QR Code)"

# 2. Lancement de l'application (Python)
# Assurez-vous que le port 8088 est bien utilisé dans votre main.py
if (Test-Path ".\.venv\Scripts\python.exe") {
    Write-Host "Utilisation de l'environnement virtuel local..."
    .\.venv\Scripts\python.exe frontend/main.py
} else {
    Write-Host "Environnement virtuel introuvable. Tentative avec python global..."
    python frontend/main.py
}
