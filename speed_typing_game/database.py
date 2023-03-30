
import os
from typing import List, Tuple, Iterable
import logging

from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlQueryModel

from speed_typing_game import config, models

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
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
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
        return False
    if True: #not check_table_exists(wordset_tablename, con_name):
        dropTableQuery = QSqlQuery(db)
        if not dropTableQuery.exec(deleteGameTableQueryStr):
            logger.error(f"Unable to delete table '{game_tablename}'\n" + dropTableQuery.lastError().text())
            return False
        logger.debug(f"Deleted table '{game_tablename}' from {db.databaseName()}")
    return True

def delete_wordset_table() -> bool:
    con_name = config.CON_NAME
    wordset_tablename = config.WORDSET_TABLE
    word_tablename = config.WORD_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open database connection '{con_name}'")
        return False
    if True: #not check_table_exists(wordset_tablename, con_name):
        dropTableQuery = QSqlQuery(db)
        if not dropTableQuery.exec(deleteWordsetTableQueryStr):
            logger.error(f"Unable to delete table '{wordset_tablename}'\n" + dropTableQuery.lastError().text())
            return False
        if not dropTableQuery.exec(deleteWordTableQueryStr):
            logger.error(f"Unable to delete table '{word_tablename}'\n" + dropTableQuery.lastError().text())
            return False
        logger.debug(f"Deleted table '{wordset_tablename}' from {db.databaseName()}")
    return True

def check_table_exists(tablename: str, db_con: str) -> bool:
    return tablename in QSqlDatabase.database(db_con).tables()

path = "speed_typing_game/resources/words/difficult_english_word_base.txt"


def add_wordsets_to_database(wordsets: Iterable['models.Wordset']) -> bool:
    con_name = config.CON_NAME
    wordset_tablename = config.WORDSET_TABLE
    word_tablename = config.WORD_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open database connection '{con_name}'")
        return False
    if True: #not check_table_exists(wordset_tablename, con_name):
        createTableQuery = QSqlQuery(db)
        if not createTableQuery.exec(createWordsetTableQueryString):
            logger.error(f"Unable to create table '{wordset_tablename}'\n" + createTableQuery.lastError().text())
            return False
        logger.debug(f"Created/updated table '{wordset_tablename}' in {db.databaseName()}")

    if True: #not check_table_exists(word_tablename, con_name):
        createTableQuery = QSqlQuery(db)
        if not createTableQuery.exec(createWordTableQueryString):
            logger.error(f"Unable to create table '{word_tablename}'\n" + createTableQuery.lastError().text())
            return False
        logger.debug(f"Created/updated table '{word_tablename}' in {db.databaseName()}")

    insertWordsetQuery = QSqlQuery(db)
    insertWordsetQuery.prepare(insertWordsetQueryString)
    wordset_ids = []
    word_vals = []
    for wordset in wordsets:
        name, language_code, difficulty = wordset.name, wordset.language, wordset.difficulty
        words = wordset.words
        if not words:
            logger.warning(f"Ignoring empty wordset {name}")
            continue
        insertWordsetQuery.addBindValue(name)
        insertWordsetQuery.addBindValue(language_code)
        insertWordsetQuery.addBindValue(difficulty)
        if not insertWordsetQuery.exec():
            logger.error(f"Unable to insert wordset data into table '{wordset_tablename}'\n" + insertWordsetQuery.lastError().text())
            return False
        logger.info(f"Added wordset {name} to table {db.databaseName()}.{wordset_tablename}")
        selectAutoincrIdQueryStr = f"""
            SELECT seq, name FROM sqlite_sequence WHERE name = '{wordset_tablename}';
        """
        selectAutoincrIdQuery = QSqlQuery(db)
        if not selectAutoincrIdQuery.exec(selectAutoincrIdQueryStr):
            logger.error(f"Unable to select autoincrement value for table {wordset_tablename}:\n" + selectAutoincrIdQuery.lastError().text())
            return False
        selectAutoincrIdQuery.next()
        last_wordset_id = selectAutoincrIdQuery.value(0)
        last_name = selectAutoincrIdQuery.value(1)
        logger.debug(f"Wordset autoincrement value: {last_wordset_id} for table {last_name}")
        wordset_ids.extend([last_wordset_id]*len(words))
        word_vals.extend([*words,])

    insertWordQuery = QSqlQuery(db)
    insertWordQuery.prepare(insertWordQueryString)
    insertWordQuery.addBindValue(word_vals)
    insertWordQuery.addBindValue(wordset_ids)
    if not insertWordQuery.execBatch():
        logger.error(f"Unable to insert words into table '{word_tablename}'\n" + insertWordQuery.lastError().text())
        deleteWordsetQueryString = f"""
            DELETE FROM {wordset_tablename}
            WHERE id IN {*wordset_ids,}
        """
        deleteWordsetQuery = QSqlQuery(db)
        if not deleteWordsetQuery.exec(deleteWordsetQueryString):
            logger.error(f"Unable to delete wordsets from table '{wordset_tablename}'\n" + deleteWordsetQuery.lastError().text())
        logger.info(f"Removed wordsets from table {db.databaseName()}.{wordset_tablename}")
        return False
    logger.info(f"Added {len(word_vals)} words to table '{db.databaseName()}.{word_tablename}'")
    return True
    

def add_games_to_database(games: Iterable['models.TypingGame']) -> bool:
    #TODO: update
    con_name = config.CON_NAME
    game_tablename = config.GAME_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open database connection {con_name}")
        return False
    # if not check_table_exists(game_tablename, con_name):
    if True: #TODO
        createTableQuery = QSqlQuery(db)
        if not createTableQuery.exec(createGameTableQueryString):
            logger.error(f"Unable to create table {game_tablename}\n" + createTableQuery.lastError().text())
        logger.info(f"Created/updated table '{game_tablename}' in {db.databaseName()}")
    
    insertGameQuery = QSqlQuery(db)
    insertGameQuery.prepare(insertGameQueryString)
    modes, wordset_ids, seeds, poss, incorrect_charss, elapseds, created_ats = [], [], [], [], [], [], []
    for game in games:
        # mode, wordset, seed, pos, incorrect_chars, created_at = game.mode, game.wordset, game.seed,
        logger.debug(f"Preparing {game} for database insertion")
        if not all((game.wordset, game.seed, game.elapsed)):
            logger.warning(f"Ignoring partially initialized or corrupted game data")
            continue
        modes.append(game.mode)
        wordset_ids.append(game.wordset.id)
        seeds.append(game.seed)
        poss.append(game.pos)
        incorrect_charss.append(game.incorrect_chars)
        elapseds.append(game.elapsed)
        created_ats.append(game.start_time)
    if created_ats:
        insertGameQuery.addBindValue(modes)
        insertGameQuery.addBindValue(wordset_ids)
        insertGameQuery.addBindValue(seeds)
        insertGameQuery.addBindValue(poss)
        insertGameQuery.addBindValue(incorrect_charss)
        insertGameQuery.addBindValue(elapseds)
        insertGameQuery.addBindValue(created_ats)
        # logger.debug(f"{len(modes)} {len(wordset_ids)} {len(seeds)} {len(poss)} {len(incorrect_charss)} {len(elapseds)} {len(created_ats)}")
        if not insertGameQuery.execBatch():
            logger.error(f"Unable to insert values into table '{game_tablename}':\n" + insertGameQuery.lastError().text())
            return False
        logger.info(f"Added game data to database {db.databaseName()}")
    return True


def get_available_wordsets_ids() -> List[int]:
    con_name = config.CON_NAME
    wordset_tablename = config.WORDSET_TABLE
    db = QSqlDatabase.database(con_name)
    if not db.open():
        logger.error(f"Could not open database connection {con_name}")
        return False
    
    queryString = f"""
        SELECT id FROM {wordset_tablename}
    """
    query = QSqlQuery(db)
    if not query.exec(queryString):
        logger.error(f"Unable to get wordset ids from {wordset_tablename}\n"+query.lastError().text())
        return False
    ids = []
    while query.next():
        ids.append(query.value(0))
    logger.debug(f"Retrieved indices of wordsets in database: {ids}")
    return ids