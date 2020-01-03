import operator

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler

from handlers.main_menu_handler import render_checklists_from_callback
from main import conv_cancel
from queries import user_queries, purchase_queries, checklist_queries

BASE_STATE = 0


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^equalize$')],
        states={
            BASE_STATE: [
                CallbackQueryHandler(buffer_purchase, pattern='^bp_.+'),
                CallbackQueryHandler(revert_purchase, pattern='^rp$'),
                CallbackQueryHandler(finish, pattern='^fe$'),
                CallbackQueryHandler(abort, pattern='^ae$')
            ]
        },
        fallbacks=[CommandHandler('cancel', conv_cancel)]
    )


def initialize(update, context):
    context.user_data['buffered_purchases'] = []
    render_purchases_to_equalize(update, context)

    return BASE_STATE


def buffer_purchase(update, context):
    query = update.callback_query
    purchase_id = query.data.split('_')[-1]
    context.user_data['buffered_purchases'].append(int(purchase_id))
    render_purchases_to_equalize(update, context)

    return BASE_STATE


def revert_purchase(update, context):
    buffered_purchases = context.user_data['buffered_purchases']
    if not buffered_purchases:
        update.callback_query.answer('Nothing to revert.')
        return

    buffered_purchases.pop()
    render_purchases_to_equalize(update, context)

    return BASE_STATE


def render_purchases_to_equalize(update, context):
    purchases = purchase_queries.find_to_equalize(context.user_data['checklist_id'])
    keyboard = []
    for purchase in purchases:
        if purchase.id not in context.user_data['buffered_purchases']:
            keyboard.append([InlineKeyboardButton(
                '{} spent {}'.format(purchase.buyer.username, purchase.get_price()),
                callback_data='bp_{}'.format(purchase.id)
            )])

    keyboard.append([
        InlineKeyboardButton('Revert', callback_data='rp'),
        InlineKeyboardButton('Abort', callback_data='ae')
    ])
    keyboard.append([
        InlineKeyboardButton('Finish', callback_data='fe')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text='Choose purchases to equalize:', reply_markup=reply_markup)


def abort(update, context):
    update.callback_query.edit_message_text(text='Equalization aborted.')
    render_checklists_from_callback(update, context, True)

    return ConversationHandler.END


def finish(update, context):
    summed_purchases = {}
    average_price = 0
    # sum up purchase prices
    purchases = purchase_queries.find_by_ids(context.user_data['buffered_purchases'])
    for purchase in purchases:
        average_price += purchase.get_price()
        if purchase.buyer.id not in summed_purchases:
            summed_purchases[purchase.buyer.id] = purchase.get_price()
        else:
            summed_purchases[purchase.buyer.id] += purchase.get_price()

    # add entry with price of 0 for everyone who hasn't purchased anything
    participants = checklist_queries.find_participants(context.user_data['checklist_id'])
    for participant in participants:
        if participant.id not in summed_purchases:
            summed_purchases[participant.id] = 0

    # sort by price (has to be a tuple now)
    sorted_purchases = sorted(summed_purchases.items(), key=operator.itemgetter(1))
    average_price /= len(summed_purchases)
    lowboi = 0
    highboi = len(sorted_purchases) - 1
    transactions = []
    while lowboi < highboi:
        to_give = average_price - sorted_purchases[lowboi][1]
        if to_give == 0:
            lowboi += 1
            continue

        to_get = sorted_purchases[highboi][1] - average_price
        if to_get == 0:
            highboi -= 1
            continue

        if to_give > to_get:
            to_give = to_get

        sorted_purchases[lowboi] = (sorted_purchases[lowboi][0], sorted_purchases[lowboi][1] + to_give)
        sorted_purchases[highboi] = (sorted_purchases[highboi][0], sorted_purchases[highboi][1] - to_give)

        transactions.append({
            'from': sorted_purchases[lowboi][0],
            'to': sorted_purchases[highboi][0],
            'amount': to_give
        })

    purchase_queries.equalize(context.user_data['buffered_purchases'])

    transaction_message = 'The chosen purchases have been equalized under the assumption that the following ' \
                          'transactions will be made:\n '
    for transaction in transactions:
        transaction_message += '{} has to send {} to {}\n'.format(
            user_queries.find_username(transaction['from']),
            transaction['amount'],
            user_queries.find_username(transaction['to'])
        )
    update.callback_query.edit_message_text(text=transaction_message)

    render_checklists_from_callback(update, context, True)

    return ConversationHandler.END
