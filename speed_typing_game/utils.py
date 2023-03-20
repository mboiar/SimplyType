import json
import logging
import os
from datetime import datetime as dt

import speed_typing_game.config as config

logger = logging.getLogger(__name__)


def set_stylesheet(app, palette_name, theme):
    palette = get_color_palette(palette_name, theme)
    template_path = os.path.join(config.RESOURCES_DIR, "styles", "template.css")
    with open(template_path, "r") as main_f:
        style_sheet = main_f.read()
        for color_var in palette.keys():
            style_sheet = style_sheet.replace(
                f"var({color_var})", '"' + palette[color_var] + '"'
            )
        logger.info(f"Set palette: {palette_name}")
        app.setStyleSheet(style_sheet)

def get_color_palette_names(theme):
    theme_path = os.path.join(config.RESOURCES_DIR, "styles", theme)
    palette_names = [d for d in os.listdir(theme_path)]
    logger.debug(f"Retrieved available palette names for {theme} theme: {palette_names}")
    return palette_names

def get_color_palette(palette_name, theme):
    palette_path = os.path.join(config.RESOURCES_DIR, "styles", theme, palette_name, "colors.json")
    if not os.path.exists(palette_path):
        raise FileNotFoundError(f"Palette {palette_name} with theme {theme} does not exist.")
    else:
        with open(palette_path, "r") as f:
            return json.load(f)


def setup_logging(log_destination, log_level):
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


def detect_dark_theme_os():
    themes = ["dark", "light"]
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
