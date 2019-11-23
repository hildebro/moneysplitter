import sqlite3
from sqlite3 import Error

def sql_connection():
    try:
        con = sqlite3.connect('money_splitter.db')
        print("Connection is established")
        return con
    except Error:
        print(Error)

con = sql_connection()
cursorObj = con.cursor()

cursorObj.execute("""
    CREATE TABLE user(
        id integer PRIMARY KEY,
        first_name text,
        username text UNIQUE
    )
""")

cursorObj.execute("""
    CREATE TABLE checklist(
        id integer PRIMARY KEY AUTOINCREMENT,
        name text,
        creator_id integer,
        UNIQUE (name, creator_id),
        FOREIGN KEY(creator_id) REFERENCES user(id) ON DELETE SET NULL
    )
""")

cursorObj.execute("""
    CREATE TABLE checklist_user(
        checklist_id integer,
        user_id integer,
        PRIMARY KEY (checklist_id, user_id),
        FOREIGN KEY (checklist_id) REFERENCES checklist(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
    )
""")

cursorObj.execute("""
    CREATE TABLE checklist_item(
        name text,
        checklist_id integer,
        PRIMARY KEY (checklist_id, name),
        FOREIGN KEY (checklist_id) REFERENCES checklist(id) ON DELETE CASCADE
    )
""")

cursorObj.execute("""
    CREATE TABLE purchase(
        id integer PRIMARY KEY AUTOINCREMENT,
        checklist_id integer,
        user_id integer,
        active integer DEFAULT 1,
        price integer,
        FOREIGN KEY (checklist_id) REFERENCES checklist(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
    )
""")

cursorObj.execute("""
    CREATE TABLE purchase_item(
        purchase_id integer,
        name text,
        purchase_order integer,
        FOREIGN KEY (purchase_id) REFERENCES purchase(id) ON DELETE CASCADE
    )
""")

con.commit()

