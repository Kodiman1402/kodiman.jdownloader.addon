import xbmcplugin
import xbmcgui
import xbmcaddon
import sys
import urllib.parse
import myjdapi

ADDON = xbmcaddon.Addon()
EMAIL = ADDON.getSetting("email")
PASSWORD = ADDON.getSetting("password")

def connect_to_jd():
    jd = myjdapi.Myjdapi()
    jd.set_app_key("KodiAddon")
    jd.connect(EMAIL, PASSWORD)
    jd.update_devices()
    devices = jd.list_devices()
    if not devices:
        raise Exception("Kein jDownloader-Gerät gefunden.")
    return jd.get_device(devices[0]["name"])

def add_download():
    link = xbmcgui.Dialog().input("Download-Link eingeben", type=xbmcgui.INPUT_ALPHANUM)
    if not link:
        return
    try:
        device = connect_to_jd()
        device.linkgrabber.add_links([{
            "autostart": True,
            "packageName": "Kodi-Download",
            "links": link,
            "overwritePackagizerRules": True
        }])
        xbmcgui.Dialog().ok("Erfolg", "Download-Link wurde an jDownloader gesendet.")
    except Exception as e:
        xbmcgui.Dialog().ok("Fehler", str(e))

def show_status():
    try:
        device = connect_to_jd()
        downloads = device.downloads.query_links()
        if not downloads:
            xbmcgui.Dialog().ok("Status", "Keine aktiven Downloads gefunden.")
            return

        handle = int(sys.argv[1])
        for dl in downloads:
            name = dl.get("name", "Unbenannt")
            status = dl.get("status", "Unbekannt")
            uuid = dl.get("uuid")
            loaded = dl.get("bytesLoaded", 0)
            total = dl.get("bytesTotal", 0)
            progress = int(min(loaded / total, 1.0) * 100) if total > 0 else 0
            label = f"{name} - {progress}% - {status}"
            li = xbmcgui.ListItem(label)
            li.addContextMenuItems([
                ("Download stoppen", f"RunPlugin({sys.argv[0]}?action=stop&uuid={uuid})"),
                ("Download löschen", f"RunPlugin({sys.argv[0]}?action=delete&uuid={uuid})")
            ])
            xbmcplugin.addDirectoryItem(handle, sys.argv[0]+"?action=nop", li, False)

        xbmcplugin.endOfDirectory(handle)

    except Exception as e:
        xbmcgui.Dialog().ok("Fehler", str(e))

def stop_download(uuid):
    try:
        device = connect_to_jd()
        device.downloads.set_enabled(False, [uuid], [])
        xbmcgui.Dialog().ok("Aktion", "Download wurde gestoppt.")
    except Exception as e:
        xbmcgui.Dialog().ok("Fehler", str(e))

def delete_download(uuid):
    try:
        device = connect_to_jd()
        device.downloads.remove_links([uuid], [])
        xbmcgui.Dialog().ok("Aktion", "Download wurde gelöscht.")
    except Exception as e:
        xbmcgui.Dialog().ok("Fehler", str(e))

def main():
    handle = int(sys.argv[1])
    args = urllib.parse.parse_qs(sys.argv[2][1:])
    action = args.get("action", [None])[0]

    if action == "add":
        add_download()
    elif action == "status":
        show_status()
    elif action == "stop":
        stop_download(args.get("uuid", [""])[0])
    elif action == "delete":
        delete_download(args.get("uuid", [""])[0])
    else:
        xbmcplugin.setPluginCategory(handle, "jDownloader")
        xbmcplugin.setContent(handle, "files")

        xbmcplugin.addDirectoryItem(handle, url=sys.argv[0]+"?action=add", listitem=xbmcgui.ListItem("Neuen Download hinzufügen"), isFolder=False)
        xbmcplugin.addDirectoryItem(handle, url=sys.argv[0]+"?action=status", listitem=xbmcgui.ListItem("Download-Status anzeigen"), isFolder=True)

        xbmcplugin.endOfDirectory(handle)

if __name__ == '__main__':
    main()
