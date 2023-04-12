"""
Setup application and run it's main loop.

Functions:

    main() -> None

"""
import logging
import os
import sys

import PyQt6.QtCore as QtCore
from PyQt6.QtGui import QIcon, QGuiApplication
from PyQt6.QtWidgets import QApplication

from speed_typing_game import config
from speed_typing_game.utils import (create_connection, get_color_palette,
                                     get_color_palette_names,
                                     get_supported_locale, set_stylesheet,
                                     setup_logging)
from speed_typing_game.views import MainWindow


def configure_app(app: QApplication) -> None:
    setup_logging("console", config.LOGGING_LEVEL)
    logger = logging.getLogger(__name__)
    if not create_connection(config.DB, config.CON_NAME):
        sys.exit(1)

    translator = QtCore.QTranslator()
    # system_locale = QtCore.QLocale.system().name()
    # locale = get_supported_locale()[0]
    QtCore.QCoreApplication.setApplicationName(config.PROJECT_NAME)
    QtCore.QCoreApplication.setOrganizationName("AGHTech")
    settings = QtCore.QSettings()
    if settings.contains("styles/theme"):
        theme = settings.value("styles/theme")
        logger.debug(f"Retrieved theme from settings: {theme}")
    else:
        theme = "dark"
        settings.setValue("styles/theme", theme)

    if settings.contains("styles/palette"):
        palette_name = settings.value("styles/palette")
        logger.debug(f"Retrieved palette from settings: {palette_name}")
    else:
        palette_name = get_color_palette_names([theme])[0]
        settings.setValue("styles/palette", palette_name)

    if settings.contains("localization/locale"):
        locale = settings.value("localization/locale")
        logger.debug(f"Retrieved locale from settings: {locale}")
    else:
        locale = QtCore.QLocale("pl_PL")
        settings.setValue("localization/locale", locale)
    if locale.name() != config.DEFAULT_LOCALE and translator.load(locale.name() + ".qm", config.RESOURCES_DIR + "/translate/"):
        app.installTranslator(translator)
        logger.debug(f"Set locale: {locale}")
    else:
        logger.debug(f"Set locale: {config.DEFAULT_LOCALE}")
 
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

def restart_app() -> None:
    app = QGuiApplication.instance()
    QGuiApplication.setQuitOnLastWindowClosed(False)
    QApplication.closeAllWindows()
    configure_app(app)
    QGuiApplication.setQuitOnLastWindowClosed(True)

def main() -> None:
    app = QApplication(sys.argv)
    configure_app(app)

    sys.exit(app.exec())
