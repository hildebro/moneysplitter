from sqlalchemy import func

from db import get_session
from models import Purchase
from models.item import Item


def create(item_name, checklist_id):
    session = get_session()
    session.add(Item(item_name, checklist_id))
    session.commit()
    session.close()


def remove(item_id):
    session = get_session()
    session.query(Item).filter(Item.id == item_id).delete()
    session.commit()
    session.close()


def find_by_checklist(checklist_id):
    session = get_session()
    # noinspection PyComparisonWithNone
    items = session.query(Item).filter(Item.checklist_id == checklist_id, Item.purchase == None).all()
    session.close()
    return items


def find_for_purchase(purchase_id):
    session = get_session()
    purchase = session.query(Purchase).filter(Purchase.id == purchase_id).one()
    # noinspection PyComparisonWithNone
    items = session \
        .query(Item) \
        .filter(Item.checklist == purchase.checklist, Item.purchase == None) \
        .order_by(Item.id) \
        .all()
    session.close()
    return items


def buffer(item_id, purchase_id):
    session = get_session()
    highest_order = session.query(func.max(Item.purchase_order)).filter(Item.purchase_id == purchase_id).scalar()
    if highest_order is None:
        highest_order = 0
    item = session.query(Item).filter(Item.id == item_id).one()
    item.purchase_id = purchase_id
    item.purchase_order = highest_order + 1
    session.commit()
    session.close()


def unbuffer(purchase_id):
    session = get_session()
    highest_order = session.query(func.max(Item.purchase_order)).filter(Item.purchase_id == purchase_id).scalar()
    if highest_order is None:
        session.close()
        return False

    item = session.query(Item).filter(Item.purchase_id == purchase_id, Item.purchase_order == highest_order).one()
    item.purchase_id = None
    item.purchase_order = None
    session.commit()
    session.close()
    return True
