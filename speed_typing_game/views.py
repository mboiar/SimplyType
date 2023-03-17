import sys
import time

import PyQt6.QtCore as QtCore
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QDesktopServices, QIcon, QCursor, QTextDocument
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


class InputLabel(QLabel):
    def __init__(self, width=600):
        super().__init__()
        self.cursor_pos = (0, 0, 5, 10) # TODO: use fontmetrics
        self.cursor = QtCore.QRect(*(self.cursor_pos))
        self.text = ""
        self.max_chars = 80*3 # TODO: set based on width
        self.setText(self.text[:self.max_chars])
        self.incorrect_chars = {}
        self.correct_chars = {}
        self.pos = 0

    def redraw(self, width):
        """Change displayed word count if width/font changed"""
        pass

    def newline(self):
        # TODO: hide prev. line, set cursor, show new text
        pass

    def update_label(self, char, pos):
        if self.text[pos] == char:
            updated_char_class = 'super-text'
            if char in self.correct_chars.keys():
                self.correct_chars[char] += 1
            else:
                self.correct_chars[char] = 1
        else:
            updated_char_class = 'error-text'
            if char in self.incorrect_chars.keys():
                self.incorrect_chars[char] += 1
            else:
                self.incorrect_chars[char] = 1
        new_char =  f'<span class="{updated_char_class}">{char}</span>'
        self.text = self.text[:pos] + new_char + self.text[pos+1:]
        self.setText(self.text)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.words = "words will appear here you can see that this\
is a multi-line text"
        self.incorrect_chars = {}
        self.correct_chars = {}
        self.text = self.words
        self.init_window()
        self.pos = 0
        self.error_color = "#CB4C4E"
        self.correct_color = "#e3e3e3"
        self.colored_char_width = len('<span style="color: #e3e3e3;">a</span>')
        self.words_to_type_doc = QTextDocument()
        self.words_to_type_doc.setHtml(self.words_to_type_label.text())
        self.plain_label = self.words_to_type_doc.toPlainText()
        self.typed_in = ''
        self.cur_char = self.words[0]

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
        self.timer_label = QLabel("32")
        self.timer_label.setObjectName("timer_label")
        self.input_label = InputLabel()
        self.words_input = QLineEdit()
        self.words_input.textEdited.connect(self.validate_character)
        self.words_input.textEdited.connect(self.move_cursor_back_on_backspace)
        # self.words_input.setEchoMode(QLineEdit.NoEcho)
        # self.words_input.setCursorPosition()
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
        self.description_label = QLabel("Begin typing to start")
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

        self.retranslate()

    def move_cursor_back_on_backspace(self, key):
        if key[-1] == QtCore.Qt.Key.Key_Backspace:
            self.pos = max(self.pos-1, 0)

    def open_hyperlink(self, linkStr):
        QDesktopServices.openUrl(QUrl(linkStr))

    def get_user_input(self):
        return self.words_input.text()

    def reset_game(self):
        """Reset the game: re-generate words and reset cursor position."""
        self.words_input.clear()
        # TODO: reset game

    def validate_character(self):
        """Check if typed character is correct."""
        self.words_to_type_doc.setHtml(self.words_to_type_label.text())
        self.plain_label = self.words_to_type_doc.toPlainText()
        char = self.words_input.text()[-1]
        
        pos = self.pos
        self.pos += 1
        if self.words[pos] == char:
            updated_char_class = 'super-text'
            color = self.correct_color
            if char in self.correct_chars.keys():
                self.correct_chars[char] += 1
            else:
                self.correct_chars[char] = 1
        else:
            updated_char_class = 'error-text'
            color = self.error_color
            if char in self.incorrect_chars.keys():
                self.incorrect_chars[char] += 1
            else:
                self.incorrect_chars[char] = 1
            if self.words[pos] == " ":
                char = "_"
            else:
                char = self.words[pos]
        # new_char =  f'<span class="{updated_char_class}">{char}</span>'
        new_char =  self.set_html_color(char, color)
        self.typed_in += new_char
        # text = self.words_to_type_label.text()
        # text = self.plain_label[:pos] + new_char + self.plain_label[pos+1:]
        # self.words_input.setText(new_char)
        self.words_to_type_label.setText(self.typed_in+self.words[self.pos:])

    @staticmethod
    def set_html_color(text, color):
        return f'<span style="color: {color};">{text}</span>'

    def get_words_subset(self):
        """Get a subset of words that will immediately appear on screen."""
        words = self.words
        return "".join(words)

    def retranslate(self):
        self.button_reset.setText(_translate("QPushButton", "reset"))
        self.button_settings.setText(_translate("QPushButton", "Settings"))
        self.button_stats.setText(_translate("QPushButton", "Stats"))
        self.button_about.setText(_translate("QPushButton", "About"))
        self.button_menu1.setText(_translate("QPushButton", "Language"))
        self.button_menu2.setText(_translate("QPushButton", "Mode"))
        self.button_menu3.setText(_translate("QPushButton", "Duration"))
        self.button_exit.setText(_translate("QPushButton", "Exit"))

    def start_game(self):
        self.sidebarLayout.hide()
        self.menuLayout.hide()
        self.description_label.hide()
        self.timer_label.show()
        self.timer = QtCore.QTimer()
        self.duration = 30*1000
        update_interval = 1000
        self.timer.singleShot(self.duration, self.end_game)
        self.timer.timeout.connect(self.update_timer_label)
        self.timer.start(update_interval)
        self.start_time = time.time()

    def display_results(self):
        pass

    def end_game(self):
        self.end_time = time.time()
        time_elapsed = self.end_time - self.start_time
        self.save_results()
        self.sidebarLayout.show()
        self.menuLayout.show()
        self.timer_label.hide()
        self.description_label.show()
        self.display_results()

        self.reset_game()

    def update_timer_label(self):
        self.timer_label.setText(self.timer.remainingTime())

    def save_results(self):
        pass


    def close(self):
        sys.exit()
