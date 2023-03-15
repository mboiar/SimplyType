import sys

import PyQt6.QtCore as QtCore
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QDesktopServices, QIcon, QCursor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from speed_typing_game import config

_translate = QtCore.QCoreApplication.translate


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.words = "words will appear here you can see that this\
        is a multi-line text"

        self.init_window()

    def init_window(self):
        self.resize(900, 500)
        self.setWindowTitle(config.PROJECT_NAME)
        self.setWindowIcon(
            QIcon(config.RESOURCES_DIR + "/images/" + config.ICON_FILENAME)
        )

        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.title = QLabel('<font color="#007acc">Simply</font>Type')
        self.title.setProperty("class", "heading")
        self.timer = QLabel("32")
        self.timer.setObjectName("timer")

        self.words_input = QLineEdit()
        self.words_input.textEdited.connect(self.validate_character)
        self.button_restart = QPushButton(
            #    _translate("QPushButton", "Restart")
        )
        self.button_restart.clicked.connect(self.reset_game)

        self.sidebarLayout = QVBoxLayout()
        self.button_settings = QPushButton()
        self.button_about = QPushButton()
        self.button_stats = QPushButton()
        self.button_stats.setProperty("class", "highlighted")
        self.button_exit = QPushButton()
        self.button_exit.clicked.connect(self.close)

        self.menuLayout = QVBoxLayout()
        self.button_menu1 = QPushButton()
        self.button_menu2 = QPushButton()
        self.button_menu3 = QPushButton()
        self.menuLayout.addWidget(self.button_menu1)
        self.menuLayout.addWidget(self.button_menu2)
        self.menuLayout.addWidget(self.button_menu3)

        # TODO: sort this styling mess out
        self.link_github = QLabel(
            f'<a href="{config.PROJECT_URL}" style="text-decoration:none;\
            color:#fff">{config.PROJECT_VERSION}</a>'
        )
        self.link_github.linkActivated.connect(self.open_hyperlink)
        self.link_github.setObjectName("link_github")
        self.link_github.setProperty("class", "faded")

        self.words_to_type_label = QLabel(self.get_words_subset())
        self.words_to_type_label.setWordWrap(True)
        self.words_to_type_label.setProperty("class", "words_to_type")

        for button in [
            self.button_about,
            self.button_menu1,
            self.button_menu2,
            self.button_menu3,
            self.button_restart,
            self.button_settings,
            self.button_stats,
            self.button_exit,
        ]:
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.mainLayout.addWidget(self.title)
        self.mainLayout.addWidget(self.timer)
        self.timer.hide()
        self.mainLayout.addWidget(self.words_input)
        self.mainLayout.addWidget(self.words_to_type_label)
        self.mainLayout.addWidget(self.button_restart)

        self.sidebarLayout = QVBoxLayout()
        self.sidebarLayout.addWidget(self.button_settings)
        self.sidebarLayout.addWidget(self.button_about)
        self.sidebarLayout.addWidget(self.button_stats)
        self.sidebarLayout.addWidget(self.button_exit)
        self.sidebarLayout.addWidget(self.link_github)

        self.secondaryLayout = QHBoxLayout()
        self.secondaryLayout.addLayout(self.menuLayout)
        self.secondaryLayout.addStretch()
        self.secondaryLayout.addLayout(self.sidebarLayout)
        self.mainLayout.addLayout(self.secondaryLayout)
        self.retranslate()

    def open_hyperlink(self, linkStr):
        QDesktopServices.openUrl(QUrl(linkStr))

    def get_user_input(self):
        return self.words_input.text()

    def reset_game(self):
        """Restart the game, re-generate words and reset cursor position"""
        self.words_input.clear()
        # TODO: reset game

    def validate_character(self):
        """Check if typed character is correct"""
        pass

    def get_words_subset(self):
        """Get a subset of words that will immediately appear on screen"""
        words = self.words
        return "".join(words)

    def retranslate(self):
        self.button_restart.setText(_translate("QPushButton", "Restart"))
        self.button_settings.setText(_translate("QPushButton", "Settings"))
        self.button_stats.setText(_translate("QPushButton", "Stats"))
        self.button_about.setText(_translate("QPushButton", "About"))
        self.button_menu1.setText(_translate("QPushButton", "Language"))
        self.button_menu2.setText(_translate("QPushButton", "Mode"))
        self.button_menu3.setText(_translate("QPushButton", "Duration"))
        self.button_exit.setText(_translate("QPushButton", "Exit"))

    def close(self):
        sys.exit()
