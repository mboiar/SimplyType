"""
Classes:

    MainTypingArea(QLineEdit)
    TranslucentWidget(QWidget)
    TypingHintLabel(QLabel)
    MainWindow(QWidget)

"""
import logging
import sys
from typing import Dict, List, Tuple, Optional
from collections import Counter

import PyQt6.QtCore as QtCore
import PyQt6.QtGui as QtGui
from PyQt6.QtCore import QCoreApplication, QSettings, Qt, QUrl
from PyQt6.QtGui import (QCursor, QDesktopServices, QFontMetrics, QIcon,
                         QKeyEvent, QMouseEvent, QPixmap, QResizeEvent)
from PyQt6.QtWidgets import (QButtonGroup, QFileDialog, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QListView,
                             QPushButton, QVBoxLayout, QWidget, QAbstractButton)
from PyQt6 import QtWidgets
import pyqtgraph as pg

from speed_typing_game import config, models, database
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
                char = " "
            else:
                char = char_correct
        new_char = self.set_html_color(char, color)
        # self.typed_in.append(new_char)
        self.label.formattedCharList += [new_char]
        # new_text = "".join(self.label.formattedCharList) + game.text[game.pos :]
        if (
            self.parent().game.pos % int(self.label.char_line_width) == 0
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


class TranslucentWidgetSignals(QtCore.QObject):
    # SIGNALS
    CLOSE = QtCore.pyqtSignal()


class TranslucentWidget(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.logger = logging.getLogger(__name__)
        # make the window frameless
        self.setWindowFlags(QtCore.Qt.WindowFlags.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.fillColor = self.palette().window().color().darker(120) #QtGui.QColor(30, 30, 30, 120)  # TODO
        self.penColor = self.palette().windowText().color().darker(120) #QtGui.QColor("#333333")  # TODO

        # self.popup_fillColor = QtGui.QColor(240, 240, 240, 255)
        # self.popup_penColor = QtGui.QColor(200, 200, 200, 255)
        self.popup_fillColor = self.palette().window().color() #QtGui.QColor(240, 240, 240, 255)  # TODO
        self.popup_penColor = self.palette().windowText().color() #QtGui.QColor(200, 200, 200, 255)  # TODO

        self.close_btn = QPushButton(self)
        self.close_btn.setText("x")
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.popup_width = self.width()//2
        self.popup_height = self.height()//2

        font = QtGui.QFont()
        font.setPixelSize(14)
        font.setBold(True)
        self.close_btn.setFont(font)
        # self.close_btn.setStyleSheet("background-color: rgb(0, 0, 0, 0)")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self._onclose)

        self.SIGNALS = TranslucentWidgetSignals()

    def resizeEvent(self, event):
        s = self.size()
        # popup_width = 300
        # popup_height = 120
        ow = int(s.width() / 2 - self.popup_width / 2)
        oh = int(s.height() / 2 - self.popup_height / 2)
        self.close_btn.move(ow + 265, oh + 5)

    def paintEvent(self, event):
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
        popup_width = self.popup_width
        popup_height = self.popup_height
        ow = int(s.width() / 2 - popup_width / 2)
        oh = int(s.height() / 2 - popup_height / 2)
        qp.drawRoundedRect(ow, oh, popup_width, popup_height, 5, 5)

        font = QtGui.QFont()
        font.setPixelSize(18)
        font.setBold(True)
        qp.setFont(font)
        # qp.setPen(QtGui.QColor(70, 70, 70))
        # tolw, tolh = 80, -5
        # qp.drawText(
        #     ow + int(popup_width / 2) - tolw,
        #     oh + int(popup_height / 2) - tolh,
        #     "Will this work?",
        # )
        qp.end()

    def _onclose(self):
        self.logger.debug(f"Closed pop-up {self}")
        self.SIGNALS.CLOSE.emit()


class SwitchPrivate(QtCore.QObject):
    def __init__(self, q: QWidget, parent: QWidget = None) -> None:
        QtCore.QObject.__init__(self, parent=parent)
        self.mPointer = q
        self.mPosition: float = 0.0
        self.mGradient = QtGui.QLinearGradient()
        self.mGradient.setSpread(QtGui.QGradient.Spread.PadSpread)

        self.animation = QtCore.QPropertyAnimation(self)
        self.animation.setTargetObject(self)
        self.animation.setPropertyName(b'position')
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QtCore.QEasingCurve(QtCore.QEasingCurve.Type.InOutCirc))

        self.animation.finished.connect(self.mPointer.update)

    @QtCore.pyqtProperty(float)
    def position(self) -> float:
        return self.mPosition

    @position.setter
    def position(self, value: float) -> None:
        self.mPosition = value
        self.mPointer.update()

    def draw(self, painter: QtGui.QPainter) -> None:
        r = self.mPointer.rect()
        margin = r.height()/10
        shadow = self.mPointer.palette().dark().color()
        light = self.mPointer.palette().light().color()
        button = self.mPointer.palette().button().color()
        painter.setPen(Qt.PenStyle.NoPen)

        self.mGradient.setColorAt(0, shadow.darker(130))
        self.mGradient.setColorAt(1, light.darker(130))
        self.mGradient.setStart(0, r.height())
        self.mGradient.setFinalStop(0, 0)
        painter.setBrush(self.mGradient)
        painter.drawRoundedRect(r, r.height()/2, r.height()/2)

        self.mGradient.setColorAt(0, shadow.darker(140))
        self.mGradient.setColorAt(1, light.darker(160))
        self.mGradient.setStart(0, 0)
        self.mGradient.setFinalStop(0, r.height())
        painter.setBrush(self.mGradient)
        painter.drawRoundedRect(r.adjusted(margin, margin, -margin, -margin), r.height()/2, r.height()/2)

        self.mGradient.setColorAt(0, button.darker(130))
        self.mGradient.setColorAt(1, button)

        painter.setBrush(self.mGradient)

        x = r.height()/2.0 + self.mPosition*(r.width()-r.height())
        painter.drawEllipse(QtCore.QPointF(x, r.height()/2), r.height()/2-margin, r.height()/2-margin)

    @QtCore.pyqtSlot(bool, name='animate')
    def animate(self, checked: bool) -> None:
        self.animation.setDirection(QtCore.QPropertyAnimation.Direction.Forward if checked else QtCore.QPropertyAnimation.Direction.Backward)
        self.animation.start()

class Switch(QAbstractButton):
    def __init__(self, parent: QWidget = None) -> None:
        QAbstractButton.__init__(self, parent=parent)
        self.dPtr = SwitchPrivate(self)
        self.setCheckable(True)
        self.clicked.connect(self.dPtr.animate)

    def sizeHint(self):
        return QtCore.QSize(64, 32)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHints.Antialiasing)
        self.dPtr.draw(painter)

    def resizeEvent(self, event):
        self.update()

class SettingsMenu(TranslucentWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()
        
    def show(self) -> None:
        if QtCore.QSettings().value("styles/theme") == "dark":
            self.theme_switch.setChecked(True)
        super().show()

    def initUI(self) -> None:
        self.setLayout(QGridLayout())
        margin_x = self.rect().width()//2 - self.popup_width//2 + 200
        margin_y = self.rect().height()//2 - self.popup_height//2 + 200
        self.logger.debug(f"Setting margins: {margin_x} {margin_y}, w: {self.width()} h: {self.height()}")
        self.setContentsMargins(margin_x, margin_y, margin_x, margin_y)
        self.theme_switch = Switch()
        self.theme_switch.clicked.connect(self.toggle_theme)

        self.theme_switch_label = QLabel()

        self.language_selector = QButtonGroup()
        self.language_selector_label = QLabel()
        for i, widgets in enumerate([
            (self.theme_switch_label, self.theme_switch),
            # (self.language_selector_label, self.language_selector)
        ]):
            self.layout().addWidget(widgets[0], i, 0)
            # self.layout().spacerItem()
            self.layout().addWidget(widgets[1], i, 1)
        self.retranslateUI()

    def toggle_theme(self) -> None:
        settings = QSettings("BoiarTech", config.PROJECT_NAME)
        themes = ["light", "dark"]
        theme = themes[self.theme_switch.isChecked()]
        set_stylesheet(
            QCoreApplication.instance(), theme
        )
        QtCore.QSettings().setValue("styles/theme", theme)

    def retranslateUI(self) -> None:
        self.theme_switch_label.setText(
            QCoreApplication.translate("QLabel", "Use dark scheme")
        )
        self.language_selector_label.setText(
            QCoreApplication.translate("QLabel", "Select language")
        )


class WordsetFileSelectWindow(TranslucentWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        self.setLayout(QGridLayout())
        margin_x = self.rect().width()//2 - self.popup_width//2 + 200
        margin_y = self.rect().height()//2 - self.popup_height//2 + 200
        self.logger.debug(f"Setting margins: {margin_x} {margin_y}, w: {self.width()} h: {self.height()}")
        self.setContentsMargins(margin_x, margin_y, margin_x, margin_y)

        self.wordset_list_view = QListView()
        self.wordset_from_file_button = QPushButton("Choose file containing wordset", self)
        self.wordset_from_file_button.clicked.connect(self.get_set_wordset)
        self.save_to_database_checkbox = QtWidgets.QCheckBox(self)
        self.save_to_database_label = QLabel(self)
        for i, widgets in enumerate([
            (self.wordset_from_file_button, ),
            (self.save_to_database_label, self.save_to_database_checkbox)
        ]):
            for j, widget in enumerate(widgets):
                self.layout().addWidget(widget, i, j)
            # self.layout().spacerItem()
            # self.layout().addWidget(widgets[1], i, 1)
        self.retranslateUI()

    def get_wordset_filename_from_user_input(self) -> Optional[str]:
        file_name, selected_filter = QFileDialog.getOpenFileName(
            self, QCoreApplication.translate("QFileDialog", "Load wordset"),
            "",
            QCoreApplication.translate("QFileDialog", "text files (*.txt *.csv)")
            )
        if file_name is not None:
            self.logger.info(f"Received filename from user input: {file_name}")
        else:
            self.logger.warning(f"No wordset file selected")
            return None
        return file_name
    
    def get_set_wordset(self) -> None:
        filename = self.get_wordset_filename_from_user_input()
        if filename:
            wordset = models.Wordset.from_file(filename)
            if wordset:
                self.parent().set_wordset(wordset, self.save_to_database_checkbox.isChecked())
            
    
    def retranslateUI(self) -> None:
        self.save_to_database_label.setText(
            QCoreApplication.translate("QLabel", "Add wordset to database")
        )


class WordsetMenu(TranslucentWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()
        
    def show(self) -> None:
        super().show()

    def initUI(self) -> None:
        self.setLayout(QHBoxLayout())
        margin_x = self.rect().width()//2 - self.popup_width//2 + 200
        margin_y = self.rect().height()//2 - self.popup_height//2 + 200
        self.logger.debug(f"Setting margins: {margin_x} {margin_y}, w: {self.width()} h: {self.height()}")
        self.setContentsMargins(margin_x, margin_y, margin_x, margin_y)

        self.wordset_list_view = QListView()
        self.wordset_from_file_button = QPushButton("Custom")
        self.wordset_from_file_window = WordsetFileSelectWindow(self)
        self.wordset_from_file_button.clicked.connect(lambda: self.parent().show_popup(self.wordset_from_file_window))
        for _, widgets in enumerate([
            (self.wordset_from_file_button),
        ]):
            self.layout().addWidget(widgets)
            # self.layout().spacerItem()
            # self.layout().addWidget(widgets[1], i, 1)
        self.retranslateUI()

    def set_wordset(self, wordset: models.Wordset, add_to_database: bool = False) -> None:
        settings = QSettings("BoiarTech", config.PROJECT_NAME)
        set_wordset = False
        if wordset.id:
            settings.setValue("game/options/wordset/id", wordset.id)
            set_wordset = True
        elif wordset.name:
            settings.setValue("game/options/wordset/name", wordset.name)
            set_wordset = True

        if set_wordset:
            self.logger.info(f"Set default wordset {wordset}")
            if add_to_database:
                wordset.save()
            return None
        self.logger.error(f"Could not set wordset: wordset {wordset} has incomplete data")

    def retranslateUI(self) -> None:
        pass
        # self.duration_selector_label.setText(
        #     QCoreApplication.translate("QLabel", "Select duration")
        # )


class AboutWindow(TranslucentWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        self.setLayout(QGridLayout())
        margin_x = self.rect().width()//2 - self.popup_width//2 + 200
        margin_y = self.rect().height()//2 - self.popup_height//2 + 200
        self.logger.debug(f"Setting margins: {margin_x} {margin_y}, w: {self.width()} h: {self.height()}")
        self.setContentsMargins(margin_x, margin_y, margin_x, margin_y)
        self.about_label = QLabel()

        for i, widgets in enumerate([
            (self.about_label),
        ]):
            self.layout().addWidget(widgets, i, 0)
            # self.layout().spacerItem()
            # self.layout().addWidget(widgets[1], i, 1)
        self.retranslateUI()

    def retranslateUI(self) -> None:
        self.about_label.setText(
            QCoreApplication.translate("QLabel", f"About {config.PROJECT_NAME}")
        )


class UserStatsWindow(TranslucentWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.game_data = None
        self.initUI()

    def _update(self) -> None:
        self.game_data = self.get_game_data()
        
    def show(self) -> None:
        self._update()
        # self.wpm_plot = pg.PlotWidget()
        self.most_inaccurate_letters = [()]
        self.avg_stats = []
        self.animal_speed_comparison = None
        if self.game_data:
            accs, wpms, dates, incorrect_charss = list(zip(*self.game_data))
        # self.wpm_plot.plot(dates, wpms)
            counter = Counter()
            for chars in incorrect_charss:
                counter.update(chars)
            self.most_inaccurate_letters = counter.most_common(10)
            self.avg_stats = [sum(i)/len(i) for i in [accs, wpms]]
        # TODO
        super().show()        

    def initUI(self) -> None:
        self.setLayout(QGridLayout())
        margin_x = self.rect().width()//2 - self.popup_width//2 + 200
        margin_y = self.rect().height()//2 - self.popup_height//2 + 200
        self.logger.debug(f"Setting margins: {margin_x} {margin_y}, w: {self.width()} h: {self.height()}")
        self.setContentsMargins(margin_x, margin_y, margin_x, margin_y)
        self.title = QLabel()
        self.title.setProperty("class", "heading")

        for i, widgets in enumerate([
            (self.title)
        ]):
            self.layout().addWidget(widgets, i, 0)
            # self.layout().spacerItem()
            # self.layout().addWidget(widgets[1], i, 1)
        self.retranslateUI()

    def get_game_data(self) -> Optional[List[Tuple[float, float, float, str]]]:
        return database.get_game_data()

    def retranslateUI(self) -> None:
        self.title.setText(
            QCoreApplication.translate("QLabel", "User statistics")
        )


class GameStatsWindow(TranslucentWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()

    def show(self) -> None:
        stats = self.parent().game.get_stats()
        if stats:
            self.wpm_data.setText(f"{stats['wpm']:.0f} wpm")
            self.accuracy_data.setText(f"{stats['accuracy']*100:.0f}%")
            most_frequent = sorted(stats["incorrect characters frequency"], key=lambda x: x[1])[:5]
            self.incorrect_chars_data.setText(" ".join([f"'{i[0]}' ({i[1]})" for i in most_frequent]))
        super().show()

    def initUI(self) -> None:
        self.setLayout(QGridLayout())
        margin_x = self.rect().width()//2 - self.popup_width//2 + 200
        margin_y = self.rect().height()//2 - self.popup_height//2 + 200
        self.logger.debug(f"Setting margins: {margin_x} {margin_y}, w: {self.width()} h: {self.height()}")
        self.setContentsMargins(margin_x, margin_y, margin_x, margin_y)

        self.title = QLabel()
        self.wpm_label = QLabel()
        self.wpm_data = QLabel()
        self.accuracy_label = QLabel()
        self.accuracy_data = QLabel()
        self.incorrect_chars_label = QLabel()
        self.incorrect_chars_data = QLabel()
        self.button_continue = QPushButton("Continue")
        self.button_continue.clicked.connect(self.close_btn.click)
        # self.theme_switch.clicked.connect(self.set_mode)
        # self.duration_selector_label = QLabel()
        for i, widgets in enumerate([
            (self.title,),
            (self.wpm_label, self.wpm_data),
            (self.accuracy_label, self.accuracy_data),
            (self.incorrect_chars_label, self.incorrect_chars_data),
            (self.button_continue,)
        ]):
            for j, widget in enumerate(widgets):
                self.layout().addWidget(widget, i, j)
        self.retranslateUI()

    def retranslateUI(self) -> None:
        self.title.setText(
            QCoreApplication.translate("QLabel", "Game results")
        )
        self.wpm_label.setText(
            QCoreApplication.translate("QLabel", "Speed")
        )
        self.accuracy_label.setText(
            QCoreApplication.translate("QLabel", "Accuracy")
        )
        self.incorrect_chars_label.setText(
            QCoreApplication.translate("QLabel", "Most frequent incorrect characters")
        )

class PauseMenu(TranslucentWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        self.setLayout(QVBoxLayout())
        margin_x = self.rect().width()//2 - self.popup_width//2 + 200
        margin_y = self.rect().height()//2 - self.popup_height//2 + 200
        self.logger.debug(f"Setting margins: {margin_x} {margin_y}, w: {self.width()} h: {self.height()}")
        self.setContentsMargins(margin_x, margin_y, margin_x, margin_y)
        self.label = QLabel()
        self.exit_button = QPushButton()
        self.resume_button = QPushButton()
        self.settings_button = QPushButton()
        self.resume_button.clicked.connect(self.parent().resume)
        self.exit_button.clicked.connect(self.parent().close)
        self.settings_button.clicked.connect(lambda: self.parent().show_popup(self.parent().settings_menu))

        for _, widget in enumerate([
            self.label,
            self.resume_button,
            self.settings_button,
            self.exit_button
        ]):
            self.layout().addWidget(widget)
            # self.layout().spacerItem()
            # self.layout().addWidget(widgets[1], i, 1)
        self.retranslateUI()

    def retranslateUI(self) -> None:
        self.label.setText(
            QCoreApplication.translate("QLabel", "Pause game")
        )
        self.resume_button.setText(
            QCoreApplication.translate("QLabel", "Resume")
        )
        self.settings_button.setText(
            QCoreApplication.translate("QLabel", "Settings")
        )
        self.exit_button.setText(
            QCoreApplication.translate("QLabel", "Exit")
        )


class DurationMenu(TranslucentWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        self.setLayout(QHBoxLayout())
        margin_x = self.rect().width()//2 - self.popup_width//2 + 200
        margin_y = self.rect().height()//2 - self.popup_height//2 + 200
        self.logger.debug(f"Setting margins: {margin_x} {margin_y}, w: {self.width()} h: {self.height()}")
        self.setContentsMargins(margin_x, margin_y, margin_x, margin_y)

        self.duration_selector = QButtonGroup()
        # self.theme_switch.clicked.connect(self.set_duration)

        # self.duration_selector_label = QLabel()
        for _, widgets in enumerate([
            # self.duration_selector
        ]):
            self.layout().addWidget(widgets)
            # self.layout().spacerItem()
            # self.layout().addWidget(widgets[1], i, 1)
        self.retranslateUI()

    def set_duration(self, duration: int = 30) -> None:
        settings = QSettings("BoiarTech", config.PROJECT_NAME)
        settings.setValue("game/options/duration", duration)

    def retranslateUI(self) -> None:
        pass
        # self.duration_selector_label.setText(
        #     QCoreApplication.translate("QLabel", "Select duration")
        # )


class ModeMenu(TranslucentWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        self.setLayout(QHBoxLayout())
        margin_x = self.rect().width()//2 - self.popup_width//2 + 200
        margin_y = self.rect().height()//2 - self.popup_height//2 + 200
        self.logger.debug(f"Setting margins: {margin_x} {margin_y}, w: {self.width()} h: {self.height()}")
        self.setContentsMargins(margin_x, margin_y, margin_x, margin_y)

        self.wordset_selector = QButtonGroup()
        # self.duration_selector_label = QLabel()
        for _, widgets in enumerate([
            # self.wordset_selector
        ]):
            self.layout().addWidget(widgets)
            # self.layout().spacerItem()
            # self.layout().addWidget(widgets[1], i, 1)
        self.retranslateUI()

    def set_mode(self, mode: str = "default") -> None:
        settings = QSettings("BoiarTech", config.PROJECT_NAME)
        settings.setValue("game/options/mode", mode)

    def retranslateUI(self) -> None:
        pass
        # self.duration_selector_label.setText(
        #     QCoreApplication.translate("QLabel", "Select duration")
        # )


class TypingHintLabel(QLabel):
    """Label displaying user typed input."""

    def __init__(self, parent: 'MainWindow' = None, *flags):
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
        # self.logger.debug(f"Char list: {char_list}")
        # self.logger.debug(f"Remaining text: {remaining_text}")
        self.logger.debug(
            f"Setting rich text {''.join(char_list+list(remaining_text))[:40]}..."
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
        inp = QLineEdit()
        inp.setText(self.parent().game.text)
        self.logger.debug(inp.cursorPositionAt(self.geometry().topRight()))
        inp.clear()
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
        if self.line_pos == 0:
            self.line_pos += 1
        elif self.line_pos == 1:
            # TODO reset caret
            self.min_char_pos += int(self.char_line_width)
            self.logger.debug(
                f"Set new starting position: {self.min_char_pos}"
            )
        self.logger.debug(f"Newline: {self.line_pos}")
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
        pixmapi = QtWidgets.QStyle.StandardPixmap.SP_MediaPlay
        icon = self.style().standardIcon(pixmapi)
        self.button_pause = QPushButton()
        self.button_pause.setIcon(icon)
        self.pause_menu = PauseMenu(self)
        self.gamestats_window = GameStatsWindow(self)
        self.button_about = QPushButton()
        self.about_popup = AboutWindow(self)
        self.button_stats = QPushButton()
        self.button_stats.setProperty("class", "highlighted")
        self.stats_popup = UserStatsWindow(self)
        self.button_exit = QPushButton()

        self.menuLayout = QVBoxLayout()
        self.button_menu1 = QPushButton()
        self.menu1_popup = WordsetMenu(self)
        self.button_menu2 = QPushButton()
        self.menu2_popup = ModeMenu(self)
        self.button_menu3 = QPushButton()
        self.menu3_popup = DurationMenu(self)
        self.menuLayout.addWidget(self.button_menu1)
        self.menuLayout.addWidget(self.button_menu2)
        self.menuLayout.addWidget(self.button_menu3)
        self.menu_list = [
            (self.menu1_popup, self.button_menu1),
            (self.menu2_popup, self.button_menu2),
            (self.menu3_popup, self.button_menu3),
            (self.settings_menu, self.button_settings),
            (self.pause_menu, self.button_pause),
            (self.about_popup, self.button_about),
            (self.stats_popup, self.button_stats)
        ]
        for i, menu_item in enumerate(self.menu_list):
            menu_item[0].hide()
            # menu_item[1].clicked.connect(lambda: self.show_popup(self.menu_list[i][0]))
        # self.button_menu3.clicked.connect(lambda: self.show_popup(self.menu3_popup))
        self.button_menu1.clicked.connect(lambda: self.show_popup(self.menu1_popup))
        self.button_menu2.clicked.connect(lambda: self.show_popup(self.menu2_popup))
        self.button_menu3.clicked.connect(lambda: self.show_popup(self.menu3_popup))
        self.button_settings.clicked.connect(lambda: self.show_popup(self.settings_menu))
        self.button_pause.clicked.connect(lambda: self.show_popup(self.pause_menu))
        self.button_about.clicked.connect(lambda: self.show_popup(self.about_popup))
        self.button_stats.clicked.connect(lambda: self.show_popup(self.stats_popup))

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
            self.button_pause,
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


    def resume(self) -> None:
        pass

    def show_popup(self, popup: TranslucentWidget) -> None:
        self.logger.info(f"Showing popup {popup}")
        popup.move(0, 0)
        popup.resize(self.width(), self.height())
        # popup.initUI()
        popup.SIGNALS.CLOSE.connect(self._closepopup)
        self._popflag = True
        self.game.finish_or_pause()
        # self.timer.pause() # TODO
        popup.show()
        self._popframe = popup
        # self._popframe.move(0, 0)
        # self._popframe.resize(self.width(), self.height())
        # self._popframe.SIGNALS.CLOSE.connect(self._closepopup)
        # self._popflag = True
        # self.game.finish_or_pause()
        # self._popframe.show()

    def _closepopup(self) -> None:
        popup = self._popframe
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
        self, wordset_id: Optional[int] = None, mode: Optional[str] = None, duration: Optional[int] = None, seed: Optional[int] = None
    ) -> None:
        settings = QSettings("BoiarTech", config.PROJECT_NAME)
        options = {"wordset/id":wordset_id, "mode":mode, "duration":duration, "seed":seed}
        for (option, val) in options.items():
            if val is None and settings.contains(f"game/options/{option}"):
                options[option] = settings.value(f"game/options/{option}")
                self.logger.debug(f"Retrieved '{option}' from settings: {val}")
        self.game = TypingGame(
            wordset_id=options["wordset/id"], mode=options["mode"], duration=options["duration"], seed=options["seed"]
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
        self.logger.info(f"Finished game {self.game.get_stats()}")

    def finish_game(self, save: bool = False) -> None:
        self.logger.debug("Trying to finish game?")
        if not self.game.finish_or_pause(save=save):
            return None
        self.words_to_type_label.formattedCharList.clear()
        self.words_to_type_label.line_pos = 0
        self.update_timer.stop()
        # self.game.save()
        self.show_popup(self.gamestats_window)
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
