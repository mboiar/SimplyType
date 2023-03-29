"""
Define utility functions.

Functions:

    set_stylesheet(QApplication, str, str) -> None
    get_color_palette_names(str) -> List[str]
    get_color_palette(str, str) -> Dict
    setup_logging(str, Union[int, str]) -> None
    create_connection(str) -> bool
    detect_dark_theme_os() -> str

"""

import json
import logging
import os
from datetime import datetime as dt
from typing import Dict, List, Union, Tuple

from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtWidgets import QWidget, QMessageBox

import speed_typing_game.config as config

logger = logging.getLogger(__name__)


def set_stylesheet(widget: QWidget, theme: str, palette_name: str = None) -> None:
    """Set stylesheet with a given palette on the widget."""
    logger.debug(f"Attempting to set color palette of {widget} to {palette_name} ({theme})")
    palette_name, palette = get_color_palette(theme, palette_name)
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
        widget.setStyleSheet(style_sheet)
    current_palette = widget.palette()
    # TODO: modify palette
    # current_palette.setColorGroup()
    widget.setPalette(current_palette)


def get_color_palette_names(theme: str) -> List[str]:
    """Retrieve available palette names for a dark or light theme."""
    theme_path = os.path.join(config.RESOURCES_DIR, "styles", theme)
    palette_names = [d for d in os.listdir(theme_path)]
    logger.debug(
        f"Retrieved available palette names for {theme} theme: {palette_names}"
    )
    return palette_names


def get_color_palette(theme: str, palette_name: str) -> Tuple[str, Dict]:
    """Retrieve a dict with colors for a given palette name."""
    if not palette_name or not os.path.exists(
        os.path.join(
        config.RESOURCES_DIR, "styles", theme, palette_name, "colors.json"
    )
    ):
        default_palette_name = get_color_palette_names(theme)[0]
        palette_name = default_palette_name
        logger.warning(
            f"Palette {palette_name} with theme {theme} does not exist.\n\
                Using default palette {default_palette_name} ({theme})."
        )
    palette_path = os.path.join(
        config.RESOURCES_DIR, "styles", theme, palette_name, "colors.json"
    )
    with open(palette_path, "r") as f:
        return (palette_name, json.load(f))


def setup_logging(log_destination: str, log_level: Union[int, str]) -> None:
    """Setup console and/or file loggers to be used throughout application."""
    timestamp = dt.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(config.LOG_DIR, f"{timestamp}.log")
    handlers = []
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


def create_connection(db_name: str, con_name: str) -> bool:
    """Create and open a SQLite database connection."""
    con = QSqlDatabase.addDatabase("QSQLITE", con_name)
    con.setDatabaseName(db_name)

    if not con.open():
        QMessageBox.critical(
            None,
            f"{config.PROJECT_NAME} - Error!",
            "Database Error: %s" % con.lastError().databaseText(),
        )
        logger.critical("Unable to connect to the database")
        return False
    return True


def get_supported_locale() -> List[str]:
    translation_path = os.path.join(config.RESOURCES_DIR, "translate")
    locale_names = [
        n.removesuffix(".qm")
        for n in os.listdir(translation_path)
        if n.endswith(".qm")
    ] + ["en_US"]
    logger.debug(f"Retrieved available locale names: {locale_names}")
    return locale_names


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
                    print(value)
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
