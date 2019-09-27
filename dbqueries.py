import requests
import re
import sqlite3

def connect_db():
    conn = None
    try:
        conn = sqlite3.connect('money_splitter.db')
    except Error as e:
        print(e)

    return conn

def make_party(party_name, creator_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        print('Cursor created')
        cur.execute('INSERT INTO party(name, creator_id) values (?, ?)', [party_name, creator_id])

    print('Party created')
