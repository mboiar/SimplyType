"""
Classes:

    MainTypingArea(QLineEdit)
    TranslucentWidget(QWidget)
    TypingHintLabel(QLabel)
    MainWindow(QWidget)

"""
import logging
import sys
from typing import Dict, List

import PyQt6.QtCore as QtCore
import PyQt6.QtGui as QtGui
from PyQt6.QtCore import QCoreApplication, QSettings, Qt, QUrl
from PyQt6.QtGui import (QCursor, QDesktopServices, QFontMetrics, QIcon,
                         QKeyEvent, QMouseEvent, QPixmap, QResizeEvent)
from PyQt6.QtWidgets import (QButtonGroup, QFileDialog, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QListView,
                             QPushButton, QVBoxLayout, QWidget)

from speed_typing_game import config
from speed_typing_game.models import TypingGame
from speed_typing_game.utils import set_stylesheet


class MainTypingArea(QLineEdit):
    """A class representing a typing area in the game."""

    def __init__(
        self,
        label: QWidget,
        allow_takeback: bool = False,
        parent: "MainWindow" = None,
        *flags,
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
        # self._pos = 0
        self.label = label
        # self.typed_in = []

    def _textEdited(self, text: str) -> None:
        """Process user input during a game."""
        # char = self.words_input.text()[-1]
        game = self.parent().game
        char = text[-1]
        pos = game.pos
        self.parent().game.pos += 1
        char_correct = game.text[pos]
        self.logger.debug(
            f"Typed in '{char}' - correct answer'{char_correct}'\
 - position {pos}"
        )
        self.setText("")
        if char_correct == char:  # correct character typed
            color = self.palette().buttonText().color().name()
        else:  # incorrect character typed
            color = self.palette().highlight().color().name()
            self.parent().game.incorrect_chars.update(char_correct)
            if char_correct == " ":
                char = "_"
            else:
                char = char_correct
        new_char = self.set_html_color(char, color)
        # self.typed_in.append(new_char)
        self.label.formattedCharList += [new_char]
        # new_text = "".join(self.label.formattedCharList) + game.text[game.pos :]
        if (
            self.label.fontMetrics()
            .boundingRect(game.text[: game.pos])
            .width()
            > self.label.geometry().width()
        ):
            self.label.newline()
        else:
            # self.logger.debug(f"Setting new text {self.label.formattedCharList} {list(game.text[game.pos:])}")
            self.label.setCharList()
            # if char_correct != " ":
            #     ch = char_correct
            # elif char == "_":
            #     ch = char
            # else:
            #     ch = "_"
            # char_width = self.label.fontMetrics().boundingRectChar(ch).width()
            # prev_pos = self.label.label_caret.pos()
            # self.label.label_caret.move(prev_pos.x()+char_width+1, prev_pos.y())
        # super().textEdited(text)

    @staticmethod
    def set_html_color(text: str, color: str) -> str:
        return f'<span style="color: {color};">{text}</span>'

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Process and filter user input, then call default (overrided) method."""
        key = event.key()
        modifier = event.nativeModifiers()
        window = self.parent()
        modifier_message = (
            ("with a modifier:" + str(modifier)) if modifier else ""
        )
        self.logger.debug(
            f"Detected keyPressEvent: key {key} {modifier_message}"
        )
        is_cutpaste_event = modifier == config.CTRL_MODIFIER and key in config.CUT_KEYS
        if (not self.allow_takeback) and (
            key in config.TAKEBACK_KEYS or is_cutpaste_event
        ):
            self.logger.debug(
                "Skipped takeback event: takeback is not allowed"
            )
            return
        elif key in config.TAKEBACK_KEYS or is_cutpaste_event:
            self.logger.debug("Takeback")
        if not window.game.in_progress:
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


class TranslucentWidgetSignals(QtCore.QObject):
    # SIGNALS
    CLOSE = QtCore.pyqtSignal()


class TranslucentWidget(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        # make the window frameless
        self.setWindowFlags(QtCore.Qt.WindowFlags.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.fillColor = QtGui.QColor(30, 30, 30, 120)  # TODO
        self.penColor = QtGui.QColor("#333333")  # TODO

        # self.popup_fillColor = QtGui.QColor(240, 240, 240, 255)
        # self.popup_penColor = QtGui.QColor(200, 200, 200, 255)
        self.popup_fillColor = QtGui.QColor(240, 240, 240, 255)  # TODO
        self.popup_penColor = QtGui.QColor(200, 200, 200, 255)  # TODO

        self.close_btn = QPushButton(self)
        self.close_btn.setText("x")
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        font = QtGui.QFont()
        font.setPixelSize(12)
        font.setBold(True)
        self.close_btn.setFont(font)
        self.close_btn.setStyleSheet("background-color: rgb(0, 0, 0, 0)")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self._onclose)
        self.logger = logging.getLogger(__name__)

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
        ow = int(s.width() / 2 - popup_width / 2)
        oh = int(s.height() / 2 - popup_height / 2)
        qp.drawRoundedRect(ow, oh, popup_width, popup_height, 5, 5)

        font = QtGui.QFont()
        font.setPixelSize(18)
        font.setBold(True)
        qp.setFont(font)
        qp.setPen(QtGui.QColor(70, 70, 70))
        tolw, tolh = 80, -5
        qp.drawText(
            ow + int(popup_width / 2) - tolw,
            oh + int(popup_height / 2) - tolh,
            "Will this work?",
        )

        qp.end()

    def _onclose(self):
        self.logger.debug(f"Closed pop-up {__name__}")
        self.SIGNALS.CLOSE.emit()


class SettingsMenu(TranslucentWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        # self.theme_id = False
        self.initUI()

    def initUI(self) -> None:
        self.resize(150, 200)
        self.setLayout(QGridLayout())
        self.theme_switch = QPushButton(
            """<label class="switch">
            <input type="checkbox">
            <span class="slider round"></span>
        </label>"""
        )
        self.theme_switch.clicked.connect(self.toggle_theme)
        self.theme_switch.setStyleSheet(
            """

 /* The switch - the box around the slider */
 .switch {
    position: relative;
    display: inline-block;
    width: 60px;
    height: 34px;
  }
  
  /* Hide default HTML checkbox */
  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  
  /* The slider */
  .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #ccc;
    -webkit-transition: .4s;
    transition: .4s;
  }
  
  .slider:before {
    position: absolute;
    content: "";
    height: 26px;
    width: 26px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    -webkit-transition: .4s;
    transition: .4s;
  }
  
  input:checked + .slider {
    background-color: #2196F3;
  }
  
  input:focus + .slider {
    box-shadow: 0 0 1px #2196F3;
  }
  
  input:checked + .slider:before {
    -webkit-transform: translateX(26px);
    -ms-transform: translateX(26px);
    transform: translateX(26px);
  }
  
  /* Rounded sliders */
  .slider.round {
    border-radius: 34px;
  }
  
  .slider.round:before {
    border-radius: 50%;
  } 
        """
        )
        self.theme_switch_label = QLabel()
        self.layout().addWidget(self.theme_switch, 0, 0)
        self.layout().addWidget(self.theme_switch_label, 0, 1)
        self.retranslateUI()

    def toggle_theme(self) -> None:
        themes = ["light", "dark"]
        # self.theme_id = not self.theme_id
        set_stylesheet(
            QCoreApplication.instance(), themes[self.theme_switch.isChecked()]
        )

    def retranslateUI(self) -> None:
        self.theme_switch_label.setText(
            QCoreApplication.translate("QLabel", "Select theme")
        )


class LanguageMenu(TranslucentWidget):
    pass


class AboutPage(TranslucentWidget):
    pass


class DurationMenu(TranslucentWidget):
    pass


class ModeMenu(TranslucentWidget):
    pass


class TypingHintLabel(QLabel):
    """Label displaying user typed input."""

    def __init__(self, parent: "MainWindow" = None, *flags):
        super().__init__(parent, *flags)
        self.logger = logging.getLogger(__name__)
        self.max_chars: float = 0
        self.num_lines: int = 3
        self.line_pos: int = 0
        self._caret = QPixmap(config.RESOURCES_DIR + "/images/cursor.png")
        self.label_caret = QLabel(self)
        self.label_caret.setPixmap(self._caret)
        self.label_caret.hide()
        self.max_chars_displayed: float = 0
        self.min_char_pos: int = 0
        self.formattedCharList: List = []
        self.redraw()

    def setText(self, text: str) -> None:
        # self.logger.debug(f"Setting label text: {text}")
        # text = text[:min(len(text), int(self.max_chars))]
        super().setText(text)  # TODO

    def setCharList(self, char_list: List[str] = None) -> bool:
        if not char_list:
            char_list = self.formattedCharList
        try:
            char_list = char_list[self.min_char_pos :]  # TODO: sus
            self.check_extend()
            remaining_text = self.parent().game.text[
                self.parent().game.pos : self.max_char_pos()
            ]
        except IndexError as e:
            self.logger.error(
                f"Invalid char list (length {len(char_list)}, min pos: {self.min_char_pos}): {char_list[:10]}..."
            )
            return False
        self.logger.debug(f"Char list: {char_list}")
        self.logger.debug(f"Remaining text: {remaining_text}")
        self.logger.debug(
            f"Setting rich text {''.join(char_list+list(remaining_text))}"
        )
        self.setText("".join(char_list + list(remaining_text)))
        return True

    def max_char_pos(self) -> int:
        return int(self.min_char_pos + self.max_chars)

    def check_extend(self) -> None:
        if len(self.parent().game.text[self.min_char_pos :]) < self.max_chars:
            self.logger.debug(
                f"Asking to extend text: {len(self.parent().game.text[self.min_char_pos:])} < {self.max_chars}"
            )
            self.parent().game.extend_text()

    def redraw(self) -> None:
        """Change displayed word count if width/font changed"""
        self.label_width = self.geometry().width()
        max_px_length = self.label_width * self.num_lines
        self.max_chars = (
            max_px_length / 1.4
        )  # TODO self.fontMetrics().boundingRectChar("m").width()
        self.char_line_width = self.label_width / 1.4
        self.logger.debug(
            f"Max chars: {self.max_chars}; label width: {self.label_width}; px_length: {max_px_length}; font width {self.fontMetrics().averageCharWidth()}"
        )
        self.setCharList()
        # self.words_displayed = self.parent().game.text[int(first_char_ind):int(last_char_ind)]
        # self.logger.debug(f"Setting label text: {self.words_displayed}")
        # self.setText(self.words_displayed)
        # self.label_caret.move(-4, 0)
        # self.chars_displayed = 0 # TODO

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        # TODO
        super().paintEvent(a0)

    def newline(self) -> None:
        self.logger.debug("Newline")
        if self.line_pos == 0:
            self.line_pos += 1
        if self.line_pos == 1:
            # TODO reset caret
            self.min_char_pos += int(self.char_line_width)
            self.logger.debug(
                f"Set new starting position: {self.min_char_pos}"
            )
        self.setCharList()
        # self.setText(self.parent().words[self.parent()._pos:])
        # TODO
        # self.label_caret.move(-4, 0)
        # if self.cur_line == 0:
        #     y = self.fontMetrics().lineSpacing() + self.fontMetrics().boundingRect(self.)
        #     self.label_caret.move(x, y)
        #     self.cur_line += 1


class MainWindow(QWidget):
    """A class representing main window of the game."""

    def __init__(self, icon: QIcon) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings("BoiarTech", config.PROJECT_NAME, self)
        self.timer = QtCore.QTimer()
        self.icon = icon
        self.game = TypingGame()
        self.init_window()

    def init_window(self) -> None:
        """Initialize main window GUI"""
        self.logger.debug("Initializing main window")
        self.resize(900, 500)
        self.setWindowTitle(config.PROJECT_NAME)
        self.setWindowIcon(self.icon)

        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.title = QLabel(
            f"<font color='{self.palette().brightText().color().name()}'>Simply</font>Type"
        )
        self.title.setProperty("class", "heading")
        self.timer_label = QLabel()
        sp_retain = self.timer_label.sizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        self.timer_label.setSizePolicy(sp_retain)
        self.timer_label.setObjectName("timer_label")
        self.timer_label.setProperty("class", "highlighted")

        self.words_to_type_label = TypingHintLabel(self)
        self.words_to_type_label.setWordWrap(True)
        self.words_to_type_label.setProperty("class", "words_to_type")
        # self.words_to_type_label.setText(self.game.text)

        self.words_input = MainTypingArea(
            self.words_to_type_label, allow_takeback=False, parent=self
        )
        self.words_input.textEdited.connect(self.words_input._textEdited)
        self.button_reset = QPushButton()

        self.sidebarLayout = QVBoxLayout()
        self.button_settings = QPushButton()
        self.settings_menu = SettingsMenu(self)
        self.settings_menu.hide()
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

        self.link_github = QLabel(
            f'<a href="{config.PROJECT_URL}" style="text-decoration:none;\
            color:{self.palette().text().color().name()}">{config.PROJECT_VERSION}</a>'
        )
        self.link_github.linkActivated.connect(self.open_hyperlink)
        self.link_github.setObjectName("link_github")
        self.link_github.setProperty("class", "faded")

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

    def show_settings(self) -> None:
        self.show_popup(self.settings_menu)

    def show_popup(self, popup: TranslucentWidget) -> None:
        popup.move(0, 0)
        popup.resize(self.width(), self.height())
        popup.SIGNALS.CLOSE.connect(self._closepopup)
        self._popflag = True
        self.game.finish_or_pause()
        # self.timer.pause() # TODO
        popup.show()
        # self._popframe.move(0, 0)
        # self._popframe.resize(self.width(), self.height())
        # self._popframe.SIGNALS.CLOSE.connect(self._closepopup)
        # self._popflag = True
        # self.game.finish_or_pause()
        # self._popframe.show()

    def _closepopup(self, popup: TranslucentWidget) -> None:
        popup.close()
        self._popflag = False

    def reset_game(self) -> None:
        self.logger.debug("Reset game")
        self.finish_game(save=False)
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

    def init_game(
        self, wordset_id=None, mode=None, duration=None, seed=None
    ) -> None:
        self.game = TypingGame(
            wordset_id=wordset_id, mode=mode, duration=duration, seed=seed
        )
        self.words_to_type_label.min_char_pos = self.game.pos
        self.logger.debug(f"Setting starting label position {self.game.pos}")
        self.words_to_type_label.setCharList()

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

        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.finish_game)
        self.logger.debug(f"Setting timer for {self.game.duration//1000} s")
        self.timer.start(self.game.duration)
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_timer_label)
        self.update_timer.start(100)

        self.game.start_or_resume()

    def display_results(self) -> None:
        pass

    def finish_game(self, save: bool = False) -> None:
        self.logger.debug("Trying to finish game?")
        if not self.game.finish_or_pause(save=save):
            return
        self.words_to_type_label.formattedCharList.clear()
        self.update_timer.stop()
        # self.game.save()
        self.display_results()
        self.words_to_type_label.label_caret.move(0, 0)
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
