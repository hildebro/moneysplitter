from sqlalchemy.orm import joinedload

from db import get_session
from models import Item
from models.purchase import Purchase


def create_item_purchase(user_id, checklist_id, item_ids_to_purchase, price):
    session = get_session()
    purchase = Purchase(user_id, checklist_id, price)
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    session.query(Item).filter(Item.id.in_(item_ids_to_purchase)).update({"purchase_id": purchase.id},
                                                                         synchronize_session=False)
    session.commit()
    session.close()


def create_named_purchase(user_id, checklist_id, name, price):
    named_item = Item(name, checklist_id)
    purchase = Purchase(user_id, checklist_id, price)
    purchase.items = [named_item]
    session = get_session()
    session.add(purchase)
    session.add(named_item)
    session.commit()
    session.close()


def find_by_checklist(checklist_id):
    session = get_session()
    purchases = session \
        .query(Purchase) \
        .options(joinedload(Purchase.buyer), joinedload(Purchase.items)) \
        .filter(Purchase.checklist_id == checklist_id, Purchase.equalized.is_(False)) \
        .all()
    session.close()
    return purchases


def find_to_equalize(checklist_id):
    session = get_session()
    purchases = session \
        .query(Purchase) \
        .options(joinedload(Purchase.buyer)) \
        .filter(Purchase.checklist_id == checklist_id, Purchase.equalized.is_(False)) \
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
