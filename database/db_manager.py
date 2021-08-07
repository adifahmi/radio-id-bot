import sqlite3


class DBase:
    def __init__(self, database) -> None:
        self.conn = sqlite3.connect(database)

    def migration(self):
        self.conn.execute(
            '''
            '''
        )
        self.conn.execute(
            '''
            DROP TABLE IF EXISTS guild;
            '''
        )
        self.conn.execute(
            '''
            DROP TABLE IF EXISTS guild_details;
            '''
        )
        self.conn.execute(
            '''
            CREATE TABLE guild (
                ID              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT,
                member_count    INT     NOT NULL,
                guild_id        BIGINT  NOT NULL
            );
            '''
        )
        self.conn.execute(
            '''
            CREATE TABLE guild_details (
                ID              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT,
                member_count    INT     NOT NULL,
                guild_id        BIGINT  NOT NULL,
                created_at      TEXT,
                voice_region    TEXT,
                bitrate_limit   TEXT,
                bot_nickname    TEXT,
                bot_roles       TEXT,
                pref_locale     TEXT,
                premium_tier    INT,
                icon_url        TEXT,
                features        TEXT,
                roles           TEXT,
                text_channels   TEXT,
                voice_channels  TEXT
            );
            '''
        )

    def insert(self, table, fields, values):
        self.conn.execute(f"INSERT INTO {table} {fields} VALUES {values};")
        self.conn.commit()

    def close_conn(self):
        self.conn.close()
