import requests
import re
import sqlite3

def unwrap(array):
    unwrapped_array = []
    for element in array:
        unwrapped_array.append(element[0])

    return unwrapped_array

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
        return unwrap(cur.fetchall())

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

def find_party_items(party_name = '', party_id = 0):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        if party_name != '':
            cur.execute(
                '''
                SELECT i.item_name
                FROM item i
                WHERE EXISTS(
                    SELECT NULL
                    FROM party p
                    WHERE p.id = i.party_id AND p.name = ?
                )
                ''',
                [party_name]
            )
        elif party_id != 0:
            cur.execute(
                '''
                SELECT i.item_name
                FROM item i
                WHERE i.party_id = ?
                AND NOT EXISTS(
                    SELECT NULL
                    FROM purchase_items pi
                    WHERE pi.item_name = i.item_name
                    AND pi.purchase_id in (
                        SELECT p.id
                        FROM purchase p
                        WHERE p.party_id = i.party_id
                    )
                )
                ''',
                [party_id]
            )
        else:
            return []

        return unwrap(cur.fetchall())

def find_items_to_purchase(purchase_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT i.item_name
            FROM item i
            WHERE i.party_id IN (
                SELECT p.party_id
                FROM purchase p
                WHERE p.id = ?
            )
            AND NOT EXISTS(
                SELECT NULL
                FROM purchase_items pi
                WHERE pi.item_name = i.item_name
                AND pi.purchase_id = ?
            )
            ''',
            [purchase_id, purchase_id]
        )

        return unwrap(cur.fetchall())

def get_active_purchase(user_id, party_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT id FROM purchase WHERE party_id = ? and user_id = ? and active = 1',
            [party_id, user_id]
        )
        result = cur.fetchone()
        if result is None:
            return None
        return result[0]

def start_purchase(user_id, party_id):
    purchase_id = get_active_purchase(user_id, party_id)
    if purchase_id is not None:
        return purchase_id

    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO purchase(party_id, user_id) VALUES (?, ?)', [party_id, user_id])

    return get_active_purchase(user_id, party_id)


def buffer_purchase(item_name, purchase_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO purchase_items(purchase_id, item_name, purchase_order) VALUES (?, ?, ?)',
            [purchase_id, item_name, find_next_order(purchase_id)]
        )

def find_next_order(purchase_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT MAX(purchase_order) FROM purchase_items where purchase_id = ?',
            [purchase_id]
        )
        max_order = cur.fetchone()[0]
        if max_order is None:
            return 0

        return max_order + 1

def revert_purchase(purchase_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT MAX(purchase_order) FROM purchase_items WHERE purchase_id = ?', [purchase_id])
        purchase_order = cur.fetchone()[0]
        if purchase_order is None:
            return False

        cur.execute(
                'DELETE FROM purchase_items WHERE purchase_id = ? and purchase_order = ?',
                [purchase_id, purchase_order]
        )

    return True

def finish_purchase(purchase_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            '''
            DELETE FROM item
            WHERE item_name IN (
                SELECT pi.item_name FROM purchase_items pi WHERE pi.purchase_id = ?
            )
            AND party_id IN (
                SELECT p.party_id FROM purchase p WHERE p.id = ?
            )
            ''',
            [purchase_id, purchase_id]
        )
        cur.execute('UPDATE purchase SET active = 0 WHERE id = ?', [purchase_id])

def set_price(purchase_id, price):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('UPDATE purchase SET price = ? WHERE id = ?', [float(price) * 100, purchase_id])
