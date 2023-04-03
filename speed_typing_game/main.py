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
    # locale = get_supported_locale()[0]
    QtCore.QCoreApplication.setApplicationName(config.PROJECT_NAME)
    QtCore.QCoreApplication.setOrganizationName("BoiarTech")
    QtCore.QCoreApplication.setOrganizationDomain("boiartech.com")
    settings = QtCore.QSettings()
    if settings.contains("styles/theme"):
        theme = settings.value("styles/theme")
        logger.debug(f"Retrieved theme from settings: {theme}")
    else:
        theme = "dark"
        settings.setValue("styles/theme", theme)
    if settings.contains("localization/locale"):
        locale = settings.value("localization/locale")
        logger.debug(f"Retrieved locale from settings: {locale}")
    else:
        locale = "pl_PL"
        settings.setValue("localization/locale", locale)
    if translator.load(locale + ".qm", config.RESOURCES_DIR + "/translate/"):
        app.installTranslator(translator)
        logger.debug(f"Set locale: {locale}")
    else:
        logger.debug(f"Set locale: {config.DEFAULT_LOCALE}")

    palette_name = get_color_palette_names(theme)[0]
 
    set_stylesheet(app, theme, palette_name)
    icon = QIcon(
        os.path.join(
            config.RESOURCES_DIR, "styles", theme, palette_name, "icon.png"
        )
    )
    # from speed_typing_game import models
    # w = models.Wordset.from_file(r"speed_typing_game\resources\words\easy_polish_word_base.txt")
    window = MainWindow(icon)
    window.show()
    sys.exit(app.exec())
