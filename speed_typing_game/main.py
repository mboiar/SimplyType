import json
import os
import sys
from datetime import datetime as dt
import logging

import PyQt6.QtCore as QtCore
from PyQt6.QtWidgets import QApplication

import speed_typing_game.config as config
from speed_typing_game.views import MainWindow


def load_stylesheet(app, theme_name):
    theme_path = os.path.join(config.RESOURCES_DIR, "styles", theme_name + ".json")
    template_path = config.RESOURCES_DIR + "/styles/template.css"
    with open(theme_path, "r") as theme_f, open(template_path, "r") as main_f:
        theme = json.load(theme_f)
        style_sheet = main_f.read()
        for color_var in theme["colors"].keys():
            style_sheet = style_sheet.replace(
                f"var({color_var})", '"' + theme["colors"][color_var] + '"'
            )
        app.setStyleSheet(style_sheet)

def setup_logging(log_destination, log_level):
    timestamp = dt.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(config.LOG_PATH, f"{timestamp}.log")
    handlers = []
    if log_destination in ["console", "both"]:
        handlers.append(logging.StreamHandler())
    if log_destination in ["file", "both"]:
        handlers.append(logging.FileHandler(filename=log_filename, mode="x"))

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=log_level,
        handlers=handlers,
    )

def main():

    setup_logging("console", config.LOGGING_LEVEL)
    app = QApplication(sys.argv)

    translator = QtCore.QTranslator()
    # system_locale = QtCore.QLocale.system().name()
    locale = "pl_PL"
    if translator.load(locale + ".qm", config.RESOURCES_DIR + "/translate/"):
        app.installTranslator(translator)
    window = MainWindow()

    theme_name = "vscode"
    load_stylesheet(app, theme_name)

    window.show()
    sys.exit(app.exec())
