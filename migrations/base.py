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
    CREATE TABLE party(
        id integer PRIMARY KEY AUTOINCREMENT,
        name text,
        creator_id integer,
        UNIQUE (name, creator_id)
    )
""")

cursorObj.execute("""
    CREATE TABLE party_users(
        party_id integer,
        user_id integer,
        PRIMARY KEY (party_id, user_id)
    )
""")

cursorObj.execute("""
    CREATE TABLE item(
        item_name integer,
        party_id integer,
        PRIMARY KEY (party_id, item_name)
    )
""")

cursorObj.execute("""
    CREATE TABLE purchase(
        id integer PRIMARY KEY AUTOINCREMENT,
        party_id integer,
        user_id integer,
        price integer
    )
""")

cursorObj.execute("""
    CREATE TABLE purchase_items(
        purchase_id integer,
        item_id integer,
        PRIMARY KEY (purchase_id, item_id)
    )
""")

con.commit()

