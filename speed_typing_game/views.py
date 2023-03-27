import logging
import sys
import time

import PyQt6.QtCore as QtCore
from PyQt6.QtCore import QCoreApplication, Qt, QUrl
from PyQt6.QtGui import QCursor, QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from speed_typing_game import config

# translate = QtCore.QCoreApplication.translate
update_timer_interval = 200
game_duration = 20 * 1000
BACKSPACE_KEY = 16777219
DELETE_KEY = 16777223
X_KEY = 88
V_KEY = 86
TAKEBACK_KEYS = [BACKSPACE_KEY, DELETE_KEY]
CUT_KEYS = [X_KEY, V_KEY]
CTRL_MODIFIER = 2


class InputLabel(QLabel):
    def __init__(self, width=600):
        super().__init__()
        self.cursor_pos = (0, 0, 5, 10)  # TODO: use fontmetrics
        self.cursor = QtCore.QRect(*(self.cursor_pos))
        self.text = ""
        self.max_chars = 80 * 3  # TODO: set based on width
        self.setText(self.text[: self.max_chars])
        self.incorrect_chars = {}
        self.correct_chars = {}
        self.pos = 0

    def redraw(self, width):
        """Change displayed word count if width/font changed"""
        pass

    def newline(self):
        # TODO: hide prev. line, set cursor, show new text
        pass


class CustomLineEdit(QLineEdit):
    def __init__(self, parent, allow_takeback=False, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.allow_takeback = allow_takeback
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, event):
        key = event.key()
        modifier = event.nativeModifiers()
        window = self.parent()
        modifier_message = "with a modifier:" + modifier if modifier else ""
        self.logger.debug(
            f"Detected keyPressEvent: key {key} {modifier_message}"
        )
        is_cutpaste_event = modifier == CTRL_MODIFIER and key in CUT_KEYS
        if (not self.allow_takeback) and (
            key in TAKEBACK_KEYS or is_cutpaste_event
        ):
            self.logger.debug(
                "Skipped takeback event: takeback is not allowed"
            )
            return
        if not window.game_in_progress:
            window.start_game()
        super().keyPressEvent(event)


class MainWindow(QWidget):
    def __init__(self, palette_name, icon):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.words = "words will appear here you can see that this\
is a multi-line text"
        self.incorrect_chars = {}
        self.correct_chars = {}
        self.text = self.words
        self.pos = 0
        self.cur_char = self.words[0]
        self.typed_in = []
        self.game_in_progress = False
        self.timer = QtCore.QTimer()
        self.update_timer = QtCore.QTimer()
        self.palette = palette_name
        self.icon = icon
        self.init_window()

    def init_window(self):
        self.logger.debug("Initialized main window")
        self.resize(900, 500)
        self.setWindowTitle(config.PROJECT_NAME)
        self.setWindowIcon(self.icon)

        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        standout_color = self.palette["--standout-color"]
        self.title = QLabel(
            f"<font color='{standout_color}'>Simply</font>Type"
        )
        self.title.setProperty("class", "heading")
        self.timer_label = QLabel()
        sp_retain = self.timer_label.sizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        self.timer_label.setSizePolicy(sp_retain)
        self.timer_label.setObjectName("timer_label")
        self.timer_label.setProperty("class", "highlighted")

        self.input_label = InputLabel()
        self.words_input = CustomLineEdit(self)
        self.words_input.textEdited.connect(self.validate_character)
        self.button_reset = QPushButton()

        self.sidebarLayout = QVBoxLayout()
        self.button_settings = QPushButton()
        self.button_about = QPushButton()
        self.button_stats = QPushButton()
        self.button_stats.setProperty("class", "highlighted")
        self.button_exit = QPushButton()

        self.menuLayout = QVBoxLayout()
        self.button_menu1 = QPushButton()
        self.button_menu2 = QPushButton()
        self.button_menu3 = QPushButton()
        self.menuLayout.addWidget(self.button_menu1)
        self.menuLayout.addWidget(self.button_menu2)
        self.menuLayout.addWidget(self.button_menu3)

        text_color = self.palette["--foreground-color"]
        self.link_github = QLabel(
            f'<a href="{config.PROJECT_URL}" style="text-decoration:none;\
            color:{text_color}">{config.PROJECT_VERSION}</a>'
        )
        self.link_github.linkActivated.connect(self.open_hyperlink)
        self.link_github.setObjectName("link_github")
        self.link_github.setProperty("class", "faded")

        self.words_to_type_label = QLabel(self.get_words_subset())
        self.words_to_type_label.setWordWrap(True)
        self.words_to_type_label.setProperty("class", "words_to_type")
        self.description_label = QLabel()
        for button in [
            self.button_about,
            self.button_menu1,
            self.button_menu2,
            self.button_menu3,
            self.button_reset,
            self.button_settings,
            self.button_stats,
            self.button_exit,
        ]:
            button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.mainLayout.addWidget(self.title)
        self.mainLayout.addWidget(self.timer_label)
        self.timer_label.hide()
        self.mainLayout.addWidget(self.words_input)
        self.mainLayout.addWidget(self.input_label)
        self.mainLayout.addWidget(self.words_to_type_label)
        self.mainLayout.addWidget(self.button_reset)
        self.mainLayout.addWidget(self.description_label)

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

        self.button_reset.clicked.connect(self.reset_game)
        self.button_exit.clicked.connect(self.close)
        self.words_to_type_label.mousePressEvent = self.focus_input

        self.retranslate()

    def focus_input(self, *args):
        self.words_input.setFocus()

    def open_hyperlink(self, linkStr):
        QDesktopServices.openUrl(QUrl(linkStr))

    def reset_game(self):
        self.logger.debug("Reset game")
        self.end_game()
        self.focus_input()

    def validate_character(self, key):
        char = self.words_input.text()[-1]
        pos = self.pos
        self.pos += 1
        char_correct = self.words[pos]
        self.logger.debug(
            f"Typed in '{char}' - correct answer'{char_correct}'\
 - position {pos}"
        )
        if char_correct == char:  # correct character typed
            color = self.palette["--foreground-selected-color"]
            if char in self.correct_chars.keys():
                self.correct_chars[char] += 1
            else:
                self.correct_chars[char] = 1
        else:  # incorrect character typed
            color = self.palette["--error-color"]
            if char in self.incorrect_chars.keys():
                self.incorrect_chars[char] += 1
            else:
                self.incorrect_chars[char] = 1
            if char_correct == " ":
                char = "_"
            else:
                char = char_correct
        new_char = self.set_html_color(char, color)
        self.typed_in.append(new_char)
        self.words_to_type_label.setText(
            "".join(self.typed_in) + self.words[self.pos :]
        )

    @staticmethod
    def set_html_color(text, color):
        return f'<span style="color: {color};">{text}</span>'

    def get_words_subset(self):
        """Get a subset of words that will immediately appear on screen."""
        # TODO
        words = self.words
        return "".join(words)

    def retranslate(self):
        self.button_reset.setText(
            QCoreApplication.translate("QPushButton", "Reset")
        )
        self.button_settings.setText(
            QCoreApplication.translate("QPushButton", "Settings")
        )
        self.button_stats.setText(
            QCoreApplication.translate("QPushButton", "Stats")
        )
        self.button_about.setText(
            QCoreApplication.translate("QPushButton", "About")
        )
        self.button_menu1.setText(
            QCoreApplication.translate("QPushButton", "Word set")
        )
        self.button_menu2.setText(
            QCoreApplication.translate("QPushButton", "Mode")
        )
        self.button_menu3.setText(
            QCoreApplication.translate("QPushButton", "Duration")
        )
        self.button_exit.setText(
            QCoreApplication.translate("QPushButton", "Exit")
        )
        self.description_label.setText(
            QCoreApplication.translate("Qlabel", "Begin typing to start")
        )

    def start_game(self):
        mode = None
        time_ = None
        self.logger.info(f"Started game: mode {mode} - time {time_}")
        self.game_in_progress = True
        for button in [
            self.button_about,
            self.button_menu1,
            self.button_menu2,
            self.button_menu3,
            self.button_stats,
        ]:
            button.hide()
        self.description_label.hide()
        self.timer_label.show()

        self.timer.timeout.connect(self.end_game)
        self.timer.setSingleShot(True)
        self.timer.start(game_duration)
        self.update_timer.timeout.connect(self.update_timer_label)
        self.update_timer.start(update_timer_interval)

        self.start_time = time.time()

    def display_results(self):
        pass

    def end_game(self):
        if self.game_in_progress:
            self.end_time = time.time()
            time_elapsed = self.end_time - self.start_time
            self.logger.info(
                f"Finished game: time elapsed {time_elapsed:.2f}s\
 - characters typed {self.pos}"
            )
            self.update_timer.stop()
            self.save_results()
            self.words_input.clear()
            self.words_to_type_label.setText(
                self.words
            )  # TODO: do this after results shown

            # self.sidebarLayout.show()
            # self.menuLayout.show()
            for button in [
                self.button_about,
                self.button_menu1,
                self.button_menu2,
                self.button_menu3,
                # self.button_reset,
                # self.button_settings,
                self.button_stats,
                # self.button_exit,
            ]:
                button.show()
            self.timer_label.hide()
            self.description_label.show()
            self.display_results()
            self.game_in_progress = False
            self.pos = 0
            self.typed_in = []
            self.incorrect_chars = {}
            self.correct_chars = {}
            self.cur_char = self.words[0]
            self.focus_input()

    def update_timer_label(self):
        self.timer_label.setText(str(int(self.timer.remainingTime() // 1000)))

    def save_results(self):
        total_chracters=self.correct_chars+self.incorrect_chars
        time_elapsed=self.end_time-self.start_time
        self.accuracy= (self.correct_chars/(total_chracters))*100 #celnosc jako ilosc dobrze napisanych znakow przez wszystkie znaki
        self.cps =self.total_chracters/time_elapsed #ilosc znakow w czasie calej

        pass

    def close(self):
        sys.exit()
