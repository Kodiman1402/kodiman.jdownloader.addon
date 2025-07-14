import sys

def addDirectoryItem(handle, url, listitem, isFolder):
    print(f"addDirectoryItem: handle={handle}, url={url}, label={listitem.label}, isFolder={isFolder}")

def endOfDirectory(handle):
    print(f"endOfDirectory: handle={handle}")

def setPluginCategory(handle, category):
    print(f"setPluginCategory: handle={handle}, category={category}")

def setContent(handle, content):
    print(f"setContent: handle={handle}, content={content}")
