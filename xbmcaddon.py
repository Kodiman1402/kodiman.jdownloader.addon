class Addon:
    def __init__(self):
        self._settings = {
            "email": "",
            "password": ""
        }

    def getSetting(self, key):
        return self._settings.get(key, "")

    def setSetting(self, key, value):
        self._settings[key] = value
