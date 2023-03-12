import json
import os
import sys

import PyQt6.QtCore as QtCore
from PyQt6.QtCore import QCoreApplication, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

PROJECT_NAME = "SimplyType"
PROJECT_URL = "https://github.com/mboiar/speed-typing-game"
PROJECT_VERSION = "v0.1-dev"
RESOURCES_DIR = "speed_typing_game/resources"
SUPPORTED_LOCALE = ["pl_PL", "en_US"]
ICON_FILENAME = "icon-vscode.png"


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_window()

    def init_window(self):
        self.resize(900, 500)
        self.setWindowTitle(PROJECT_NAME)
        self.setWindowIcon(QIcon(RESOURCES_DIR + "/images/" + ICON_FILENAME))

        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        title = QLabel('<font color="#007acc">Simply</font>Type')
        title.setProperty("class", "heading")
        self.words_input = QLineEdit()
        self.words_input.setProperty("class", "super-text")
        self.words_input.textEdited.connect(self.validate_character)
        button_restart = QPushButton(
            QCoreApplication.translate("QPushButton", "Restart")
        )
        button_restart.clicked.connect(self.reset_game)
        # TODO: why cursor can not be imported?
        # button_restart.setCursor(QCursor(QtCore.Qt.PointingHandCursor))

        sidebarLayout = QVBoxLayout()
        button_settings = QPushButton(
            QCoreApplication.translate("QPushButton", "Settings")
        )
        button_about = QPushButton(QCoreApplication.translate("QPushButton", "About"))
        button_stats = QPushButton(QCoreApplication.translate("QPushButton", "Stats"))
        button_stats.setProperty("class", "highlighted")

        menuLayout = QVBoxLayout()
        button_menu1 = QPushButton(
            QCoreApplication.translate("QPushButton", "Language")
        )
        button_menu2 = QPushButton(QCoreApplication.translate("QPushButton", "Mode"))
        button_menu3 = QPushButton(
            QCoreApplication.translate("QPushButton", "Duration")
        )
        menuLayout.addWidget(button_menu1)
        menuLayout.addWidget(button_menu2)
        menuLayout.addWidget(button_menu3)

        # TODO: sort this styling mess out
        link_github = QLabel(
            f'<a href="{PROJECT_URL}" style="text-decoration:none;color:#fff">\
            {PROJECT_VERSION}</a>'
        )
        link_github.linkActivated.connect(self.link)
        link_github.setObjectName("link_github")
        link_github.setProperty("class", "faded")

        words_to_type_label = QLabel(
            "words will appear here you can see that this is a multi-line text"
        )
        words_to_type_label.setWordWrap(True)
        words_to_type_label.setProperty("class", "words_to_type")

        mainLayout.addWidget(title)
        mainLayout.addWidget(self.words_input)
        mainLayout.addWidget(words_to_type_label)
        mainLayout.addWidget(button_restart)

        sidebarLayout = QVBoxLayout()
        sidebarLayout.addWidget(button_settings)
        sidebarLayout.addWidget(button_about)
        sidebarLayout.addWidget(button_stats)
        sidebarLayout.addWidget(link_github)

        secondaryLayout = QHBoxLayout()
        secondaryLayout.addLayout(menuLayout)
        secondaryLayout.addStretch()
        secondaryLayout.addLayout(sidebarLayout)
        mainLayout.addLayout(secondaryLayout)

    def link(self, linkStr):
        QDesktopServices.openUrl(QUrl(linkStr))

    def get_words_input(self):
        print(self.words_input.text())

    def reset_game(self):
        self.words_input.clear()
        # TODO: reset game

    def validate_character(self):
        pass


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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    translator = QtCore.QTranslator()
    system_locale = QtCore.QLocale.system().name()
    locale = "pl_PL"
    if translator.load(locale + ".qm", RESOURCES_DIR + "/translate/"):
        app.installTranslator(translator)
    window = MainWindow()

    theme_name = "vscode"
    load_stylesheet(app, theme_name)

    window.show()
    sys.exit(app.exec())
