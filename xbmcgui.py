class Dialog:
    def input(self, message, type=None):
        try:
            return input(message + " ")
        except EOFError:
            return ""

    def ok(self, title, message):
        print(f"{title}: {message}")

class ListItem:
    def __init__(self, label):
        self.label = label
        self.context_items = []

    def addContextMenuItems(self, items):
        # store context menu items for debugging
        self.context_items.extend(items)
