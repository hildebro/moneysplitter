import requests
import re
import sqlite3
import os

def unwrap(array):
    unwrapped_array = []
    for element in array:
        unwrapped_array.append(element[0])

    return unwrapped_array

def connect_db():
    conn = None
    try:
        conn = sqlite3.connect(os.path.dirname(__file__) + '/money_splitter.db')
    except Error as e:
        print(e)

    return conn

def make_checklist(checklist_name, creator_id):
    conn = connect_db()
    cur = conn.cursor()
    with conn:
        cur.execute('INSERT INTO checklist(name, creator_id) values (?, ?)', [checklist_name, creator_id])

    cur.execute('SELECT id FROM checklist WHERE name = ? and creator_id = ?', [checklist_name, creator_id])
    checklist_add(cur.fetchone()[0], creator_id)

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

def checklist_name_exists(creator_id, checklist_name):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) from checklist where creator_id = ? and name = ?', [creator_id, checklist_name])
        result = cur.fetchone()
        return result[0] > 0

def check_user_exists(user_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM user WHERE id = ?', [user_id])
        return cur.fetchone()[0] > 0

def find_user(username):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * from user where username = ?', [username])
        user = cur.fetchone()
        if user is None:
            return None

        return {
            'id':user[0],
            'first_name':user[1],
            'username':user[2]
        }

def checklist_add(checklist_id, user_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO checklist_user(checklist_id, user_id) VALUES (?, ?)', [checklist_id, user_id])

def find_checklists_by_creator(user_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM checklist WHERE creator_id = ? ', [user_id])
        checklists = []
        for checklist in cur.fetchall():
            checklists.append({
                'id' : checklist[0],
                'name' : checklist[1],
                'creator_id' : checklist[2]
            })
        return checklists

def find_checklists_by_participant(user_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT * FROM checklist p WHERE exists(
                SELECT null
                FROM checklist_user pu
                WHERE pu.checklist_id = p.id and pu.user_id = ?)
            ''',
            [user_id]
        )
        checklists = []
        for checklist in cur.fetchall():
            checklists.append({
                'id' : checklist[0],
                'name' : checklist[1],
                'creator_id' : checklist[2]
            })
        return checklists

def add_item(item_name, checklist_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO checklist_item(name, checklist_id) VALUES (?, ?)', [item_name, checklist_id])

def remove_item(item_name, checklist_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            'DELETE FROM checklist_item WHERE name = ? and checklist_id = ?',
            [item_name, checklist_id]
        )

def find_checklist_items(checklist_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT i.name
            FROM checklist_item i
            WHERE i.checklist_id = ?
            AND NOT EXISTS(
                SELECT NULL
                FROM purchase_item pi
                WHERE pi.name = i.name
                AND pi.purchase_id in (
                    SELECT p.id
                    FROM purchase p
                    WHERE p.checklist_id = i.checklist_id
                )
            )
            ''',
            [checklist_id]
        )

        return unwrap(cur.fetchall())

def find_purchases(checklist_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT u.username, p.price, pi.purchase_id, pi.name
            FROM purchase_item pi
            JOIN purchase p on p.id = pi.purchase_id
            JOIN user u on p.user_id = u.id
            WHERE p.checklist_id = ?
            ''',
            [checklist_id]
        )
        results = cur.fetchall()
        if len(results) == 0:
            return []

        converted_results = {}
        for result in results:
            username = result[0]
            price = result[1]
            purchase_id = result[2]
            item_name = result[3]
            if username not in converted_results:
                converted_results[username] = {
                    'price' : 0.0,
                    'purchase_ids' : [],
                    'items' : []
                }
            if purchase_id not in converted_results[username]['purchase_ids']:
                converted_results[username]['purchase_ids'].append(purchase_id)
                converted_results[username]['price'] += price / 100.0
            converted_results[username]['items'].append(item_name)

        return converted_results

def find_items_to_purchase(purchase_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT i.name
            FROM checklist_item i
            WHERE i.checklist_id IN (
                SELECT p.checklist_id
                FROM purchase p
                WHERE p.id = ?
            )
            AND NOT EXISTS(
                SELECT NULL
                FROM purchase_item pi
                WHERE pi.name = i.name
                AND pi.purchase_id = ?
            )
            ''',
            [purchase_id, purchase_id]
        )

        return unwrap(cur.fetchall())

def find_active_purchase(user_id, checklist_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT id FROM purchase WHERE checklist_id = ? and user_id = ? and active = 1',
            [checklist_id, user_id]
        )
        result = cur.fetchone()
        if result is None:
            return None
        return result[0]

def start_purchase(user_id, checklist_id):
    purchase_id = find_active_purchase(user_id, checklist_id)
    if purchase_id is not None:
        return purchase_id

    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO purchase(checklist_id, user_id) VALUES (?, ?)', [checklist_id, user_id])

    return find_active_purchase(user_id, checklist_id)


def buffer_item(item_name, purchase_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO purchase_item(purchase_id, name, purchase_order) VALUES (?, ?, ?)',
            [purchase_id, item_name, find_next_order(purchase_id)]
        )

def find_next_order(purchase_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT MAX(purchase_order) FROM purchase_item where purchase_id = ?',
            [purchase_id]
        )
        max_order = cur.fetchone()[0]
        if max_order is None:
            return 0

        return max_order + 1

def unbuffer_last_item(purchase_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT MAX(purchase_order) FROM purchase_item WHERE purchase_id = ?', [purchase_id])
        purchase_order = cur.fetchone()[0]
        if purchase_order is None:
            return False

        cur.execute(
                'DELETE FROM purchase_item WHERE purchase_id = ? and purchase_order = ?',
                [purchase_id, purchase_order]
        )

    return True

def abort_purchase(purchase_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM purchase_item WHERE purchase_id = ?', [purchase_id])
        cur.execute('DELETE FROM purchase WHERE id = ?', [purchase_id])

def finish_purchase(purchase_id):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute(
            '''
            DELETE FROM checklist_item
            WHERE name IN (
                SELECT pi.name FROM purchase_item pi WHERE pi.purchase_id = ?
            )
            AND checklist_id IN (
                SELECT p.checklist_id FROM purchase p WHERE p.id = ?
            )
            ''',
            [purchase_id, purchase_id]
        )
        cur.execute('UPDATE purchase SET active = 0 WHERE id = ?', [purchase_id])

def set_purchase_price(purchase_id, price):
    conn = connect_db()
    with conn:
        cur = conn.cursor()
        cur.execute('UPDATE purchase SET price = ? WHERE id = ?', [float(price) * 100, purchase_id])
