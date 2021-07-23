import sqlite3

conn = sqlite3.connect('database/app.db')

conn.execute(
    '''
    CREATE TABLE IF NOT EXISTS guild (
        ID              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT,
        member_count    INT     NOT NULL,
        guild_id        BIGINT  NOT NULL
    );
    '''
)

conn.execute(
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

# conn.execute("INSERT INTO guild (name,member_count,guild_id) \
#       VALUES ('Test', 25, 123123213213 )")

# conn.commit()

conn.close()
