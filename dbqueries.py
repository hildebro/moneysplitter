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
    cur = conn.cursor()
    with conn:
        cur.execute('INSERT INTO party(name, creator_id) values (?, ?)', [party_name, creator_id])

    cur.execute('SELECT id FROM party WHERE name = ? and creator_id = ?', [party_name, creator_id])
    party_add(cur.fetchone()[0], creator_id)

def register_user(user):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO user(id, first_name, username) values (?, ?, ?)', [user.id, user.first_name, user.username])

def refresh_username(user):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('UPDATE user SET username = ? WHERE id = ?', [user.username, user.id])

def find_party_id(creator_id, party_name):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * from party where creator_id = ? and name = ?', [creator_id, party_name])
        return cur.fetchone()[0]

def find_user(username):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * from user where username = ?', [username])
        user = cur.fetchone()
        return {
            'id':user[0],
            'first_name':user[1],
            'username':user[2]
        }

def party_add(party_id, user_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO party_users(party_id, user_id) VALUES (?, ?)', [party_id, user_id])

def find_parties_by_creator(user_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT name FROM party WHERE creator_id = ? ', [user_id])
        parties = cur.fetchall()
        unwrapped_parties = []
        for party in parties:
            unwrapped_parties.append(party[0])

        return unwrapped_parties

def find_parties_by_participant(user_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT * FROM party p WHERE exists(
                SELECT null
                FROM party_users pu
                WHERE pu.party_id = p.id and pu.user_id = ?)
            ''',
            [user_id]
        )
        parties = []
        for party in cur.fetchall():
            parties.append({
                'id' : party[0],
                'name' : party[1],
                'creator_id' : party[2]
            })
        return parties

def add_item(item_name, party_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO item(item_name, party_id) VALUES (?, ?)', [item_name, party_id])
