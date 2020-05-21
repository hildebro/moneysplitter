from sqlalchemy import or_

from ..models import Transaction
from ..queries import user_queries


def find(session, user_id):
    checklist = user_queries.get_selected_checklist(session, user_id)
    transactions = session \
        .query(Transaction) \
        .filter(Transaction.checklist == checklist) \
        .filter(or_(Transaction.giver_id == user_id, Transaction.receiver_id == user_id)) \
        .all()
    return transactions
