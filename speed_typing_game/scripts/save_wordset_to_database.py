import sys

from speed_typing_game import database, models, utils, config

if __name__ == "__main__":
    if not utils.create_connection(config.DB, config.CON_NAME):
        sys.exit(1)
    database.delete_wordset_table()
    wordsets = [models.Wordset.from_file(i) for i in sys.argv[1:]]
    database.add_wordsets_to_database(wordsets)
