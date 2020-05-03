from sqlalchemy import or_

from ..models import Item
from ..models import Purchase


# todo clear ongoing item deletion
# def clear_ongoing_purchase(session, checklist_id, user_id):
#     session \
#         .query(Purchase) \
#         .filter(Purchase.checklist_id == checklist_id, Purchase.buyer_id == user_id, Purchase.in_progress == True) \
#         .delete(synchronize_session=False)
#     session.commit()

def create(session, item_names, checklist_id, purchase_id=None):
    """
    Creates items for the given names (separated by newline). If a purchase is given, the items will be added to it.
    """
    item_name_list = item_names.split('\n')
    item_list = []

    for item_name in item_name_list:
        if item_name.strip() == '':
            continue

        item = Item(item_name.strip(), checklist_id)
        item.purchase_id = purchase_id
        session.add(item)
        item_list.append(item)

    session.commit()


def find_by_checklist(session, checklist_id):
    items = session.query(Item).filter(Item.checklist_id == checklist_id, Item.purchase == None).all()
    return items


def find_for_purchase(session, purchase_id):
    purchase = session.query(Purchase).filter(Purchase.id == purchase_id).one()
    # noinspection PyComparisonWithNone
    items = session \
        .query(Item) \
        .filter(Item.checklist == purchase.checklist) \
        .filter(or_(Item.purchase == None, Item.purchase == purchase)) \
        .order_by(Item.id) \
        .all()
    return items


def find_for_removal(session, checklist_id, user_id):
    return session \
        .query(Item) \
        .filter(Item.checklist_id == checklist_id, Item.purchase_id == None) \
        .filter(or_(Item.deleting_user_id == None, Item.deleting_user_id == user_id)) \
        .order_by(Item.id) \
        .all()


def mark_for_removal(session, user_id, item_id):
    item = session.query(Item).filter(Item.id == item_id).one()
    if item.deleting_user_id is None:
        item.deleting_user_id = user_id
    elif item.deleting_user_id == user_id:
        item.deleting_user_id = None
    else:
        return False

    session.commit()
    return True


def abort_removal(session, checklist_id, user_id):
    session \
        .query(Item) \
        .filter(Item.checklist_id == checklist_id, Item.deleting_user_id == user_id) \
        .update({'deleting_user_id': None})
    session.commit()


def delete_pending(session, checklist_id, user_id):
    item_count = session \
        .query(Item) \
        .filter(Item.checklist_id == checklist_id, Item.deleting_user_id == user_id) \
        .count()

    if item_count == 0:
        return False

    session \
        .query(Item) \
        .filter(Item.checklist_id == checklist_id, Item.deleting_user_id == user_id) \
        .delete(synchronize_session=False)
    session.commit()
    return True
