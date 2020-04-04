from sqlalchemy.orm import joinedload

from ..models import Item
from ..models import Purchase


def create_purchase(session, user_id, checklist_id, item_ids_to_purchase, price):
    purchase = Purchase(user_id, checklist_id, price)
    session.add(purchase)
    session.commit()
    session.query(Item).filter(Item.id.in_(item_ids_to_purchase)).update({"purchase_id": purchase.id},
                                                                         synchronize_session=False)
    session.commit()


def find_by_checklist(session, checklist_id):
    purchases = session \
        .query(Purchase) \
        .options(joinedload(Purchase.buyer), joinedload(Purchase.items)) \
        .filter(Purchase.checklist_id == checklist_id, Purchase.equalized.is_(False)) \
        .all()
    return purchases


def find_to_equalize(session, checklist_id):
    purchases = session \
        .query(Purchase) \
        .options(joinedload(Purchase.buyer)) \
        .filter(Purchase.checklist_id == checklist_id, Purchase.equalized.is_(False)) \
        .all()
    return purchases


def find_by_ids(session, ids):
    purchases = session \
        .query(Purchase) \
        .options(joinedload(Purchase.buyer)) \
        .filter(Purchase.id.in_(ids)) \
        .all()
    return purchases


def equalize(session, purchase_ids):
    purchases = session.query(Purchase).filter(Purchase.id.in_(purchase_ids)).all()
    for purchase in purchases:
        purchase.equalized = True
    session.commit()
