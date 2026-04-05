"""Kodi jDownloader Addon entry point - Update mit dynamischer Pfadsuche für myjdapi."""
import sys
import os
import urllib.parse
import xbmcaddon
import xbmcgui
import xbmcplugin

# --- Dynamische Pfadsuche für myjdapi ---
# 1. Standardpfad (für lokale Installation)
ADDON_DIR = xbmcaddon.Addon().getAddonInfo('path')
LIB_DIR_STANDARD = os.path.join(ADDON_DIR, 'lib')

# 2. Alternative Pfade (falls addon_data oder userdata verwendet wird)
#   - Kodi 18+: lib/ in userdata/addon_data/plugin.program.kodiman.jdownloader/
#   - Kodi 19+: lib/ in addon_root/lib/
ADDON_DATA_DIR = os.path.join(xbmcaddon.Addon().getAddonInfo('profile'), 'lib')
USERDATA_LIB_DIR = os.path.join(xbmcaddon.Addon().getAddonInfo('profile'), 'addons', 'plugin.program.kodiman.jdownloader', 'lib')

# Alle möglichen Pfade prüfen
LIB_PATHS = [
    LIB_DIR_STANDARD,
    ADDON_DATA_DIR,
    USERDATA_LIB_DIR,
]

# Ersten gültigen Pfad wählen
LIB_DIR = None
for path in LIB_PATHS:
    if os.path.exists(path) and os.path.isdir(path):
        LIB_DIR = path
        break

# sys.path für myjdapi aktualisieren
if LIB_DIR:
    sys.path.append(LIB_DIR)
else:
    # Falls kein Pfad gefunden wird, Standard-Ordner erstellen (für Nutzer-Hinweis)
    os.makedirs(LIB_DIR_STANDARD, exist_ok=True)
    LIB_DIR = LIB_DIR_STANDARD

# --- myjdapi-Import mit dynamischer Pfadsuche ---
try:
    import myjdapi
except ImportError:
    # Nutzerfreundlicher Dialog mit Anleitung
    error_message = (
        "Das Modul 'myjdapi' wurde nicht gefunden.\n\n"
        "Installiere es mit einem der folgenden Befehle:\n\n"
        "Option 1 (empfohlen für Kodi 19+):\n"
        "pip install myjdapi --target=" + os.path.join(LIB_DIR_STANDARD, 'myjdapi') + "\n\n"
        "Option 2 (für Kodi 18 und älter):\n"
        "pip install myjdapi --target=" + ADDON_DATA_DIR + "\n\n"
        "Danach Kodi neu starten."
    )
    
    xbmcgui.Dialog().ok("Fehler: Abhängigkeit fehlt", error_message)
    sys.exit(1)

ADDON = xbmcaddon.Addon()

def _get_credentials():
    """Liest die Zugangsdaten aus den Einstellungen."""
    email = ADDON.getSetting("email")
    password = ADDON.getSetting("password")
    device_name_filter = ADDON.getSetting("device_name")
    
    if not email or not password:
        raise RuntimeError(
            "Bitte E-Mail-Adresse und Passwort in den Addon-Einstellungen hinterlegen."
        )
    return email, password, device_name_filter

# ... [Rest des Codes bleibt unverändert: connect_to_jd(), add_download(), show_status(), stop_download(), delete_download(), router()] ...

if __name__ == '__main__':
    router()