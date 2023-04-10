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
import time

import PyQt6.QtCore as QtCore
import PyQt6.QtGui as QtGui
from PyQt6.QtCore import QCoreApplication, QSettings, Qt, QUrl
from PyQt6.QtGui import (QCursor, QDesktopServices, QFontMetrics, QIcon,
                         QKeyEvent, QMouseEvent, QPixmap, QResizeEvent)
from PyQt6.QtWidgets import (QButtonGroup, QFileDialog, QGridLayout, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QListView,
                             QPushButton, QVBoxLayout, QWidget, QAbstractButton)
from PyQt6 import QtWidgets
from PyQt6 import QtSql
import pyqtgraph as pg

from speed_typing_game import config, models, database, utils
from speed_typing_game.models import TypingGame
from speed_typing_game.utils import set_stylesheet
from speed_typing_game import main


class MainTypingArea(QLineEdit):
    """A class representing a typing area in the game."""

    def __init__(
        self,
        label: "TypingHintLabel",
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
        game: models.TypingGame = self.parent().game
        char = text[-1]
        pos = game.pos
        char_correct = game.text[pos]
        self.logger.debug(
            f"Typed in '{char}' - correct answer'{char_correct}'\
 - position {pos}"
        )
        self.setText("")
        underline = False
        if char_correct == char:  # correct character typed
            color = self.palette().buttonText().color().name()
            game.pos += 1
        else:  # incorrect character typed
            game.incorrect_chars.update(char_correct)
            if game.mode == models.Mode.LEARNING:
                return None
            game.pos += 1
            color = self.palette().highlight().color().name()
            if char_correct == " ":
                char = " "
                underline = True
            else:
                char = char_correct
        new_char = self.set_html_color(char, color, underline)
        # self.typed_in.append(new_char)
        self.label.formattedCharList += [new_char]
        # new_text = "".join(self.label.formattedCharList) + game.text[game.pos :]
        if (
            self.parent().game.pos % int(self.label.char_line_width) == 0
        ):
            self.label.newline()
        else:
            self.label.setCharList()

    @staticmethod
    def set_html_color(text: str, color: str, underline: bool = False) -> str:
        if underline:
            return f'<span style="color: {color}; text-decoration: {color} underline">{text}</span>'
        else:
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


class PopupWidget(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.logger = logging.getLogger(__name__)
        self.setWindowFlags(QtCore.Qt.WindowFlags.Popup | QtCore.Qt.WindowFlags.FramelessWindowHint)

        self.sizePolicy().setHorizontalPolicy(QtWidgets.QSizePolicy.Policy.Minimum)
        # self.sizePolicy().setVerticalPolicy(QtWidgets.QSizePolicy.Policy.Minimum)

        self.setContentsMargins(40, 20, 40, 40)
        self.close_btn = QPushButton(self)
        self.close_btn.setText("x")
        self.close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        font = QtGui.QFont()
        font.setPixelSize(14)
        font.setBold(True)
        self.close_btn.setFont(font)
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self._onclose)
        self.SIGNALS = TranslucentWidgetSignals()

    def resizeEvent(self, event: QResizeEvent) -> None:
        p_g: QtCore.QRect = self.parent().geometry()
        s_g = self.geometry()
        self.move(p_g.x()+p_g.width()*0.5-s_g.width()*0.5, p_g.y()+p_g.height()*0.5-s_g.height()*0.5)

        ow = int(s_g.x() + s_g.width()-self.close_btn.width()-15)
        oh = int(s_g.y())
        self.close_btn.move(ow, oh)

    def _onclose(self):
        self.logger.debug(f"Closed pop-up {self}")
        self.SIGNALS.CLOSE.emit()
        
    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self._onclose()
        
    def show(self) -> None:
        self.fillColor = self.palette().window().color().lighter(120)
        self.penColor = self.palette().windowText().color().darker(120)
        self.setStyleSheet(f"""PopupWidget {{
                                        border: 4px solid {self.palette().text().color().name()};
                                        border-radius: 5px;
                                        background: {self.fillColor.name()};
                                        color: {self.penColor.name()}
        }}
        QWidget {{
            background: {self.fillColor.name()}
        }}""")
        return super().show()


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

class SettingsMenu(PopupWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()
        
    def show(self) -> None:
        if QtCore.QSettings().value("styles/theme") == "dark":
            self.theme_switch.setChecked(True)
        current_locale = QSettings().value("localization/locale")
        current_language_idx = self.languages.index(utils.locale_to_language_name(current_locale))
        self.language_box.setCurrentIndex(current_language_idx)
        self.adjustSize()
        super().show()

    def initUI(self) -> None:
        self.setLayout(QGridLayout())
        self.layout().setVerticalSpacing(30)
        self.layout().setHorizontalSpacing(50)
        self.theme_switch = Switch()
        self.theme_switch.clicked.connect(self.toggle_theme)
        self.theme_switch_label = QLabel()
        self.theme_switch.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.languages = [utils.locale_to_language_name(l) for l in utils.get_supported_locale()]
        self.logger.debug(f"{self.languages}")
        language_names = [QtCore.QLocale.languageToString(l) for l in self.languages]
        self.language_model = QtCore.QStringListModel()
        self.language_model.setStringList(language_names)
        settings = QtCore.QSettings()
        current_locale = settings.value("localization/locale")
        self.logger.debug(f"Current locale: {current_locale}")
        current_language_idx = self.languages.index(utils.locale_to_language_name(current_locale))
        self.logger.debug(f"Current language: {current_language_idx}")
        self.language_box = QtWidgets.QComboBox()
        self.language_box.setModel(self.language_model)
        self.language_box.setCurrentIndex(current_language_idx)
        self.language_box.currentIndexChanged.connect(lambda idx: self.set_language(self.languages[idx]))

        self.language_selector_label = QLabel()
        for i, widgets in enumerate([
            (self.theme_switch_label, self.theme_switch),
            (self.language_selector_label, self.language_box)
        ]):
            self.layout().addWidget(widgets[0], i, 0)
            # self.layout().spacerItem()
            self.layout().addWidget(widgets[1], i, 1)
        self.retranslateUI()
        
    def set_language(self, language: QtCore.QLocale.Language) -> None:
        # translator = QtCore.QTranslator()
        locale = QtCore.QLocale(language)
        # if locale == config.DEFAULT_LOCALE:
            # QCoreApplication.removeTranslator()
        QSettings().setValue("localization/locale", locale)
        main.restart_app()
        # elif translator.load(locale.name() + ".qm", config.RESOURCES_DIR + "/translate/"):
            # QCoreApplication.instance().installTranslator(translator)
        # else:
            # self.logger.error(f"Could not install translator for '{locale}'")

    def toggle_theme(self) -> None:
        settings = QSettings("BoiarTech", config.PROJECT_NAME)
        themes = ["light", "dark"]
        theme = themes[self.theme_switch.isChecked()]
        set_stylesheet(
            QCoreApplication.instance(), theme
        )
        self.parent().repaint()
        QtCore.QSettings().setValue("styles/theme", theme)

    def retranslateUI(self) -> None:
        self.theme_switch_label.setText(
            QCoreApplication.translate("QLabel", "Use dark scheme")
        )
        self.language_selector_label.setText(
            QCoreApplication.translate("QLabel", "Select language")
        )


class WordsetFileSelectWindow(PopupWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        self.setLayout(QGridLayout())

        self.wordset_from_file_button = QPushButton("Choose file containing wordset", self)
        self.wordset_from_file_button.clicked.connect(self.get_set_wordset)
        self.wordset_from_file_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.error_label = QLabel()
        self.error_label.setProperty("class", "error-text")
        self.save_to_database_checkbox = QtWidgets.QCheckBox(self)
        self.save_to_database_label = QLabel(self)
        self.layout().addWidget(self.wordset_from_file_button, 0, 0, 1, 3, Qt.Alignment.AlignCenter)
        self.layout().addWidget(self.error_label, 1, 0, 1, 3)
        self.layout().addWidget(self.save_to_database_label, 2, 0, 1, 2)
        self.layout().addWidget(self.save_to_database_checkbox, 2, 2, 1, 1)
        self.layout().setSpacing(20)

        self.wordset_from_file_button.setMaximumSize(200, 20)
        self.error_label.setMaximumSize(200, 20)
        self.save_to_database_label.setMaximumSize(150, 20)
        self.retranslateUI()
        
    def resizeEvent(self, event: QResizeEvent) -> None:
        # self.setFixedSize(200,300)
        # self.adjustSize()
        return super().resizeEvent(event)

    def show(self) -> None:
        self.adjustSize()
        return super().show()

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
                self.parent().menu1_popup.set_wordset(wordset, self.save_to_database_checkbox.isChecked())
                self._onclose()
            
    
    def retranslateUI(self) -> None:
        self.save_to_database_label.setText(
            QCoreApplication.translate("QLabel", "Add wordset to database")
        )


class WordsetMenu(PopupWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()
        
    def show(self) -> None:
        self.adjustSize()
        super().show()

    def initUI(self) -> None:
        self.setLayout(QVBoxLayout())
        con_name = config.CON_NAME
        wordset_tablename = config.WORDSET_TABLE
        self.db = QtSql.QSqlDatabase.database(con_name)
        if not self.db.open():
            self.logger.error(f"Could not open database connection {con_name}")
            utils.display_error("Database Error", f"Could not open database connection '{con_name}'")

        self.model = QtSql.QSqlQueryModel()
        self.model.setQuery("SELECT name, id FROM wordsets", self.db)
        self.view = QtWidgets.QListView()
        self.view.setItemAlignment(Qt.Alignment.AlignVCenter | Qt.Alignment.AlignHCenter)
        self.view.setModel(self.model)
        self.view.setMaximumWidth(150)
        self.view.setMaximumHeight(self.parent().height()*0.5)
        # if QSettings().contains("game/options/wordset"):
        #     ix = 1 # TODO
        #     self.view.selectionModel().select(ix, QtCore.QItemSelectionModel.SelectionFlags.SelectCurrent)
        self.view.selectionModel().selectionChanged.connect(self.select_wordset_from_list)
        self.wordset_from_file_button = QPushButton("Custom")
        self.wordset_from_file_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.wordset_from_file_button.setMaximumWidth(100)
        self.layout().setSpacing(5)
        # self.view.setMaximumWidth(300)
        # self.view.setMaximumHeight(self.parent().geometry().height()*0.5)
        # self.view.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
        self.wordset_from_file_window = WordsetFileSelectWindow(self.parent())
        self.wordset_from_file_button.clicked.connect(lambda: self.parent().show_popup(self.wordset_from_file_window))
        for _, widgets in enumerate([
            (self.view),
            (self.wordset_from_file_button),
        ]):
            self.layout().addWidget(widgets)
            # self.layout().setAlignment(widgets, Qt.Alignment.AlignJustify)
            # self.layout().spacerItem()
            # self.layout().addWidget(widgets[1], i, 1)
        self.view.adjustSize()
        self.retranslateUI()

    def set_wordset(self, wordset: models.Wordset, add_to_database: bool = False) -> None:
        settings = QSettings()
        set_wordset = False
        if wordset.id:
            settings.setValue("game/options/wordset/id", wordset.id)
            self.logger.info(f"Wordset id: {settings.value('game/options/wordset/id')}")
            set_wordset = True
        elif wordset.name:
            settings.setValue("game/options/wordset/name", wordset.name)
            set_wordset = True

        if set_wordset:
            self.logger.info(f"Set default wordset {wordset}")
            if add_to_database:
                wordset.save()
        else:
            self.logger.error(f"Could not set wordset: wordset {wordset} has incomplete data")
        self._onclose()
        self.parent().init_game(wordset=wordset)
        self.parent().set_focus()

    def select_wordset_from_list(self) -> None:
        ix = self.view.selectionModel().currentIndex().row()
        wordset_id = self.model.record(ix).value("id")
        QSettings().setValue("game/options/wordset/id", wordset_id)
        self.logger.info(f"Set default wordset {wordset_id}")
        self._onclose()
        self.parent().init_game()

    def retranslateUI(self) -> None:
        pass
        # self.duration_selector_label.setText(
        #     QCoreApplication.translate("QLabel", "Select duration")
        # )


class AboutWindow(PopupWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        self.setLayout(QGridLayout())
        self.about_label = QLabel()

        for i, widgets in enumerate([
            (self.about_label),
        ]):
            self.layout().addWidget(widgets, i, 0, 1, 1, Qt.Alignment.AlignCenter)
            # self.layout().spacerItem()
            # self.layout().addWidget(widgets[1], i, 1)
        self.about_label.setMaximumSize(200, 20)
        self.retranslateUI()

    def show(self) -> None:
        # self.setFixedSize(200,300)
        self.adjustSize()
        super().show()
        # return super().resizeEvent(event)

    def retranslateUI(self) -> None:
        self.about_label.setText(
            QCoreApplication.translate("QLabel", f"About {config.PROJECT_NAME}")
        )


class UserStatsWindow(PopupWidget):
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
        if self.avg_stats:
            self.acc_data.setText(f"{self.avg_stats[0]:.2f}%")
            self.wpm_data.setText(f"{self.avg_stats[1]:.2f} wpm")
        self.adjustSize()
        super().show()        

    def initUI(self) -> None:
        self.setLayout(QGridLayout())
        self.title = QLabel()
        self.title.setProperty("class", "heading")
        self.acc_label = QLabel(QCoreApplication.translate("QLabel", "Average accuracy"))
        self.wpm_label = QLabel(QCoreApplication.translate("QLabel", "Average speed"))
        self.acc_data = QLabel()
        self.wpm_data = QLabel()
        for i, widgets in enumerate([
            (self.title, ),
            (self.acc_label, self.acc_data),
            (self.wpm_label, self.wpm_data)
        ]):
            for j, widget in enumerate(widgets):
                widget.setMaximumSize(200, 20)
                self.layout().addWidget(widget, i, j, Qt.Alignment.AlignCenter)
        self.retranslateUI()

    def get_game_data(self) -> Optional[List[Tuple[float, float, float, str]]]:
        return database.get_game_data()

    def retranslateUI(self) -> None:
        self.title.setText(
            QCoreApplication.translate("QLabel", "User statistics")
        )


class GameStatsWindow(PopupWidget):
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
        self.adjustSize()
        super().show()

    def initUI(self) -> None:
        self.setLayout(QGridLayout())

        self.title = QLabel()
        self.wpm_label = QLabel()
        self.wpm_data = QLabel()
        self.accuracy_label = QLabel()
        self.accuracy_data = QLabel()
        self.incorrect_chars_label = QLabel()
        self.incorrect_chars_data = QLabel()
        self.button_continue = QPushButton("Continue")
        self.button_continue.clicked.connect(self.close_btn.click)
        self.button_continue.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        for i, widgets in enumerate([
            (self.title,),
            (self.wpm_label, self.wpm_data),
            (self.accuracy_label, self.accuracy_data),
            (self.incorrect_chars_label, self.incorrect_chars_data),
            (self.button_continue,)
        ]):
            for j, widget in enumerate(widgets):
                self.layout().addWidget(widget, i, j, Qt.Alignment.AlignCenter)
                widget.setMaximumSize(200, 20)
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

class PauseMenu(PopupWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        self.setLayout(QVBoxLayout())

        self.label = QLabel()
        self.exit_button = QPushButton()
        self.resume_button = QPushButton()
        self.settings_button = QPushButton()
        self.resume_button.clicked.connect(self._onclose)
        self.exit_button.clicked.connect(self.parent().close)
        self.settings_button.clicked.connect(lambda: self.parent().show_popup(self.parent().settings_menu))
        self.resume_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.exit_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.settings_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        for _, widget in enumerate([
            self.label,
            self.resume_button,
            self.settings_button,
            self.exit_button
        ]):
            self.layout().addWidget(widget)
            widget.setMaximumWidth(100)
            widget.setMaximumHeight(20)
            # self.layout().setAlignment(widget, Qt.Alignment.AlignCenter)
        self.layout().setSpacing(0)
        self.setFixedSize(200,300)
        self.retranslateUI()

    def retranslateUI(self) -> None:
        self.label.setText(
            QCoreApplication.translate("QLabel", "Game paused")
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

    def show(self) -> None:
        self.adjustSize()
        return super().show()

class DurationMenu(PopupWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        self.setLayout(QVBoxLayout())
        self.duration_list = [30, 60, 120, 180, 300, -1]
        self.duration_model = QtCore.QStringListModel()
        sec_ = QCoreApplication.translate("QString", "s")
        min_ = QCoreApplication.translate("QString", "min.")
        inf_ = QCoreApplication.translate("QString", "Infinite")
        self.duration_model.setStringList([f"{i/60:.0f} {min_}" if i >= 60 else (f"{i} {sec_}" if i >=0 else inf_) for i in self.duration_list])
        settings = QtCore.QSettings()
        current_duration = settings.value("game/options/duration")
        self.logger.debug(f"Current duration: {current_duration}")
        self.duration_view = QtWidgets.QListView()
        self.duration_view.setItemAlignment(Qt.Alignment.AlignVCenter | Qt.Alignment.AlignHCenter)
        self.duration_view.setMaximumWidth(100)

        self.duration_view.setModel(self.duration_model)
        self.duration_view.selectionModel().selectionChanged.connect(lambda ix: self.set_duration(self.duration_list[ix.indexes()[0].row()]))
        for _, widgets in enumerate([
            (self.duration_view),
        ]):
            self.layout().addWidget(widgets)
        self.retranslateUI()

    def set_duration(self, duration: int) -> None:
        settings = QSettings()
        settings.setValue("game/options/duration", duration)
        self.logger.info(f"Set duration {duration}")
        self._onclose()
        self.parent().init_game()

    def show(self) -> None:
        self.adjustSize()
        return super().show()

    def retranslateUI(self) -> None:
        pass


class ModeMenu(PopupWidget):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.initUI()

    def initUI(self) -> None:
        self.setLayout(QVBoxLayout())
        self.mode_list = [i for i in models.Mode]
        self.mode_model = QtCore.QStringListModel()
        self.mode_model.setStringList(self.mode_list)
        settings = QtCore.QSettings()
        current_mode = settings.value("game/options/mode")
        self.logger.debug(f"Current duration: {current_mode}")
        self.mode_view = QtWidgets.QListView()
        self.mode_view.setItemAlignment(Qt.Alignment.AlignVCenter | Qt.Alignment.AlignHCenter)
        self.mode_view.setMaximumWidth(100)
        self.mode_view.setModel(self.mode_model)
        self.mode_view.selectionModel().selectionChanged.connect(lambda ix: self.set_mode(ix.indexes()[0].row()))
        for _, widgets in enumerate([
            (self.mode_view),
        ]):
            self.layout().addWidget(widgets)
        self.retranslateUI()

    def set_mode(self, mode: int) -> None:
        settings = QSettings()
        settings.setValue("game/options/mode", mode)
        self.logger.info(f"Set mode {mode}")
        self._onclose()
        self.parent().init_game()

    def show(self) -> None:
        self.adjustSize()
        return super().show()

    def retranslateUI(self) -> None:
        pass


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
        # self.redraw()

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
            utils.display_error("Internal Error", f"Internal Error")

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

    def resizeEvent(self, event: QtCore.QEvent) -> None:
        """Change displayed word count if width/font changed"""
        super().resizeEvent(event)
        # self.adjustSize()
        self.label_width = self.geometry().width()
        max_px_length = self.label_width * self.num_lines
        self.max_chars = (
            max_px_length/self.fontMetrics().averageCharWidth() - 5*2
        )  # TODO self.fontMetrics().boundingRectChar("m").width()
        self.char_line_width = self.label_width - 5
        self.logger.debug(
            f"Max chars: {self.max_chars}; label width: {self.label_width}; px_length: {max_px_length}; font width {self.fontMetrics().averageCharWidth()}"
        )
        self.setCharList()

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
        # self.timer = QtCore.QTimer()
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.finish_game)
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_timer_label)
        self.icon = icon
        self.timer_id = 0
        self.settings = QSettings()
        self.game = TypingGame(
            wordset_id=self.settings.value("game/options/wordset/id"),
            duration=self.settings.value("game/options/duration"),
            mode=self.settings.value("game/options/mode")
        )
        self.remaining_time = self.game.duration
        self.init_window()

    def init_window(self) -> None:
        """Initialize main window GUI"""
        self.logger.debug("Initializing main window")
        self.resize(900, 500)
        self.setWindowTitle(config.PROJECT_NAME)
        self.setWindowIcon(self.icon)

        self.mainLayout = QGridLayout()
        self.setLayout(self.mainLayout)
        self.title = QLabel(
            f"<font color='{self.palette().brightText().color().name()}'>Simply</font>Type"
        )
        self.title.setProperty("class", "heading")
        self.timer_label = QLabel(self)
        sp_retain = self.timer_label.sizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        self.timer_label.setSizePolicy(sp_retain)
        self.timer_label.setObjectName("timer_label")
        self.timer_label.setProperty("class", "highlighted")

        self.words_to_type_label = TypingHintLabel(self)
        self.words_to_type_label.setWordWrap(True)
        self.words_to_type_label.setProperty("class", "words_to_type")
        self.words_to_type_label.setAlignment(Qt.Alignment.AlignJustify)
        # self.words_to_type_label.setText(self.game.text)

        self.words_input = MainTypingArea(
            self.words_to_type_label, allow_takeback=False, parent=self
        )
        self.words_input.textEdited.connect(self.words_input._textEdited)
        self.button_reset = QPushButton()
        self.button_reset.setMaximumWidth(100)

        self.sidebarLayout = QVBoxLayout()
        self.button_settings = QPushButton()
        self.settings_menu = SettingsMenu(self)
        pixmapi = QtWidgets.QStyle.StandardPixmap.SP_MediaPause
        # mask = pixmapi.createMaskFromColor(QtGui.QColor('blue'), Qt.MaskMode.MaskOutColor)
        # pixmapi.setMask(mask)
        option = QtWidgets.QStyleOption()
        option.palette = self.palette()
        icon = self.style().standardIcon(pixmapi, option)
        self.button_pause = QPushButton(self)
        # self.button_pause.setIcon(icon)
        # self.button_pause.setStyleSheet(f"""
                                        # border: 1px solid {self.palette().text().color().name()};
                                        # border-radius: 40px;
                                        # color: {self.palette().text().color().name()};
                                        # """)
        self.button_pause.setText(QCoreApplication.translate("QPushButton", "PAUSE"))
        self.pause_menu = PauseMenu(self)
        self.gamestats_window = GameStatsWindow(self)
        self.button_about = QPushButton()
        self.about_popup = AboutWindow(self)
        self.button_stats = QPushButton()
        self.button_stats.setProperty("class", "highlighted")
        self.stats_popup = UserStatsWindow(self)
        self.button_exit = QPushButton()

        self.menuLayout = QVBoxLayout()
        self.menuLayout.setSpacing(10)

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
        self.mainLayout.setContentsMargins(20, 20, 20, 20)
        self.mainLayout.setVerticalSpacing(20)
        self.mainLayout.addWidget(self.title, 0, 0, Qt.Alignment.AlignLeft)

        self.mainLayout.setRowMinimumHeight(1, 100)

        self.mainLayout.addWidget(self.button_pause, 0, 2, Qt.Alignment.AlignRight)
        self.mainLayout.addWidget(self.timer_label, 1, 0)
        self.timer_label.setFixedHeight(60)
        self.words_input.setFixedHeight(60)

        self.mainLayout.addWidget(self.words_input, 1, 1)
        self.mainLayout.addWidget(self.words_to_type_label, 2, 0, 1, 3)
        self.mainLayout.addWidget(self.button_reset, 3, 1, Qt.Alignment.AlignCenter)
        self.mainLayout.addWidget(self.description_label, 4, 1, Qt.Alignment.AlignCenter)

        self.sidebarLayout = QVBoxLayout()
        self.sidebarLayout.setSpacing(10)
        self.sidebarLayout.addWidget(self.button_settings)
        self.sidebarLayout.addWidget(self.button_about)
        self.sidebarLayout.addWidget(self.button_stats)
        self.sidebarLayout.addWidget(self.button_exit)
        self.sidebarLayout.addWidget(self.link_github)

        self.mainLayout.addLayout(self.menuLayout, 5, 0)
        self.mainLayout.addLayout(self.sidebarLayout, 5, 2)

        self.button_reset.clicked.connect(self.reset_game)
        self.button_exit.clicked.connect(self.close)
        self.words_to_type_label.mousePressEvent = self.set_focus
        self._popframes: List[PopupWidget] = []
        self._popflag = False

        self.retranslate()

    @staticmethod
    def open_hyperlink(linkStr: str) -> bool:
        return QDesktopServices.openUrl(QUrl(linkStr))

    def set_focus(self, event: QMouseEvent = None) -> None:
        self.words_input.setFocus()

    def resizeEvent(self, event):
        self.words_to_type_label.resizeEvent(event)

    def show_popup(self, popup: PopupWidget) -> None:
        self.logger.info(f"Showing popup {popup}")
        popup.move(0, 0)
        popup.resize(self.width(), self.height())
        popup.SIGNALS.CLOSE.connect(self._closepopup)
        # if not self._popflag:
            
        self._popflag = True
        self.pause_timer(reset=True)
        popup.show()
        self._popframes.append(popup)

    def _closepopup(self) -> None:
        if not self._popframes:
            return None
        popup = self._popframes.pop()
        self.logger.info(f"Closing popup {popup}")

        popup.close()
        self._popflag = False
        self.set_focus()
        self.pause_timer()

    def reset_game(self) -> None:
        self.logger.debug("Reset game")
        self.remaining_time = 0
        self.game.finish_or_pause(save=False)
        self.words_to_type_label.formattedCharList.clear()
        self.words_to_type_label.line_pos = 0
        self.words_to_type_label.min_char_pos = 0
        # self.words_to_type_label.setCharList()
        if self.game.duration != -1:
            if self.update_timer.isActive():
                self.update_timer.stop()
            if self.timer.isActive():
                self.timer.stop()
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
        self.timer_label.setText("")

        self.description_label.show()
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
        self, wordset_id: Optional[int] = None, 
        mode: Optional[str] = None, duration: Optional[int] = None, 
        seed: Optional[int] = None, wordset_name: Optional[str] = None,
        wordset: Optional[models.Wordset] = None
    ) -> None:
        settings = QSettings()

        options = {
            "wordset/id":wordset_id, 
            "mode":mode, 
            "duration":duration, 
            "seed":seed, 
            "wordset/name":wordset_name
        }
        for (option, val) in options.items():
            if val is None and settings.contains(f"game/options/{option}"):
                options[option] = settings.value(f"game/options/{option}")
                self.logger.debug(f"Retrieved '{option}' from settings: {val}")
        self.logger.debug(f"Received wordset: {wordset}")

        self.game = TypingGame(
            wordset_id=options["wordset/id"] if not wordset else None, 
            mode=options["mode"], 
            duration=options["duration"], 
            seed=options["seed"],
            wordset=wordset)
        self.words_to_type_label.min_char_pos = self.game.pos
        self.logger.debug(f"Setting starting label position {self.game.pos}")
        self.words_to_type_label.setCharList()
        self.remaining_time = self.game.duration
        self.set_focus()

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
        # self.timer_label.show()

        if self.game.duration != -1:
            self.logger.debug(f"Setting timer for {self.game.duration//1000} s")
            self.timer.start(self.game.duration)
            self.update_timer.start(100)
        else:
            # pass
            self.timer_label.setText("")

        self.game.start_or_resume()

    def display_results(self) -> None:
        self.logger.info(f"Finished game {self.game.get_stats()}")

    def pause_timer(self, reset: bool = None) -> None:
        if self.game.duration != -1:
            self.logger.debug(f"Timer active: {self.timer.isActive()}; popup open: {self._popflag}; game in progress: {self.game.in_progress}")
            if self.timer.isActive() and self.game.in_progress:
                self.game.finish_or_pause()
                self.remaining_time = self.timer.remainingTime()
                self.logger.debug(f"Pause: {self.remaining_time/1000:.3f}/{self.game.duration//1000} s")
                self.update_timer.stop()
                self.timer.stop()
            elif self._popflag == False and not self.game.in_progress and self.game.elapsed > 0:
                self.game.start_or_resume()
                self.logger.debug(f"Resume: {self.remaining_time/1000:.3f}/{self.game.duration//1000} s")

                self.timer.start(self.remaining_time)
                self.update_timer.start()

    def finish_game(self, save: bool = True) -> None:
        self.remaining_time = 0
        if not self.game.finish_or_pause(save=save):
            return None
        self.words_to_type_label.formattedCharList.clear()
        self.words_to_type_label.line_pos = 0
        self.words_to_type_label.min_char_pos = 0
        # self.words_to_type_label.setCharList()
        if self.game.duration != -1 and self.update_timer.isActive():
            self.update_timer.stop()
        self.show_popup(self.gamestats_window)
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
        # self.timer_label.hide()
        self.timer_label.setText("")

        self.description_label.show()
        self.set_focus()

    def update_timer_label(self) -> None:
        self.timer_label.setText(str(int(self.timer.remainingTime() // 1000)))

    def repaint(self) -> None:
        super().repaint()
        self.title.setText(
            f"<font color='{self.palette().brightText().color().name()}'>Simply</font>Type"
        )
        # self.button_pause.setStyleSheet(f"""
        #     border: 1px solid {self.palette().text().color().name()};
        #     border-radius: 40px;
        #     color: {self.palette().text().color().name()};
        # """)
        self.button_stats.setProperty("class", "highlighted")
        self.button_stats.setText(QCoreApplication.translate("QPushButton", "Stats"))
        self.link_github.setText(
            f'<a href="{config.PROJECT_URL}" style="text-decoration:none;\
            color:{self.palette().text().color().name()}">{config.PROJECT_VERSION}</a>'
        )
        self.words_to_type_label.setCharList()
        

    def close(self) -> None:
        sys.exit()
