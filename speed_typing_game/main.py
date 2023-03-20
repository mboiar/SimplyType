import sys
import os

import PyQt6.QtCore as QtCore
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

import speed_typing_game.config as config
from speed_typing_game.utils import (
    get_color_palette_names,
    set_stylesheet,
    setup_logging,
    get_color_palette
)
from speed_typing_game.views import MainWindow


def main():
    setup_logging("console", config.LOGGING_LEVEL)
    app = QApplication(sys.argv)

    translator = QtCore.QTranslator()
    # system_locale = QtCore.QLocale.system().name()
    locale = "pl_PL"
    if translator.load(locale + ".qm", config.RESOURCES_DIR + "/translate/"):
        app.installTranslator(translator)

    # theme =  detect_dark_theme_os()
    theme = "dark"
    palette_name = get_color_palette_names(theme)[0]
    palette = get_color_palette(palette_name, theme)
    set_stylesheet(app, palette_name, theme)
    icon = QIcon(os.path.join(config.RESOURCES_DIR, "styles", theme, palette_name, "icon.png"))

    window = MainWindow(palette, icon)
    window.show()
    sys.exit(app.exec())
