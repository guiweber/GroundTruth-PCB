from PyQt6.QtCore import QOperatingSystemVersion
from PyQt6.QtGui import QFont

def get_emoji_font():

    if QOperatingSystemVersion.currentType() == QOperatingSystemVersion.OSType.Windows:
        return QFont("Segoe UI Emoji")
    elif QOperatingSystemVersion.currentType() == QOperatingSystemVersion.OSType.MacOS:
        return QFont("Apple Color Emoji")
    else:
        return QFont("Noto Color Emoji")
