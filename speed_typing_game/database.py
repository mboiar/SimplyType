import os
from typing import List, Tuple, Iterable
import logging

from speed_typing_game import config
from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlQueryModel

logger = logging.getLogger(__name__)
createWordsetTableQueryString = f"""
            CREATE TABLE {config.WORDSET_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                name VARCHAR(40) NOT NULL,
                language_code VARCHAR(6) NOT NULL,
                difficulty INTEGER
            )
            """

createWordTableQueryString = f"""
            CREATE TABLE {config.WORD_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                content VARCHAR(50) NOT NULL UNIQUE,
                wordset_id INTEGER NOT NULL,
                FOREIGN_KEY (wordset_id)
                    REFERENCES {config.WORDSET_TABLE} (id)
                    ON DELETE CASCADE
            )
            """

createGameTableQueryString = f"""
            CREATE TABLE {config.GAME_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                mode VARCHAR(10),
                wordset_id INTEGER,
                FOREIGN_KEY (wordset_id)
                    REFERENCES {config.WORDSET_TABLE} (id)
                    ON DELETE SET NULL
                seed INTEGER NOT NULL,
                pos INTEGER NOT NULL,
                incorrect_chars TEXT,
                created_at INTEGER NOT NULL
            )
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
            created_at
        )
        VALUES (?, ?, ?, ?)
        """


def check_table_exists(tablename: str, db_con: str) -> bool:
    return tablename in QSqlDatabase.database(db_con).tables()

def get_wordset_from_file(file_path: str) -> Tuple[Tuple, Tuple[str]]:
    wordset = tuple()
    if os.path.exists(file_path):
        open_file = open(file_path, 'r')
        wordset = tuple(i.strip().lower() for i in set(open_file.read().split('\n')))
        if not wordset:
            logger.warning(f"Received empty wordset {file_path}")
            return tuple((None, None, None), tuple())
        if len(wordset[0].split()) > 1:
            header = tuple(wordset[0].split())
            words = wordset[1:]
        else:
            header = tuple(None, None, None)
            words = wordset

    return (header, words)

def add_wordsets_to_database(wordsets: Iterable[Tuple[Tuple, Tuple[str]]]) -> bool:
    con_name = config.CON_NAME
    wordset_tablename = config.WORDSET_TABLE
    word_tablename = config.WORD_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open databse connection {con_name}")
        return False
    if not check_table_exists(wordset_tablename, con_name):
        createTableQuery = QSqlQuery()
        createTableQuery.exec(createWordsetTableQueryString)
        logger.info(f"Created table {wordset_tablename} in {db.databaseName()}")

    if not check_table_exists(word_tablename, con_name):
        createTableQuery = QSqlQuery()
        createTableQuery.exec(createWordTableQueryString)
        logger.info(f"Created table {word_tablename} in {db.databaseName()}")

    insertWordsetQuery = QSqlQuery()
    insertWordsetQuery.prepare(insertWordsetQueryString)
    names, language_codes, difficulties, wordset_ids, word_vals = [], [], [], [], []
    for id, wordset in enumerate(wordsets):
        name, language_code, difficulty = wordset[0]
        words = wordset[1]
        if not words:
            logger.warning(f"Ignoring empty wordset {name}")
            continue
        names.append(name)
        language_codes.append(language_code)
        difficulties.append(difficulty)
        wordset_ids.extend([id]*len(words))
        word_vals.extend([words])

    if wordset_ids:
        insertWordsetQuery.addBindValue(names)
        insertWordsetQuery.addBindValue(language_codes)
        insertWordsetQuery.addBindValue(difficulties)
        if not insertWordsetQuery.execBatch():
            logger.error(insertWordsetQuery.lastError())
            return False

        insertWordQuery = QSqlQuery()
        insertWordQuery.prepare(insertWordQueryString)
        insertWordQuery.addBindValue(word_vals)
        insertWordQuery.addBindValue(wordset_ids)
        if not insertWordsetQuery.execBatch():
            logger.error(insertWordQuery.lastError())
            return False 
        logger.info(f"Added wordsets {names} to database {db.databaseName()}")
    return True
    

def add_games_to_database(games: List[Tuple]) -> bool:
    con_name = config.CON_NAME
    game_tablename = config.GAME_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open databse connection {con_name}")
        return False
    if not check_table_exists(game_tablename, con_name):
        createTableQuery = QSqlQuery()
        createTableQuery.exec(createGameTableQueryString)
        logger.info(f"Created table {game_tablename} in {db.databaseName()}")
    
    insertGameQuery = QSqlQuery()
    insertGameQuery.prepare(insertGameQueryString)
    modes, wordset_ids, seeds, poss, incorrect_charss, created_ats = [], [], [], [], [], []
    for game in games:
        mode, wordset_id, seed, pos, incorrect_chars, created_at = game
        if not all((wordset_id, seed, pos, created_at)):
            logger.warning(f"Ignoring game with incomplete data")
        modes.append(mode)
        wordset_ids.append(wordset_id)
        seeds.append(seed)
        poss.append(pos)
        incorrect_charss.append(incorrect_chars)
        created_ats.append(created_at)
    if created_ats:
        insertGameQuery.addBindValue(modes)
        insertGameQuery.addBindValue(wordset_ids)
        insertGameQuery.addBindValue(seeds)
        insertGameQuery.addBindValue(poss)
        insertGameQuery.addBindValue(incorrect_charss)
        insertGameQuery.addBindValue(created_ats)
        if not insertGameQuery.execBatch():
            logger.error(insertGameQuery.lastError())
            return False
    return True

def retrieve_wordset(name: str) -> Tuple[str]:
    # retrieveWordsetQueryString = f"""
    #     SELECT id FROM {config.WORDSET_TABLE} 
    #     WHERE NAME == {name}
    #     """
    con_name = config.CON_NAME
    wordset_tablename = config.WORDSET_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open database connection {con_name}")
        return
    if not check_table_exists(wordset_tablename, con_name):
        logger.warning(f"Wordset table does not exist.")
        return
    query = QSqlQuery()
    # if not query.exec(retrieveWordsetQueryString):
    #     logger.error(query.lastError())
    #     return
    # wordset_id = None
    # while query.next():
    #     wordset_id = query.value(0)
    # if wordset_id is None:
    #     logger.warning(f"No wordset named {name} in database {db.databaseName()}.")
    #     return
    retrieveWordQueryString = f"""
        SELECT W.content FROM {config.WORD_TABLE} W
        INNER JOIN {config.WORDSET_TABLE} WS ON WS.id = W.wordset_id
        WHERE WS.name = {name}
        """
    if not query.exec(retrieveWordQueryString):
        logger.error(query.lastError())
        return
    words = []
    while query.next():
        words.append(query.value(0))
    return words
