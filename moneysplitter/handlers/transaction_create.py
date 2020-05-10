import operator

from telegram import InlineKeyboardMarkup

from ..db import session_wrapper, purchase_queries, checklist_queries, user_queries
from ..db.models import Transaction
from ..helper import emojis
from ..helper.function_wrappers import button
from ..i18n import trans

ACTION_IDENTIFIER = 'transaction.create'


@session_wrapper
def info_callback(session, update, context):
    query = update.callback_query
    checklist = user_queries.get_selected_checklist(session, query.from_user.id)
    purchases = purchase_queries.find_by_checklist(session, checklist.id)

    text = trans.t(f'{ACTION_IDENTIFIER}.text', count=len(purchases))
    markup = InlineKeyboardMarkup([[
        button('checklist-menu', trans.t('checklist.menu.link'), emojis.BACK),
        button(f'{ACTION_IDENTIFIER}.execute', trans.t(f'{ACTION_IDENTIFIER}.link'), emojis.MONEY)
    ]])
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')


@session_wrapper
def execute_callback(session, update, context):
    query = update.callback_query
    checklist = user_queries.get_selected_checklist(session, query.from_user.id)
    purchases = purchase_queries.find_by_checklist(session, checklist.id)

    if len(purchases) == 0:
        query.answer(trans.t(f'{ACTION_IDENTIFIER}.no_purchases'))
        return

    user_price_mapping = {}
    full_price = 0
    # sum up purchase prices
    for purchase in purchases:
        full_price += purchase.price
        if purchase.buyer.id not in user_price_mapping:
            user_price_mapping[purchase.buyer.id] = purchase.price
        else:
            user_price_mapping[purchase.buyer.id] += purchase.price

    # add entry with price of 0 for everyone who hasn't purchased anything
    participants = checklist_queries.find_participants(session, checklist.id)
    for participant in participants:
        if participant.user_id not in user_price_mapping:
            user_price_mapping[participant.user_id] = 0

    # dictionaries inherently have no order, but we need the price mapping to be sorted ascending by price.
    # this line converts {user => price} into {index => (user, price)} with the index representing the order.
    user_price_mapping = sorted(user_price_mapping.items(), key=operator.itemgetter(1))
    average_price = full_price / len(participants)

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

    session.add_all(transactions)
    purchase_queries.write_off(session, checklist.id)

    transaction_info = '\n'.join(map(lambda transaction: transaction.display_name(), transactions))
    update.callback_query.edit_message_text(
        text=trans.t(f'{ACTION_IDENTIFIER}.success', transactions=transaction_info),
        reply_markup=InlineKeyboardMarkup([[button('checklist-menu', trans.t('checklist.menu.link'), emojis.BACK)]]),
        parse_mode='Markdown'
    )
