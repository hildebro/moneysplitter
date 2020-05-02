from sqlalchemy import func
from sqlalchemy.orm import joinedload

from ..models import Item
from ..models import Purchase


def clear_ongoing_purchase(session, checklist_id, user_id):
    session \
        .query(Purchase) \
        .filter(Purchase.checklist_id == checklist_id, Purchase.buyer_id == user_id, Purchase.in_progress == True) \
        .delete(synchronize_session=False)
    session.commit()


def new_purchase(session, checklist_id, user_id):
    clear_ongoing_purchase(session, checklist_id, user_id)
    purchase = Purchase(user_id, checklist_id)
    session.add(purchase)
    session.commit()
    return purchase


def commit_purchase(session, purchase, price):
    purchase.in_progress = False
    purchase.set_price(price)
    session.commit()


def abort(session, purchase_id):
    session.query(Purchase).filter(Purchase.id == purchase_id).delete(synchronize_session=False)
    session.commit()


def mark_item(session, purchase_id, item_id):
    """
    :return: False, if the item has already been marked by someone else.
    """
    item = session.query(Item).filter(Item.id == item_id).one()
    if item.purchase_id is None:
        item.purchase_id = purchase_id
    elif item.purchase_id == purchase_id:
        item.purchase_id = None
    else:
        return False

    session.commit()
    return True


def has_items(session, purchase_id):
    items_in_purchase = session.query(func.count(Item.id)).filter(Item.purchase_id == purchase_id).scalar()
    return items_in_purchase > 0


def find(session, purchase_id):
    return session.query(Purchase).filter(Purchase.id == purchase_id).one()


def find_by_checklist(session, checklist_id):
    purchases = session \
        .query(Purchase) \
        .options(joinedload(Purchase.buyer), joinedload(Purchase.items)) \
        .filter(Purchase.checklist_id == checklist_id,
                Purchase.written_off.is_(False),
                Purchase.in_progress.is_(False)) \
        .all()
    return purchases


def write_off(session, checklist_id):
    purchases = find_by_checklist(session, checklist_id)
    for purchase in purchases:
        purchase.written_off = True

    session.commit()


def find_by_ids(session, ids):
    purchases = session \
        .query(Purchase) \
        .options(joinedload(Purchase.buyer)) \
        .filter(Purchase.id.in_(ids)) \
        .all()
    return purchases


def find_in_progress(session, user_id):
    return session \
        .query(Purchase) \
        .filter(Purchase.buyer_id == user_id, Purchase.in_progress.is_(True)) \
        .scalar()
