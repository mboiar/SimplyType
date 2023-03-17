import json
import os
import sys

import PyQt6.QtCore as QtCore
from PyQt6.QtWidgets import QApplication

from speed_typing_game.config import RESOURCES_DIR
from speed_typing_game.views import MainWindow


def load_stylesheet(app, theme_name):
    theme_path = os.path.join(RESOURCES_DIR, "styles", theme_name + ".json")
    template_path = RESOURCES_DIR + "/styles/template.css"
    with open(theme_path, "r") as theme_f, open(template_path, "r") as main_f:
        theme = json.load(theme_f)
        style_sheet = main_f.read()
        for color_var in theme["colors"].keys():
            style_sheet = style_sheet.replace(
                f"var({color_var})", '"' + theme["colors"][color_var] + '"'
            )
        app.setStyleSheet(style_sheet)


def main():
    app = QApplication(sys.argv)

    translator = QtCore.QTranslator()
    # system_locale = QtCore.QLocale.system().name()
    locale = "pl_PL"
    if translator.load(locale + ".qm", RESOURCES_DIR + "/translate/"):
        app.installTranslator(translator)
    window = MainWindow()

    theme_name = "vscode"
    load_stylesheet(app, theme_name)

    window.show()
    sys.exit(app.exec())
