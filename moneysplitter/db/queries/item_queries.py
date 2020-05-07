from sqlalchemy import or_

from . import purchase_queries, user_queries
from ..models import Item


# todo clear ongoing item deletion
# def clear_ongoing_purchase(session, checklist_id, user_id):
#     session \
#         .query(Purchase) \
#         .filter(Purchase.checklist_id == checklist_id, Purchase.buyer_id == user_id, Purchase.in_progress == True) \
#         .delete(synchronize_session=False)
#     session.commit()

def create(session, item_names, checklist_id, purchase_id=None):
    item_name_list = item_names.split('\n')

    for item_name in item_name_list:
        if item_name.strip() == '':
            continue

        item = Item(item_name.strip(), checklist_id)
        item.purchase_id = purchase_id
        session.add(item)

    session.commit()


def create_for_purchase(session, user_id, item_names):
    checklist = user_queries.get_selected_checklist(session, user_id)
    purchase = purchase_queries.find_in_progress(session, user_id)
    create(session, item_names, checklist.id, purchase.id)


def find_by_checklist(session, checklist_id):
    items = session.query(Item).filter(Item.checklist_id == checklist_id, Item.purchase == None).all()
    return items


def find_for_purchase(session, user_id):
    purchase = purchase_queries.find_in_progress(session, user_id)
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
