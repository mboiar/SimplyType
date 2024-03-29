import pytest
from PyQt6.QtSql import QSqlDatabase, QSqlQuery

from .context import speed_typing_game


@pytest.fixture(scope="module")
def session():
    con = QSqlDatabase.addDatabase("QSQLITE", "test_con")
    con.setDatabaseName("test_db")
    assert con.open()
    yield con
    con.close()


@pytest.fixture(scope="module")
def setup_db(con):
    db = con.database()
    createQuery = QSqlQuery(db)
    assert createQuery.exec(
        """
            CREATE TABLE wordsets (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                name VARCHAR(40) NOT NULL,
                language_code VARCHAR(6) NOT NULL,
                difficulty INTEGER
            )
            """
    )
    assert createQuery.exec(
        """
            CREATE TABLE words (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                content VARCHAR(50) NOT NULL,
                wordset_id INTEGER NOT NULL,
                FOREIGN KEY (wordset_id) 
                    REFERENCES wordsets(id)
                    ON DELETE CASCADE,
                UNIQUE(content, wordset_id)
            )
            """
    )
    assert createQuery.exec(
        """
            CREATE TABLE games (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                mode VARCHAR(10),
                wordset_id INTEGER,
                seed INTEGER NOT NULL,
                pos INTEGER NOT NULL,
                incorrect_chars TEXT,
                elapsed REAL,
                created_at REAL NOT NULL UNIQUE,
                FOREIGN KEY (wordset_id)
                    REFERENCES wordsets (id)
                    ON DELETE SET NULL
            );
            """
    )
    assert createQuery.prepare(
        """
        INSERT INTO wordsets (
            name,
            language_code,
            difficulty
        )
        VALUES (?, ?, ?)
        """
    )
    for val in ["test_name", "en", 1]:
        createQuery.addBindValue(val)
    assert createQuery.exec()
    fetchIdQuery = QSqlQuery(db)
    assert fetchIdQuery.exec(
        """
            SELECT seq FROM sqlite_sequence WHERE name = 'wordsets'
        """
    )
    fetchIdQuery.next()
    wordset_id = fetchIdQuery.value(0)
    createQuery.prepare(
        """
        INSERT INTO words (
            content,
            wordset_id
        )
        VALUES (?, ?, ?)
        """
    )
    for val in ["test_word", wordset_id]:
        createQuery.addBindValue(val)
    assert createQuery.exec()

    createQuery.prepare(
        """
        INSERT INTO games (
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
    )
    for val in ["default", wordset_id, 42, 0, "", 0, 30000]:
        createQuery.addBindValue(val)
    assert createQuery.exec()


@pytest.mark.usefixtures("setup_db")
def test_get_wordset(con):
    pass
