"""
Setup application and run it's main loop.

Functions:

    main() -> None

"""

import logging
import os
import sys

import PyQt6.QtCore as QtCore
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

import speed_typing_game.config as config
from speed_typing_game.utils import (create_connection, get_color_palette,
                                     get_color_palette_names,
                                     get_supported_locale, set_stylesheet,
                                     setup_logging)
from speed_typing_game.views import MainWindow


def main() -> None:
    setup_logging("console", config.LOGGING_LEVEL)
    logger = logging.getLogger(__name__)
    app = QApplication(sys.argv)
    if not create_connection(config.DB, config.CON_NAME):
        sys.exit(1)

    translator = QtCore.QTranslator()
    # system_locale = QtCore.QLocale.system().name()
    locale = get_supported_locale()[0]
    # locale = "pl_PL"
    if translator.load(locale + ".qm", config.RESOURCES_DIR + "/translate/"):
        app.installTranslator(translator)
        logger.debug(f"Set locale: {locale}")
    else:
        logger.debug(f"Set locale: {config.DEFAULT_LOCALE}")

    # theme =  detect_dark_theme_os()
    theme = "dark"
    palette_name = get_color_palette_names(theme)[0]
    palette = get_color_palette(theme, palette_name)
    set_stylesheet(app, theme, palette_name)
    icon = QIcon(
        os.path.join(
            config.RESOURCES_DIR, "styles", theme, palette_name, "icon.png"
        )
    )

    window = MainWindow(palette, icon)
    window.show()
    sys.exit(app.exec())
