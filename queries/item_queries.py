from db import get_session
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
    items = session.query(Item).filter(Item.checklist_id == checklist_id).all()
    session.close()
    return items
