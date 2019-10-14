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
        UNIQUE (name, creator_id)
    )
""")

cursorObj.execute("""
    CREATE TABLE checklist_user(
        checklist_id integer,
        user_id integer,
        PRIMARY KEY (checklist_id, user_id)
    )
""")

cursorObj.execute("""
    CREATE TABLE checklist_item(
        name text,
        checklist_id integer,
        PRIMARY KEY (checklist_id, name)
    )
""")

cursorObj.execute("""
    CREATE TABLE purchase(
        id integer PRIMARY KEY AUTOINCREMENT,
        checklist_id integer,
        user_id integer,
        active integer DEFAULT 1,
        price integer
    )
""")

cursorObj.execute("""
    CREATE TABLE purchase_item(
        purchase_id integer,
        name text,
        purchase_order integer
    )
""")

con.commit()

