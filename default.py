"""Kodi jDownloader Addon entry point."""
import sys
import os
import urllib.parse
import xbmcaddon
import xbmcgui
import xbmcplugin

# --- WICHTIG: Lokalen lib Ordner einbinden ---
# Damit Kodi das Modul 'myjdapi' findet, muss es im Ordner /lib liegen.
ADDON_DIR = xbmcaddon.Addon().getAddonInfo('path')
LIB_DIR = os.path.join(ADDON_DIR, 'lib')
sys.path.append(LIB_DIR)

# Versuch, myjdapi zu importieren. Wenn es fehlt, Fehler anzeigen.
try:
    import myjdapi
except ImportError:
    xbmcgui.Dialog().ok(
        "Fehler: Abhängigkeit fehlt",
        "Das Modul 'myjdapi' wurde nicht gefunden.\n"
        "Bitte sicherstellen, dass der Ordner 'lib/myjdapi' im Addon-Verzeichnis existiert."
    )
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

def _build_url(base_url, **query):
    """Erstellt eine Plugin-URL."""
    if not query:
        return base_url
    return base_url + "?" + urllib.parse.urlencode(query)

def connect_to_jd():
    """Verbindet mit MyJDownloader und sucht das richtige Gerät."""
    jd = myjdapi.Myjdapi()
    jd.set_app_key("KodiAddon")
    
    email, password, device_name_filter = _get_credentials()
    
    try:
        jd.connect(email, password)
    except Exception as e:
        raise RuntimeError(f"Login fehlgeschlagen: {str(e)}")

    jd.update_devices()
    devices = jd.list_devices()
    
    if not devices:
        raise RuntimeError("Keine jDownloader-Geräte im Account gefunden.")

    target_device = None

    # Wenn ein spezifischer Name in den Settings steht, suchen wir diesen
    if device_name_filter:
        for dev in devices:
            if dev.get("name") == device_name_filter:
                target_device = dev
                break
        if not target_device:
            raise RuntimeError(f"Gerät mit Namen '{device_name_filter}' nicht gefunden.")
    else:
        # Sonst nehmen wir das erste verfügbare
        target_device = devices[0]

    # Verbindung zum spezifischen Gerät herstellen
    return jd.get_device(target_device["name"])

def add_download():
    """Fragt nach Link und sendet an JD."""
    link = xbmcgui.Dialog().input(
        "Download-Link eingeben",
        type=xbmcgui.INPUT_ALPHANUM,
    )
    if not link:
        return
    
    # Dialog für Feedback öffnen
    pDialog = xbmcgui.DialogProgress()
    pDialog.create("Verbinde...", "Sende Link an jDownloader...")
    
    try:
        device = connect_to_jd()
        # priority: DEFAULT, autostart: True
        device.linkgrabber.add_links([
            {
                "autostart": True,
                "packageName": "Kodi-Download",
                "links": link,
                "overwritePackagizerRules": False, 
            }
        ])
        pDialog.close()
        xbmcgui.Dialog().notification("jDownloader", "Link hinzugefügt", xbmcgui.NOTIFICATION_INFO, 3000)
    except Exception as err:
        pDialog.close()
        xbmcgui.Dialog().ok("Fehler", str(err))

def show_status():
    """Zeigt aktive Downloads an."""
    handle = int(sys.argv[1])
    base_url = sys.argv[0]

    try:
        device = connect_to_jd()
        # Wir fragen downloads ab
        downloads = device.downloads.query_links()
        
        if not downloads:
            # Leere Liste anzeigen, damit man sieht, dass nichts läuft
            li = xbmcgui.ListItem("Keine aktiven Downloads")
            xbmcplugin.addDirectoryItem(handle, _build_url(base_url, action="nop"), li, False)
            xbmcplugin.endOfDirectory(handle)
            return

        for dl in downloads:
            name = dl.get("name", "Unbenannt")
            # Sicherstellen, dass Status ein String ist
            status = str(dl.get("status", "")) 
            uuid = dl.get("uuid")
            bytes_loaded = dl.get("bytesLoaded", 0)
            bytes_total = dl.get("bytesTotal", 0)
            
            # Berechnung absichern
            progress = 0
            if bytes_total and bytes_total > 0:
                try:
                    progress = int((float(bytes_loaded) / float(bytes_total)) * 100)
                except:
                    progress = 0
            
            # Label formatieren
            label = f"[{progress}%] {name}"
            if status:
                label += f" - {status}"

            li = xbmcgui.ListItem(label)
            
            # Info Labels für schönere Darstellung in Kodi Skins
            li.setInfo("video", {"title": name})
            
            if uuid:
                stop_url = _build_url(base_url, action="stop", uuid=uuid)
                delete_url = _build_url(base_url, action="delete", uuid=uuid)
                
                # Context Menu
                li.addContextMenuItems([
                    ("Download stoppen", f"RunPlugin({stop_url})"),
                    ("Download löschen", f"RunPlugin({delete_url})"),
                ])
            
            xbmcplugin.addDirectoryItem(
                handle,
                _build_url(base_url, action="nop"),
                li,
                False,
            )

        xbmcplugin.endOfDirectory(handle)

    except Exception as err:
        xbmcgui.Dialog().ok("Verbindungsfehler", str(err))
        xbmcplugin.endOfDirectory(handle)

def stop_download(uuid):
    """Stoppt einen Download."""
    if not uuid: return
    try:
        device = connect_to_jd()
        device.downloads.stop_downloads([uuid]) # Korrigierte Methode je nach API Version oft unterschiedlich, aber probieren wir Standard
        xbmcgui.Dialog().notification("jDownloader", "Download gestoppt", xbmcgui.NOTIFICATION_INFO, 3000)
        xbmcplugin.refreshContainer() # Liste aktualisieren
    except Exception as err:
        xbmcgui.Dialog().ok("Fehler", str(err))

def delete_download(uuid):
    """Löscht einen Download."""
    if not uuid: return
    
    if not xbmcgui.Dialog().yesno("Löschen", "Diesen Download wirklich löschen?"):
        return

    try:
        device = connect_to_jd()
        device.downloads.remove_links([uuid], [])
        xbmcgui.Dialog().notification("jDownloader", "Download gelöscht", xbmcgui.NOTIFICATION_INFO, 3000)
        xbmcplugin.refreshContainer()
    except Exception as err:
        xbmcgui.Dialog().ok("Fehler", str(err))

def router():
    """Haupt-Router Logik."""
    # Argumente parsen
    args = urllib.parse.parse_qs(sys.argv[2][1:])
    action = args.get("action", [None])[0]
    handle = int(sys.argv[1])

    if action == "add":
        add_download()
    elif action == "status":
        show_status()
    elif action == "stop":
        stop_download(args.get("uuid", [""])[0])
    elif action == "delete":
        delete_download(args.get("uuid", [""])[0])
    elif action == "nop":
        return
    else:
        # Hauptmenü
        xbmcplugin.setPluginCategory(handle, "jDownloader Control")
        xbmcplugin.setContent(handle, "files")

        # Item 1: Neuen Download
        li_add = xbmcgui.ListItem("Neuen Download hinzufügen")
        li_add.setArt({'icon': 'DefaultAddon.png'})
        xbmcplugin.addDirectoryItem(
            handle,
            url=_build_url(sys.argv[0], action="add"),
            listitem=li_add,
            isFolder=False,
        )

        # Item 2: Status
        li_stat = xbmcgui.ListItem("Aktive Downloads anzeigen")
        li_stat.setArt({'icon': 'DefaultAddonInfo.png'})
        xbmcplugin.addDirectoryItem(
            handle,
            url=_build_url(sys.argv[0], action="status"),
            listitem=li_stat,
            isFolder=True,
        )

        xbmcplugin.endOfDirectory(handle)

if __name__ == '__main__':
    router()main()
