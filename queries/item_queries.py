from db import get_session
from models.item import Item


def create(item_name, checklist_id):
    session = get_session()
    session.add(Item(item_name, checklist_id))
    session.commit()
    session.close()
