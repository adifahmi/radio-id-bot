import sqlite3


class DBase:
    def __init__(self) -> None:
        self.conn = sqlite3.connect('database/app.db')
        self.migration()

    def migration(self):
        self.conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS guild (
                ID              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT,
                member_count    INT     NOT NULL,
                guild_id        BIGINT  NOT NULL
            );
            '''
        )
        self.conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS guild_details (
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
                voice_channels  TEXT,
            );
            '''
        )

    def insert(self, fields, values):
        self.conn.execute(f"INSERT INTO guild ({fields}) VALUES ({values})")
        self.conn.commit()

    def close_conn(self):
        self.conn.close()
