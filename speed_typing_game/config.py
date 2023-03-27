"""
Define default project variables.
"""

import logging
import os

PROJECT_NAME = "SimplyType"
PROJECT_URL = "https://github.com/mboiar/speed-typing-game"
PROJECT_VERSION = "v0.1-dev"
ROOT_DIR = "speed_typing_game"
RESOURCES_DIR = os.path.join(ROOT_DIR, "resources")
LOGGING_LEVEL = logging.DEBUG
LOG_DIR = os.path.join(ROOT_DIR, "logs")
TEST_DIR = os.path.join(ROOT_DIR, "tests")
COLOR_THEME = "dark"
DEFAULT_LOCALE = "en_US"
# STATS_DB = os.path.join(RESOURCES_DIR, "stats.sqlite")
DB = os.path.join(RESOURCES_DIR, "db.sqlite")
WORDSET_TABLE = "wordsets"
WORD_TABLE = "words"
CON_NAME = "words"
GAME_TABLE = "games"
