import logging
from functools import lru_cache
from typing import Iterable, List, Tuple, Optional
from collections import Counter
import time
import datetime

from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlQueryModel

from speed_typing_game import config, models, utils

logger = logging.getLogger(__name__)
createWordsetTableQueryString = f"""
            CREATE TABLE IF NOT EXISTS {config.WORDSET_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                name VARCHAR(40) NOT NULL,
                language_code VARCHAR(6) NOT NULL,
                difficulty INTEGER
            )
            """

createWordTableQueryString = f"""
            CREATE TABLE IF NOT EXISTS {config.WORD_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                content VARCHAR(50) NOT NULL,
                wordset_id INTEGER NOT NULL,
                FOREIGN KEY (wordset_id)
                    REFERENCES {config.WORDSET_TABLE}(id)
                    ON DELETE CASCADE,
                UNIQUE(content, wordset_id)
            )
            """

createGameTableQueryString = f"""
            CREATE TABLE IF NOT EXISTS {config.GAME_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                mode VARCHAR(10),
                wordset_id INTEGER,
                seed INTEGER NOT NULL,
                pos INTEGER NOT NULL,
                incorrect_chars TEXT,
                elapsed REAL,
                created_at REAL NOT NULL UNIQUE,
                word_count INTEGER,
                last_updated REAL,
                FOREIGN KEY (wordset_id)
                    REFERENCES {config.WORDSET_TABLE} (id)
                    ON DELETE SET NULL
            );
            """

insertWordsetQueryString = f"""
        INSERT INTO {config.WORDSET_TABLE} (
            name,
            language_code,
            difficulty
        )
        VALUES (?, ?, ?)
        """

insertWordQueryString = f"""
        INSERT INTO {config.WORD_TABLE} (
            content,
            wordset_id
        )
        VALUES (?, ?)
        """

insertGameQueryString = f"""
        INSERT INTO {config.GAME_TABLE} (
            mode,
            wordset_id,
            seed,
            pos,
            incorrect_chars,
            elapsed,
            created_at,
            word_count,
            last_updated
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

deleteWordsetTableQueryStr = """DROP TABLE wordsets"""
deleteWordTableQueryStr = """DROP TABLE words"""
deleteGameTableQueryStr = """DROP TABLE games"""


def delete_game_table() -> bool:
    con_name = config.CON_NAME
    game_tablename = config.GAME_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open database connection '{con_name}'")
        utils.display_error("Database Error", f"Could not open database connection '{con_name}'")
    if True:  # not check_table_exists(wordset_tablename, con_name):
        dropTableQuery = QSqlQuery(db)
        if not dropTableQuery.exec(deleteGameTableQueryStr):
            logger.error(
                f"Unable to delete table '{game_tablename}'\n"
                + dropTableQuery.lastError().text()
            )
            utils.display_error("Database Error", f"Unable to delete table '{game_tablename}'\n"
                + dropTableQuery.lastError().text())
        logger.debug(
            f"Deleted table '{game_tablename}' from {db.databaseName()}"
        )
    return True


def delete_wordset_table() -> bool:
    con_name = config.CON_NAME
    wordset_tablename = config.WORDSET_TABLE
    word_tablename = config.WORD_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open database connection '{con_name}'")
        utils.display_error("Database Error", f"Could not open database connection '{con_name}'")

    if True:  # not check_table_exists(wordset_tablename, con_name):
        dropTableQuery = QSqlQuery(db)
        if not dropTableQuery.exec(deleteWordsetTableQueryStr):
            logger.error(
                f"Unable to delete table '{wordset_tablename}'\n"
                + dropTableQuery.lastError().text()
            )
            utils.display_error("Database Error", f"Unable to delete table '{wordset_tablename}'\n"
                + dropTableQuery.lastError().text()
            )

        if not dropTableQuery.exec(deleteWordTableQueryStr):
            logger.error(
                f"Unable to delete table '{word_tablename}'\n"
                + dropTableQuery.lastError().text()
            )
            utils.display_error("Database Error",
                f"Unable to delete table '{word_tablename}'\n"
                + dropTableQuery.lastError().text())

        logger.debug(
            f"Deleted table '{wordset_tablename}' from {db.databaseName()}"
        )
    return True


def check_table_exists(tablename: str, db_con: str) -> bool:
    return tablename in QSqlDatabase.database(db_con).tables()


def add_wordsets_to_database(wordsets: Iterable["models.Wordset"]) -> bool:
    con_name = config.CON_NAME
    wordset_tablename = config.WORDSET_TABLE
    word_tablename = config.WORD_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open database connection '{con_name}'")
        utils.display_error("Database Error", f"Could not open database connection '{con_name}'")

    if True:  # not check_table_exists(wordset_tablename, con_name):
        createTableQuery = QSqlQuery(db)
        if not createTableQuery.exec(createWordsetTableQueryString):
            logger.error(
                f"Unable to create table '{wordset_tablename}'\n"
                + createTableQuery.lastError().text()
            )
            utils.display_error("Database Error", f"Unable to create table '{wordset_tablename}'\n"
                + createTableQuery.lastError().text())

        logger.debug(
            f"Created/updated table '{wordset_tablename}' in {db.databaseName()}"
        )

    if True:  # not check_table_exists(word_tablename, con_name):
        createTableQuery = QSqlQuery(db)
        if not createTableQuery.exec(createWordTableQueryString):
            logger.error(
                f"Unable to create table '{word_tablename}'\n"
                + createTableQuery.lastError().text()
            )
            utils.display_error("Database Error", f"Unable to create table '{word_tablename}'\n"
                + createTableQuery.lastError().text())

        logger.debug(
            f"Created/updated table '{word_tablename}' in {db.databaseName()}"
        )

    insertWordsetQuery = QSqlQuery(db)
    insertWordsetQuery.prepare(insertWordsetQueryString)
    wordset_ids = []
    word_vals = []
    for wordset in wordsets:
        name, language_code, difficulty = (
            wordset.name,
            wordset.language,
            wordset.difficulty,
        )
        words = wordset.words
        if not words:
            logger.warning(f"Ignoring empty wordset {name}")
            continue
        insertWordsetQuery.addBindValue(name)
        insertWordsetQuery.addBindValue(language_code)
        insertWordsetQuery.addBindValue(difficulty)
        if not insertWordsetQuery.exec():
            logger.error(
                f"Unable to insert wordset data into table '{wordset_tablename}'\n"
                + insertWordsetQuery.lastError().text()
            )
            utils.display_error("Database Error", f"Unable to insert wordset data into table '{wordset_tablename}'\n"
                + insertWordsetQuery.lastError().text())

        logger.info(
            f"Added wordset {name} to table {db.databaseName()}.{wordset_tablename}"
        )
        selectAutoincrIdQueryStr = f"""
            SELECT seq, name FROM sqlite_sequence WHERE name = '{wordset_tablename}';
        """
        selectAutoincrIdQuery = QSqlQuery(db)
        if not selectAutoincrIdQuery.exec(selectAutoincrIdQueryStr):
            logger.error(
                f"Unable to select autoincrement value for table {wordset_tablename}:\n"
                + selectAutoincrIdQuery.lastError().text()
            )
            utils.display_error("Database Error", f"Unable to select autoincrement value for table {wordset_tablename}:\n"
                + selectAutoincrIdQuery.lastError().text())

        selectAutoincrIdQuery.next()
        last_wordset_id = selectAutoincrIdQuery.value(0)
        last_name = selectAutoincrIdQuery.value(1)
        logger.debug(
            f"Wordset autoincrement value: {last_wordset_id} for table {last_name}"
        )
        wordset_ids.extend([last_wordset_id] * len(words))
        word_vals.extend(
            [
                *words,
            ]
        )

    insertWordQuery = QSqlQuery(db)
    insertWordQuery.prepare(insertWordQueryString)
    insertWordQuery.addBindValue(word_vals)
    insertWordQuery.addBindValue(wordset_ids)
    if not insertWordQuery.execBatch():
        logger.error(
            f"Unable to insert words into table '{word_tablename}'\n"
            + insertWordQuery.lastError().text()
        )
        deleteWordsetQueryString = f"""
            DELETE FROM {wordset_tablename}
            WHERE id IN {*wordset_ids,}
        """
        deleteWordsetQuery = QSqlQuery(db)
        if not deleteWordsetQuery.exec(deleteWordsetQueryString):
            logger.error(
                f"Unable to delete wordsets from table '{wordset_tablename}'\n"
                + deleteWordsetQuery.lastError().text()
            )
        logger.info(
            f"Removed wordsets from table {db.databaseName()}.{wordset_tablename}"
        )
        utils.display_error("Database Error", f"Unable to insert words into table '{word_tablename}'\n"
            + insertWordQuery.lastError().text())

    logger.info(
        f"Added {len(word_vals)} words to table '{db.databaseName()}.{word_tablename}'"
    )
    return True


def add_games_to_database(games: Iterable["models.TypingGame"]) -> bool:
    # TODO: update
    con_name = config.CON_NAME
    game_tablename = config.GAME_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open database connection {con_name}")
        utils.display_error("Database Error", f"Could not open database connection '{con_name}'")

    # if not check_table_exists(game_tablename, con_name):
    if True:  # TODO
        createTableQuery = QSqlQuery(db)
        if not createTableQuery.exec(createGameTableQueryString):
            logger.error(
                f"Unable to create table {game_tablename}\n"
                + createTableQuery.lastError().text()
            )
            utils.display_error("Database Error", f"Unable to create table {game_tablename}\n"
                + createTableQuery.lastError().text())

        logger.info(
            f"Created/updated table '{game_tablename}' in {db.databaseName()}"
        )

    insertGameQuery = QSqlQuery(db)
    insertGameQuery.prepare(insertGameQueryString)
    (
        modes,
        wordset_ids,
        seeds,
        poss,
        incorrect_charss,
        elapseds,
        created_ats,
        word_counts,
        last_updateds
    ) = ([], [], [], [], [], [], [], [], [])
    for game in games:
        logger.debug(f"Preparing {game} for database insertion")
        if not all((game.wordset, game.seed, game.elapsed)):
            logger.warning(
                "Ignoring partially initialized or corrupted game data"
            )
            continue
        modes.append(game.mode)
        wordset_ids.append(game.wordset.id)
        seeds.append(game.seed)
        poss.append(game.pos)
        incorrect_charss.append(game.incorrect_chars)
        elapseds.append(game.elapsed)
        created_ats.append(game.start_time)
        word_counts.append(game.get_word_count())
        last_updateds.append(game.last_paused)
    if created_ats:
        insertGameQuery.addBindValue(modes)
        insertGameQuery.addBindValue(wordset_ids)
        insertGameQuery.addBindValue(seeds)
        insertGameQuery.addBindValue(poss)
        insertGameQuery.addBindValue(incorrect_charss)
        insertGameQuery.addBindValue(elapseds)
        insertGameQuery.addBindValue(created_ats)
        insertGameQuery.addBindValue(word_counts)
        insertGameQuery.addBindValue(last_updateds)
        if not insertGameQuery.execBatch():
            logger.error(
                f"Unable to insert values into table '{game_tablename}':\n"
                + insertGameQuery.lastError().text()
            )
            utils.display_error("Database Error", f"Unable to insert values into table '{game_tablename}':\n"
                + insertGameQuery.lastError().text())

        logger.info(f"Added game data to database {db.databaseName()}")
    return True


def get_available_wordsets_ids() -> List[int]:
    con_name = config.CON_NAME
    wordset_tablename = config.WORDSET_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open database connection {con_name}")
        utils.display_error("Database Error", f"Could not open database connection '{con_name}'")


    queryString = f"""
        SELECT id FROM {wordset_tablename}
    """
    query = QSqlQuery(db)
    if not query.exec(queryString):
        logger.warning(
            f"Unable to get wordset ids from {wordset_tablename}\n"
            + query.lastError().text()
        )

    ids = []
    while query.next():
        ids.append(query.value(0))
    logger.debug(f"Retrieved indices of wordsets in database: {ids}")
    return ids

def get_game_data(
    period: Tuple[float, float] = (time.time(), (datetime.date.today().replace(day=1) - datetime.timedelta(days=1)-datetime.date(1970,1,1)).total_seconds())
) -> Optional[List[Tuple[float, float, float, str]]]:
    con_name = config.CON_NAME
    game_tablename = config.GAME_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open database connection {con_name}")
        utils.display_error("Database Error", f"Could not open database connection '{con_name}'")

    if not check_table_exists(game_tablename, con_name):
        logger.warning(
                f"Table {game_tablename} does not exist"
            )
        return None

    queryStr = f"""
        SELECT incorrect_chars, elapsed, pos, last_updated, word_count from {game_tablename}
        WHERE last_updated BETWEEN ? AND ?;
    """
    query = QSqlQuery(db)
    query.prepare(queryStr)
    query.addBindValue(int(period[1]))
    query.addBindValue(int(period[0]))
    if not query.exec():
        logger.warning(
            f"Unable to get data stats from {game_tablename} for time period {int(period[1])}-{int(period[0])}\n"
            + query.lastError().text()
        )

    accs, wpms, dates, incorrect_charss = [], [], [], []
    while query.next():
        incorrect_chars = query.value(0)
        elapsed = query.value(1)
        pos = query.value(2)
        last_updated = query.value(3)
        word_count = query.value(4)
        accs.append(1-len(incorrect_chars)/pos)
        wpms.append(word_count/elapsed*60)
        dates.append(last_updated)
        incorrect_charss.append(incorrect_chars)
    logger.debug(f"Retrieved game data {incorrect_charss[:10]}... {accs[:10]}... {wpms[:10]}... {dates[:10]}...")
    return list(zip(accs, wpms, dates, incorrect_charss))