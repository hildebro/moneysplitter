from sqlalchemy.orm import joinedload

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
    purchase.set_price(price)
    session.commit()
    session.close()


def find_by_checklist(checklist_id):
    session = get_session()
    purchases = session \
        .query(Purchase) \
        .options(joinedload(Purchase.buyer), joinedload(Purchase.items)) \
        .filter(Purchase.checklist_id == checklist_id, Purchase.active.is_(False), Purchase.equalized.is_(False)) \
        .all()
    session.close()
    return purchases


def find_to_equalize(checklist_id):
    session = get_session()
    purchases = session \
        .query(Purchase) \
        .options(joinedload(Purchase.buyer)) \
        .filter(Purchase.checklist_id == checklist_id, Purchase.active.is_(False), Purchase.equalized.is_(False)) \
        .all()
    session.close()
    return purchases


def find_by_ids(ids):
    session = get_session()
    purchases = session \
        .query(Purchase) \
        .options(joinedload(Purchase.buyer)) \
        .filter(Purchase.id.in_(ids)) \
        .all()
    session.close()
    return purchases


def equalize(purchase_ids):
    session = get_session()
    purchases = session.query(Purchase).filter(Purchase.id.in_(purchase_ids)).all()
    for purchase in purchases:
        purchase.equalized = True
    session.commit()
    session.close()
