import sys
from datetime import datetime as dt
import logging

import PyQt6.QtCore as QtCore
from PyQt6.QtWidgets import QApplication

import speed_typing_game.config as config
from speed_typing_game.views import MainWindow
from speed_typing_game.utils import setup_logging, set_stylesheet, detect_dark_theme_os, get_color_palette


def main():
    setup_logging("console", config.LOGGING_LEVEL)
    app = QApplication(sys.argv)

    translator = QtCore.QTranslator()
    # system_locale = QtCore.QLocale.system().name()
    locale = "pl_PL"
    if translator.load(locale + ".qm", config.RESOURCES_DIR + "/translate/"):
        app.installTranslator(translator)

    # theme =  detect_dark_theme_os()
    theme = 'dark'
    set_stylesheet(app, config.COLOR_PALETTE, theme)
    palette = get_color_palette(config.COLOR_PALETTE, theme)

    window = MainWindow(palette)
    window.show()
    sys.exit(app.exec())
