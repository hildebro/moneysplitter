from db import get_session
from models import Purchase
from models.item import Item


def create(item_name, checklist_id):
    session = get_session()
    item = Item(item_name, checklist_id)
    session.add(item)
    session.commit()
    session.refresh(item)
    session.close()
    return item


def remove(item_id):
    session = get_session()
    session.query(Item).filter(Item.id == item_id).delete()
    session.commit()
    session.close()


def remove_all(ids_to_remove):
    session = get_session()
    session.query(Item).filter(Item.id.in_(ids_to_remove)).delete(synchronize_session=False)
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
