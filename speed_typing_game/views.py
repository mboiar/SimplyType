"""
Classes:

    MainTypingArea(QLineEdit)
    MainWindow(QWidget)

"""

import logging
import sys
import time
from typing import List, Dict

import PyQt6.QtCore as QtCore
from PyQt6.QtCore import QCoreApplication, Qt, QUrl, QSettings, QRect
import PyQt6.QtGui as QtGui
from PyQt6.QtGui import (QCursor, QDesktopServices, QIcon, QKeyEvent,
                         QMouseEvent, QFontMetrics, QPixmap, QResizeEvent)
from PyQt6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout, QWidget, QButtonGroup, QFileDialog, QListView, QGridLayout, QGroupBox)
# from PyQt6.QtQuick

from speed_typing_game import config
from speed_typing_game.utils import set_stylesheet
from speed_typing_game.database import retrieve_wordset
from speed_typing_game.models import TypingGame

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


class MainWindow(QWidget):
    """A class representing main window of the game."""

    def __init__(self, palette_name: str, icon: QIcon) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings("BoiarTech", config.PROJECT_NAME, self)
        self.timer = QtCore.QTimer()
        self.update_timer = QtCore.QTimer()
        self.palette = palette_name
        self.icon = icon
        self.mode = "default"
        self.duration = 30
        self.init_game()
        self.init_window()

    def init_window(self) -> None:
        """Initialize main window GUI"""
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

        self.words_input = MainTypingArea(allow_takeback=False, parent=self)
        self.button_reset = QPushButton()

        self.sidebarLayout = QVBoxLayout()
        self.button_settings = QPushButton()
        # self.settings_menu = SettingsMenu(self, CtmWidget())
        # self.settings_menu.hide()
        self.button_settings.clicked.connect(self.show_settings)
        self.button_about = QPushButton()
        self.button_stats = QPushButton()
        self.button_stats.setProperty("class", "highlighted")
        self.button_exit = QPushButton()

        self.menuLayout = QVBoxLayout()
        self.button_menu1 = QPushButton()
        # self.button_menu1.setMouseTracking(True)
        # self.button_menu1.mouse.connect(self.show_menu1)
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

        self.words_to_type_label = TypingHintLabel(self.words_input, self)
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
        # self.mainLayout.addWidget(self.input_label)
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
        self.words_to_type_label.mousePressEvent = self.set_focus
        # self.mainLayout.addWidget(self.settings_menu)
        # self._settings_popup = QPushButton("Gimme settings")
        # self.tr = TranslucentWidget(self)
        self._popframe = None
        self._popflag = False
        self.retranslate()

    @staticmethod
    def open_hyperlink(linkStr: str) -> bool:
        return QDesktopServices.openUrl(QUrl(linkStr))

    def set_focus(self, event: QMouseEvent = None) -> None:
        self.words_input.setFocus()

    def resizeEvent(self, event):
        if self._popflag:
            self._popframe.move(0, 0)
            self._popframe.resize(self.width(), self.height())

    def show_settings(self):
        self._popframe = TranslucentWidget(self)
        self._popframe.move(0, 0)
        self._popframe.resize(self.width(), self.height())
        self._popframe.SIGNALS.CLOSE.connect(self._closepopup)
        self._popflag = True
        self._popframe.show()

    def _closepopup(self):
        self._popframe.close()
        self._popflag = False

    # def resizeEvent(self, a0: QResizeEvent) -> None:
    #     self.settings_menu.resize(a0.size())
    #     a0.accept()
    #     super().resizeEvent(a0)

    def reset_game(self) -> None:
        self.logger.debug("Reset game")
        self.end_game()
        self.init_game()
        self.set_focus()

    def retranslate(self) -> None:
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

    def init_game(self, wordset=None, mode=None, duration=None, seed=None) -> None:
        self.game = TypingGame(wordset=wordset, mode=mode, duration=duration, seed=seed)
        self.words_to_type_label.setText(self.game.text)

    def start_game(self) -> None:
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

        self.timer.timeout.connect(self.finish_game)
        self.timer.setSingleShot(True)
        self.timer.start(self.game.duration)
        self.update_timer.timeout.connect(self.update_timer_label)
        self.update_timer.start(update_timer_interval)

        self.game.start_or_resume()

    def display_results(self) -> None:
        pass

    def finish_game(self) -> None:
        if not self.game.finish_or_pause():
            return
        self.update_timer.stop()
        self.game.save()
        self.display_results()
        self.words_to_type_label.label_caret.move(0,0)
        self.init_game()

        for button in [
            self.button_about,
            self.button_menu1,
            self.button_menu2,
            self.button_menu3,
            # self.button_reset,
            self.button_settings,
            self.button_stats,
            # self.button_exit,
        ]:
            button.show()
        self.timer_label.hide()
        self.description_label.show()
        self.set_focus()

    def update_timer_label(self) -> None:
        self.timer_label.setText(str(int(self.timer.remainingTime() // 1000)))

    def close(self) -> None:
        sys.exit()


class MainTypingArea(QLineEdit):
    """A class representing a typing area in the game."""

    def __init__(
        self, label: QWidget, allow_takeback: bool = False, parent: QWidget = None, *flags
    ) -> None:
        """
        Parameters
        ----------
        parent : MainWindow
            Parent window, used to start the game on keyPressEvent
        allow_takeback : bool, optional
            Boolean value that determines whether re-typing text is allowed during a game
        """

        self.logger = logging.getLogger(__name__)
        self.allow_takeback = allow_takeback
        super().__init__(parent, *flags)
        self.setReadOnly(True)
        # self.textEdited.connect(self.validate_character)
        self._pos = 0
        self.label = label
        self.typed_in = []

    def textEdited(self, text: str) -> None:
        """Process user input during a game."""
        # char = self.words_input.text()[-1]
        game = self.parent().game
        char = text[-1]
        pos = game.pos
        self.parent().game.pos += 1
        char_correct = game.words[pos]
        self.logger.debug(
            f"Typed in '{char}' - correct answer'{char_correct}'\
 - position {pos}"
        )
        if char_correct == char:  # correct character typed
            color = self.palette["--foreground-selected-color"]
        else:  # incorrect character typed
            color = self.palette["--error-color"]
            self.parent().game.incorrect_chars.update(char_correct)
            if char_correct == " ":
                char = "_"
            else:
                char = char_correct
        new_char = self.set_html_color(char, color)
        self.typed_in.append(new_char)
        new_text = "".join(self.typed_in) + game.text[game.pos :]
        if self.label.fontMetrics().boundingRect(game.text[:game.pos]).width() > self.label.geometry().width():
            self.label.newline()
        else:
            self.label.setText(new_text)
            if char_correct != " ":
                ch = char_correct
            elif char == "_":
                ch = char
            else:
                ch = "_"
            char_width = self.label.fontMetrics().boundingRectChar(ch).width()
            prev_pos = self.label.label_caret.pos()
            self.label.label_caret.move(prev_pos.x()+char_width+1, prev_pos.y())
        # super().textEdited(text)

    @staticmethod
    def set_html_color(text: str, color: str) -> str:
        return f'<span style="color: {color};">{text}</span>'


    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Process and filter user input, then call default (overrided) method."""
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
        elif key in TAKEBACK_KEYS or is_cutpaste_event:
            self.logger.debug(
                "Takeback"
            )
        if not window.game_in_progress:
            window.start_game()
        self.setReadOnly(False)
        super().keyPressEvent(event)
        self.setReadOnly(True)


# class WordsetMenu(QWidget):
#     def __init__(self, parent=None) -> None:
#         super.__init__(parent)
#         self.resize(415, 200)
#         self.model = WordSet(self)
#         self.model.setData("wordsets")
#         self.view = QListView()
#         self.view.setModel(self.model)
#         self.initUI()

#     def initUI(self) -> None:
#         self.layout = QGridLayout()
#         self.view.setLayout(self.layout)
#         self.view.setFlow(QListView.Flow.LeftToRight)
#         self.view.setWrapping(True)
#         self.view.setSpacing(3)

#         self.file_select = QFileDialog(self)
#         self.wordset_options = QButtonGroup()

class SettingsMenu(QWidget):
    def __init__(self, parent: QWidget, widget: QWidget) -> None:
        super().__init__(parent)
        # self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowState.Dialog)
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.ColorRole.Window, QtCore.Qt.GlobalColor.transparent)
        self.setPalette(palette)
        self.widget = widget
        self.widget.setParent(self)
        self.initUI()

    def resizeEvent(self, event):
        position_x = (self.frameGeometry().width()-self.widget.frameGeometry().width())/2
        position_y = (self.frameGeometry().height()-self.widget.frameGeometry().height())/2

        self.widget.move(position_x, position_y)
        event.accept()

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setRenderHint(QtGui.QPainter.RenderHints.Antialiasing)
        painter.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(0, 0, 0, 127)))
        painter.end()

    def initUI(self) -> None:
        pass
        # self.resize(150, 200)

        # self.theme_switch = QPushButton("Switch")
        # self.theme_switch.clicked.connect(self.toggle_theme)
        # self.theme_switch.setStyleSheet("""
        # <label class="switch">
        #     <input type="checkbox">
        #     <span class="slider round"></span>
        # </label>
        # """)
        # self.theme_switch_label = QLabel("Select theme")
        # self.layout().addWidget(self.theme_switch, 0, 0)
        # self.layout().addWidget(self.theme_switch_label, 0, 1)
        # self.retranslateUI()

    def update_position(self) -> None:
        parent_rect = self.parent().rect()
        self.setGeometry(parent_rect.width()/2-self.width()/2, parent_rect.height()/2-self.height()/2, self.width(), self.height())

    def resizeEvent(self, a0) -> None:
        super().resizeEvent(a0)
        self.update_position()

    def toggle_theme(self) -> None:
        themes = ['light', 'dark']
        set_stylesheet(
            QCoreApplication.instance(),
            themes[self.theme_switch.isChecked()]
        )

    def retranslateUI(self) -> None:
        self.theme_switch_label.setText(
            QCoreApplication.translate("QLabel", "Select theme")
        )
        # self.theme_switch.setText(
        #     QCoreApplication.translate("QPushButton", "")
        # )

class TranslucentWidgetSignals(QtCore.QObject):
    # SIGNALS
    CLOSE = QtCore.pyqtSignal()

class TranslucentWidget(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        # make the window frameless
        self.setWindowFlags(QtCore.Qt.WindowFlags.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.fillColor = QtGui.QColor(30, 30, 30, 120)
        self.penColor = QtGui.QColor("#333333")

        self.popup_fillColor = QtGui.QColor(240, 240, 240, 255)
        self.popup_penColor = QtGui.QColor(200, 200, 200, 255)

        self.close_btn = QPushButton(self)
        self.close_btn.setText("x")
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        font = QtGui.QFont()
        font.setPixelSize(18)
        font.setBold(True)
        self.close_btn.setFont(font)
        self.close_btn.setStyleSheet("background-color: rgb(0, 0, 0, 0)")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self._onclose)

        self.SIGNALS = TranslucentWidgetSignals()

    def resizeEvent(self, event):
        s = self.size()
        popup_width = 300
        popup_height = 120
        ow = int(s.width() / 2 - popup_width / 2)
        oh = int(s.height() / 2 - popup_height / 2)
        self.close_btn.move(ow + 265, oh + 5)

    def paintEvent(self, event):
        # This method is, in practice, drawing the contents of
        # your window.

        # get current window size
        s = self.size()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.RenderHints.Antialiasing, True)
        qp.setPen(self.penColor)
        qp.setBrush(self.fillColor)
        qp.drawRect(0, 0, s.width(), s.height())

        # drawpopup
        qp.setPen(self.popup_penColor)
        qp.setBrush(self.popup_fillColor)
        popup_width = 300
        popup_height = 120
        ow = int(s.width()/2-popup_width/2)
        oh = int(s.height()/2-popup_height/2)
        qp.drawRoundedRect(ow, oh, popup_width, popup_height, 5, 5)

        font = QtGui.QFont()
        font.setPixelSize(18)
        font.setBold(True)
        qp.setFont(font)
        qp.setPen(QtGui.QColor(70, 70, 70))
        tolw, tolh = 80, -5
        qp.drawText(ow + int(popup_width/2) - tolw, oh + int(popup_height/2) - tolh, "Will this work?")

        qp.end()

    def _onclose(self):
        print("Close")
        self.SIGNALS.CLOSE.emit()


class TypingHintLabel(QLabel):
    def __init__(self, lineedit: QWidget, parent: QWidget = None, *flags):
        super().__init__(parent, *flags)
        self.logger = logging.getLogger(__name__)
        self.max_chars = 0
        self.text_pos = 0
        self.num_lines = 3
        self.line_pos = 0
        self.lineedit = lineedit
        self.cur_line = 0
        self._caret = QPixmap(config.RESOURCES_DIR+'/images/cursor.png')
        self.label_caret = QLabel(self)
        self.label_caret.setPixmap(self._caret)
        self.redraw()
        self.label_caret.hide()

    def setText(self, text: str) -> None:
        super().setText(text) # TODO

    def redraw(self) -> None:
        """Change displayed word count if width/font changed"""
        self.label_width = self.geometry().width()
        max_px_length = self.label_width * self.num_lines
        self.max_chars = max_px_length / self.fontMetrics().averageCharWidth()
        self.logger.debug(f"Max chars: {self.max_chars}; label width: {self.label_width}; px_length: {max_px_length}; font width {self.fontMetrics().averageCharWidth()}")
        first_char_ind = self.text_pos - self.max_chars / 2
        last_char_ind = self.text_pos + self.max_chars / 2
        self.words_displayed = self.parent().words[int(first_char_ind):int(last_char_ind)]
        self.setText(self.words_displayed)
        self.label_caret.move(-4, 0)

    def newline(self):
        self.setText(self.parent().words[self.parent()._pos:])
        # self.label_caret.move(-4, 0)
        # if self.cur_line == 0:
        #     y = self.fontMetrics().lineSpacing() + self.fontMetrics().boundingRect(self.)
        #     self.label_caret.move(x, y)
        #     self.cur_line += 1
