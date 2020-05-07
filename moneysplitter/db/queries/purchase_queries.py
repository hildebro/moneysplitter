from sqlalchemy import func
from sqlalchemy.orm import joinedload

from . import user_queries
from ..models import Item
from ..models import Purchase


def delete_in_progress(session, user_id):
    session \
        .query(Purchase) \
        .filter(Purchase.buyer_id == user_id, Purchase.in_progress == True) \
        .delete(synchronize_session=False)
    session.commit()


def create(session, user_id):
    delete_in_progress(session, user_id)

    checklist = user_queries.get_selected_checklist(session, user_id)
    purchase = Purchase(user_id, checklist.id)
    session.add(purchase)
    session.commit()


def mark_item(session, user_id, item_id):
    purchase = find_in_progress(session, user_id)
    item = session.query(Item).filter(Item.id == item_id).one()

    if item.purchase_id is None:
        item.purchase_id = purchase.id
    elif item.purchase_id == purchase.id:
        item.purchase_id = None
    else:
        # another purchase is working on this item
        return False

    session.commit()
    return True


def has_selected_items(session, user_id):
    count = session \
        .query(func.count(Item.id)) \
        .filter(session
                .query(Purchase)
                .filter(Purchase.in_progress == True, Purchase.buyer_id == user_id, Item.purchase_id == Purchase.id)
                .exists()
                ) \
        .scalar()
    return count > 0


def finalize_purchase(session, user_id, price):
    purchase = find_in_progress(session, user_id)
    purchase.in_progress = False
    purchase.set_price(price)
    session.commit()


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


def find_in_progress(session, user_id):
    return session \
        .query(Purchase) \
        .filter(Purchase.buyer_id == user_id, Purchase.in_progress.is_(True)) \
        .scalar()
