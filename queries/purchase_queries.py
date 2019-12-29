from db import get_session
from models import Item
from models.purchase import Purchase


def create(user_id, checklist_id):
    session = get_session()
    purchase = Purchase(user_id, checklist_id)
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    session.close()
    return purchase


def abort(purchase_id):
    session = get_session()
    session.query(Item).filter(Item.purchase_id == purchase_id).update({"purchase_order": None})
    purchase = session.query(Purchase).filter(Purchase.id == purchase_id).one()
    purchase.items = []
    session.commit()
    session.close()


def finish(purchase_id):
    session = get_session()
    purchase = session.query(Purchase).filter(Purchase.id == purchase_id).one()
    purchase.active = 0
    session.commit()
    session.close()


def set_price(purchase_id, price):
    session = get_session()
    purchase = session.query(Purchase).filter(Purchase.id == purchase_id).one()
    purchase.price = price
    session.commit()
    session.close()
