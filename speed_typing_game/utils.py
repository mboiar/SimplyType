"""
Define utility functions.

Functions:

    set_stylesheet(QApplication, str, str) -> None
    get_color_palette_names(List[str]) -> List[str]
    get_color_palette(str, str) -> Dict
    setup_logging(str, Union[int, str]) -> None
    create_connection(str) -> bool
    detect_dark_theme_os() -> str

"""

import json
import logging
import os
import sys
from datetime import datetime as dt
from typing import Dict, List, Tuple, Union, Optional
from functools import lru_cache

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtCore import QObject, QLocale
from PyQt6.QtWidgets import QMessageBox

import speed_typing_game.config as config

logger = logging.getLogger(__name__)


def set_stylesheet(
    object: QObject, theme: str, palette_name: Optional[str] = None
) -> None:
    """Set stylesheet with a given palette on the widget."""
    palette_name, palette = get_color_palette(theme, palette_name)
    logger.debug(
        f"Attempting to set color palette of {object} to '{palette_name}' ({theme})"
    )
    template_path = os.path.join(
        config.RESOURCES_DIR, "styles", "template.css"
    )
    with open(template_path, "r") as main_f:
        style_sheet = main_f.read()
        for color_var in palette.keys():
            style_sheet = style_sheet.replace(
                f"var({color_var})", '"' + palette[color_var] + '"'
            )
        logger.info(f"Set palette: {palette_name}")
        object.setStyleSheet(style_sheet)
    window_color = QColor(palette["--background-color"])
    window_text_color = QColor(palette["--foreground-color"])
    button_color = QColor(palette["--background-color"])
    bright_text_color = QColor(palette["--standout-color"])
    base_color = QColor(palette["--background-color"])
    highlight_color = QColor(palette["--error-color"])
    button_text_color = QColor(palette["--foreground-selected-color"])

    current_palette = object.palette()
    current_palette.setColorGroup(
        current_palette.currentColorGroup(),
        window_text_color,
        button_color,
        button_color,
        button_color,
        button_color,
        window_text_color,
        bright_text_color,
        base_color,
        window_color,
    )
    current_palette.setColor(
        current_palette.currentColorGroup(),
        QPalette.ColorRole.Highlight,
        highlight_color,
    )
    current_palette.setColor(
        current_palette.currentColorGroup(),
        QPalette.ColorRole.ButtonText,
        button_text_color,
    )
    object.setPalette(current_palette)

# @lru_cache(maxsize=4)
def get_color_palette_names(themes: List[str] = None) -> List[str]:
    """Retrieve available palette names for given themes."""
    palette_names = []
    for dir in os.scandir(os.path.join(config.RESOURCES_DIR, "styles")):
        if dir.is_dir() and (themes is None or dir.name in themes):
            palette_names.extend([file.name for file in os.scandir(dir.path)])
    logger.debug(f"Palette names for {themes} : {palette_names}")
    return palette_names

def get_theme_by_palette_name(palette_name: str) -> Optional[str]:
    for dir in os.scandir(os.path.join(config.RESOURCES_DIR, "styles")):
        if dir.is_dir() and palette_name in [d.name for d in os.scandir(dir)]:
            logger.debug(f"Theme for {palette_name} : {dir.name}")
            return dir.name
    logger.debug(f"Could not retrieve theme for {palette_name}")
    return None

# @lru_cache(maxsize=10)
def get_color_palette(theme: str, palette_name: Optional[str] = "") -> Tuple[str, Dict]:
    """Retrieve a dict with colors for a given palette name."""
    if not palette_name or not os.path.exists(
        os.path.join(
            config.RESOURCES_DIR, "styles", theme, palette_name, "colors.json"
        )
    ):
        logger.debug(f"Trying to set theme {theme}")

        palette_names = get_color_palette_names([theme])
        if palette_names:
            default_palette_name = palette_names[0]
        else:
            return None
        logger.debug(
            f"Palette {palette_name} with theme {theme} does not exist.\n\
                Using default palette {default_palette_name} ({theme})."
        )
        palette_name = default_palette_name
    palette_path = os.path.join(
        config.RESOURCES_DIR, "styles", theme, palette_name, "colors.json"
    )
    with open(palette_path, "r") as f:
        return (palette_name, json.load(f))


def setup_logging(log_destination: str, log_level: Union[int, str]) -> None:
    """Setup console and/or file loggers to be used throughout application."""
    timestamp = dt.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(config.LOG_DIR, f"{timestamp}.log")
    handlers: List[logging.Handler] = []
    if log_destination in ["console", "both"]:
        handlers.append(logging.StreamHandler())
    if log_destination in ["file", "both"]:
        if not os.path.exists(config.LOG_DIR):
            os.makedirs(config.LOG_DIR)
        handlers.append(logging.FileHandler(filename=log_filename, mode="x"))

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=log_level,
        handlers=handlers,
    )

def display_error(text: str, text_verbose: str, critical: bool = True) -> None:
    msg = QMessageBox()
    if critical:
        icon = QMessageBox.Icon.Critical
    else:
        icon = QMessageBox.Icon.Warning
    msg.setIcon(icon)
    msg.setText(text)
    msg.setInformativeText(text_verbose)
    msg.setWindowTitle(text)
    msg.exec()
    if critical:
        sys.exit(1)

def create_connection(db_name: str, con_name: str) -> bool:
    """Create and open a SQLite database connection."""
    con = QSqlDatabase.addDatabase("QSQLITE", con_name)
    con.setDatabaseName(db_name)
    logger.info(f"Trying to open database connection {db_name}")
    if not con.open():
        logger.error(f"Database Error: {con.lastError().databaseText()}")
        display_error("Database Error", f"Could not open database {db_name}: {con.lastError().databaseText()}")
    return True

@lru_cache
def get_supported_locale() -> List[str]:
    translation_path = os.path.join(config.RESOURCES_DIR, "translate")
    locale_names = [
        n.removesuffix(".qm")
        for n in os.listdir(translation_path)
        if n.endswith(".qm")
    ] + ["en_US"]
    logger.debug(f"Retrieved available locale names: {locale_names}")
    return locale_names

def locale_to_language_name(locale_name: str) -> QLocale.Language:
    return QLocale(locale_name).language()

def detect_dark_theme_os() -> str:
    """Attempt to determine if user's OS theme is dark (default: dark)."""
    themes = ["light", "dark"]
    # TODO: other platforms
    is_dark_theme = True
    try:
        import winreg
    except ImportError:
        logger.debug(f"Detected theme: {themes[is_dark_theme]}")
        return themes[is_dark_theme]
    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    reg_keypath = (
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    )
    try:
        reg_key = winreg.OpenKey(registry, reg_keypath)
        for i in range(1024):
            try:
                value_name, value, _ = winreg.EnumValue(reg_key, i)
                if value_name == "AppsUseLightTheme":
                    is_dark_theme = value
            except OSError:
                break
    except FileNotFoundError:
        pass
    logger.debug(f"Detected theme: {themes[is_dark_theme]}")
    return themes[is_dark_theme]
    # MacOS
    # cmd = 'defaults read -g AppleInterfaceStyle'
    # p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
    #                      stderr=subprocess.PIPE, shell=True)
    # return bool(p.communicate()[0])

    # GTK
    # getArgs = ['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-theme']
    # currentTheme = subprocess.run(
    #     getArgs, capture_output=True
    # ).stdout.decode("utf-8").strip().strip("'")
    # darkIndicator = '-dark'
    # if currentTheme.endswith(darkIndicator):
    #     return True
    # return False
