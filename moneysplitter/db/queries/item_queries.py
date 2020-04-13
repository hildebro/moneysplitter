from sqlalchemy import or_

from ..models import Item
from ..models import Purchase


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
    return item_list


def remove_all(session, ids_to_remove):
    session.query(Item).filter(Item.id.in_(ids_to_remove)).delete(synchronize_session=False)
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
