import operator

from ..db import Transaction
from ..db.queries import participant_queries, transaction_queries


def write_off(session, checklist, purchases):
    if len(purchases) == 0:
        return []

    # sum up purchase prices -  both per user and as a whole
    user_price_mapping = {}
    full_price = 0
    for purchase in purchases:
        full_price += purchase.leftover_price
        if purchase.buyer.id not in user_price_mapping:
            user_price_mapping[purchase.buyer.id] = purchase.leftover_price
        else:
            user_price_mapping[purchase.buyer.id] += purchase.leftover_price

    # add entry with price of 0 for everyone who hasn't purchased anything
    participants = participant_queries.find(session, checklist.id)
    for participant in participants:
        if participant.user_id not in user_price_mapping:
            user_price_mapping[participant.user_id] = 0

    average_price = full_price / len(participants)

    # dictionaries inherently have no order, but we need the price mapping to be sorted ascending by price.
    # the following line converts {user => price} into {index => (user, price)} with the index representing the order.
    user_price_mapping = sorted(user_price_mapping.items(), key=operator.itemgetter(1))

    # our goal is for everybody to spend the average price of the outstanding purchases. that's why we create
    # transactions in which the people who spent less than the average give money to the ones that spent above average.
    # in order to have as few transactions as possible, we match the lowest paying user to the highest paying user.
    # as transactions are made, the index of lowest payer moves up while the index of highest payer moves down.
    # when those indices meet, everyone should be equal.
    low_end_index = 0
    high_end_index = len(user_price_mapping) - 1
    transactions = []
    while low_end_index < high_end_index:
        low_end_id = user_price_mapping[low_end_index][0]
        low_end_amount = user_price_mapping[low_end_index][1]
        high_end_id = user_price_mapping[high_end_index][0]
        high_end_amount = user_price_mapping[high_end_index][1]

        low_end_underpay = average_price - low_end_amount
        if low_end_underpay == 0:
            # low end user sent enough to reach the average; move that index forward
            low_end_index += 1
            continue

        high_end_overpay = high_end_amount - average_price
        if high_end_overpay == 0:
            # high end user received enough to reach the average; move that index backward
            high_end_index -= 1
            continue

        # now we need to find out how much money low end should send to high end.
        # case 1: low end is closer to the average => low end can send his full debt amount to high end.
        #         this means low end is now at average, so we increment the low end index next turn
        # case 2: high end is closer to the average => low end will just send high end's overpay to him.
        #         this means high end is now at average, so we decrement the high end index next turn
        amount_to_transfer = low_end_underpay if low_end_underpay < high_end_overpay else high_end_overpay
        new_low_end_amount = low_end_amount + amount_to_transfer
        new_high_end_amount = high_end_amount - amount_to_transfer

        # update the price mapping to reflect the money transfer
        user_price_mapping[low_end_index] = (low_end_id, new_low_end_amount)
        user_price_mapping[high_end_index] = (high_end_id, new_high_end_amount)

        # create new transaction for what happened in this iteration step
        transactions.append(Transaction(checklist.id, low_end_id, high_end_id, amount_to_transfer))

    # adding a transaction for every purchase distribution
    # we don't care about potential duplicates here since transaction_queries.add_all will aggregate it anyway
    for purchase in purchases:
        for distribution in purchase.distributions:
            # no need to create a transaction, if the buyer bought items for himself
            if distribution.user_id != purchase.buyer_id:
                transactions.append(
                    Transaction(checklist.id, distribution.user_id, purchase.buyer_id, distribution.amount))

        # mark everything as written off
        purchase.written_off = True

    if len(transactions) > 0:
        transaction_queries.add_all(session, checklist, transactions)
