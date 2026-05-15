"""Kodi jDownloader Addon entry point."""

import sys
import urllib.parse

import myjdapi
import xbmcaddon  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error
import xbmcplugin  # pylint: disable=import-error

ADDON = xbmcaddon.Addon()


def _get_credentials():
    """Return the configured login credentials.

    Raises a RuntimeError with a translated message if the credentials are
    missing so the caller can display the error in a dialog.
    """

    email = ADDON.getSetting("email")
    password = ADDON.getSetting("password")
    if not email or not password:
        raise RuntimeError(
            "Bitte E-Mail-Adresse und Passwort in den Addon-Einstellungen hinterlegen."
        )
    return email, password


def _build_url(base_url, **query):
    """Create a plugin URL including the provided query arguments."""

    if not query:
        return base_url
    return base_url + "?" + urllib.parse.urlencode(query)


def _get_uuid(args):
    """Return a validated UUID argument or show an error dialog."""

    uuid = args.get("uuid", [""])[0].strip()
    if not uuid:
        xbmcgui.Dialog().ok("Fehler", "Download-ID fehlt oder ist ungültig.")
        return None
    return uuid


def connect_to_jd():
    """Establish a connection to the first available jDownloader device."""

    jd = myjdapi.Myjdapi()
    jd.set_app_key("KodiAddon")
    email, password = _get_credentials()
    jd.connect(email, password)
    jd.update_devices()
    devices = jd.list_devices()
    if not devices:
        raise RuntimeError("Kein jDownloader-Gerät gefunden.")
    return jd.get_device(devices[0]["name"])


def add_download():
    """Prompt for a link and send it to jDownloader."""

    link = xbmcgui.Dialog().input(
        "Download-Link eingeben",
        type=xbmcgui.INPUT_ALPHANUM,
    )
    if not link:
        return

    try:  # pylint: disable=broad-except
        device = connect_to_jd()
        device.linkgrabber.add_links(
            [
                {
                    "autostart": True,
                    "packageName": "Kodi-Download",
                    "links": link,
                    "overwritePackagizerRules": True,
                }
            ]
        )
        xbmcgui.Dialog().ok("Erfolg", "Download-Link wurde an jDownloader gesendet.")
    except Exception as err:  # pylint: disable=broad-except
        xbmcgui.Dialog().ok("Fehler", str(err))


def show_status(base_url, handle):
    """Display the list of active downloads."""

    if handle < 0:
        xbmcgui.Dialog().ok("Fehler", "Ungültiger Plugin-Aufruf.")
        return

    try:  # pylint: disable=broad-except
        device = connect_to_jd()
        downloads = device.downloads.query_links()

        if not downloads:
            xbmcgui.Dialog().ok("Status", "Keine aktiven Downloads gefunden.")
            return

        for dl in downloads:
            name = dl.get("name", "Unbenannt")
            status = dl.get("status", "Unbekannt")
            uuid = dl.get("uuid")
            loaded = dl.get("bytesLoaded", 0)
            total = dl.get("bytesTotal", 0)
            try:
                progress = int(min(float(loaded) / float(total), 1.0) * 100)
            except (TypeError, ZeroDivisionError):
                progress = 0

            label = f"{name} - {progress}% - {status}"
            li = xbmcgui.ListItem(label)
            if uuid:
                stop_url = _build_url(base_url, action="stop", uuid=uuid)
                delete_url = _build_url(base_url, action="delete", uuid=uuid)
                li.addContextMenuItems(
                    [
                        ("Download stoppen", f"RunPlugin({stop_url})"),
                        ("Download löschen", f"RunPlugin({delete_url})"),
                    ]
                )
            xbmcplugin.addDirectoryItem(handle, _build_url(base_url, action="nop"), li, False)

        xbmcplugin.endOfDirectory(handle)
    except Exception as err:  # pylint: disable=broad-except
        xbmcgui.Dialog().ok("Fehler", str(err))


def _parse_request():
    """Return base URL, handle and parsed query parameters for the call."""

    base_url = sys.argv[0] if sys.argv else ""
    try:
        handle = int(sys.argv[1])
    except (IndexError, ValueError, TypeError):
        handle = -1

    raw_query = sys.argv[2] if len(sys.argv) > 2 else ""
    query_string = raw_query[1:] if raw_query.startswith("?") else raw_query
    args = urllib.parse.parse_qs(query_string)
    return base_url, handle, args


def stop_download(uuid):
    """Stop a download by UUID."""

    try:  # pylint: disable=broad-except
        device = connect_to_jd()
        device.downloads.set_enabled(False, [uuid], [])
        xbmcgui.Dialog().ok("Aktion", "Download wurde gestoppt.")
    except Exception as err:  # pylint: disable=broad-except
        xbmcgui.Dialog().ok("Fehler", str(err))


def delete_download(uuid):
    """Remove a download by UUID."""

    try:  # pylint: disable=broad-except
        device = connect_to_jd()
        device.downloads.remove_links([uuid], [])
        xbmcgui.Dialog().ok("Aktion", "Download wurde gelöscht.")
    except Exception as err:  # pylint: disable=broad-except
        xbmcgui.Dialog().ok("Fehler", str(err))


def main():
    """Addon entry point."""

    base_url, handle, args = _parse_request()
    action = args.get("action", [None])[0]

    if action == "add":
        add_download()
    elif action == "status":
        show_status(base_url, handle)
    elif action == "stop":
        uuid = _get_uuid(args)
        if uuid:
            stop_download(uuid)
    elif action == "delete":
        uuid = _get_uuid(args)
        if uuid:
            delete_download(uuid)
    elif action == "nop":
        return
    else:
        if handle < 0:
            xbmcgui.Dialog().ok("Fehler", "Ungültiger Plugin-Aufruf.")
            return

        xbmcplugin.setPluginCategory(handle, "jDownloader")
        xbmcplugin.setContent(handle, "files")

        xbmcplugin.addDirectoryItem(
            handle,
            url=_build_url(base_url, action="add"),
            listitem=xbmcgui.ListItem("Neuen Download hinzufügen"),
            isFolder=False,
        )
        xbmcplugin.addDirectoryItem(
            handle,
            url=_build_url(base_url, action="status"),
            listitem=xbmcgui.ListItem("Download-Status anzeigen"),
            isFolder=True,
        )

        xbmcplugin.endOfDirectory(handle)


if __name__ == "__main__":
    main()
