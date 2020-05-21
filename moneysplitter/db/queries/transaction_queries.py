from sqlalchemy import or_, tuple_

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


def add_all(session, checklist, new_transactions):
    """
    for any pair of users, there should be at most a single transaction entity between them per checklist.
    so instead of simply persisting the new transactions, we check for existing ones with matching users.
    if we find matches, we update the old transactions. otherwise, we add the new ones.
    """
    user_tuples = list(map(lambda transaction: (transaction.giver_id, transaction.receiver_id), new_transactions))
    # we need to find matches in both directions of giver/receiver, so we add the inverse tuples to themselves
    user_tuples += [user_tuple[::-1] for user_tuple in user_tuples]

    old_transactions = session \
        .query(Transaction) \
        .filter(Transaction.checklist == checklist,
                tuple_(Transaction.giver_id, Transaction.receiver_id).in_(user_tuples)) \
        .all()

    for new_transaction in new_transactions:
        _merge_data(session, new_transaction, old_transactions)

    session.commit()


def _merge_data(session, new_transaction, old_transactions):
    for old_transaction in old_transactions:
        if new_transaction.giver_id == old_transaction.giver_id and new_transaction.receiver_id == old_transaction.receiver_id:
            # matching giver/receiver pair exists: increase old transaction amount
            old_transaction.amount += new_transaction.amount
            return

        if new_transaction.giver_id == old_transaction.receiver_id and new_transaction.receiver_id == old_transaction.giver_id:
            # inverse giver/receiver pair exists: some special logic required...
            if new_transaction.amount == old_transaction.amount:
                # transaction amounts even each other out: delete old transaction
                session.delete(old_transaction)
                return

            old_transaction.amount -= new_transaction.amount
            if old_transaction.amount < 0:
                # we don't want negative transaction amounts, so we switch giver/receiver and inverse the amount
                old_transaction.giver = new_transaction.receiver
                old_transaction.receiver = new_transaction.giver
                old_transaction.amount *= -1

            return

    # we didn't find any matches, so the new transaction has a unique giver/receiver pair
    session.add(new_transaction)
