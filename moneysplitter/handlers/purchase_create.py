from telegram import InlineKeyboardMarkup
from telegram.ext import MessageHandler, Filters, CallbackQueryHandler, ConversationHandler

from . import main_menu
from ..db import session_wrapper
from ..db.queries import purchase_queries, item_queries, transaction_queries
from ..helper import write_off_calculator
from ..helper.calculator import Calculator
from ..helper.entity_select_conversation_builder import EntitySelectConversationBuilder, AbortTarget, abort_button
from ..helper.function_wrappers import reply, edit, button
from ..i18n import trans

ITEM_SELECT_STATE, PRICE_SET_STATE, WRITE_OFF_SET_STATE = range(3)

ACTION_IDENTIFIER = 'purchase.create'


def conversation_handler():
    builder = EntitySelectConversationBuilder(
        ACTION_IDENTIFIER,
        item_queries.find_for_purchase,
        is_item_selected,
        purchase_queries.mark_item,
        purchase_queries.clear_purchase_data,
        AbortTarget.MAIN_MENU,
        ask_price,
        purchase_queries.create,
        [
            [MessageHandler(Filters.text, check_price)],
            [
                CallbackQueryHandler(write_off_now, pattern=f'^{ACTION_IDENTIFIER}.write_off_now$'),
                CallbackQueryHandler(write_off_later, pattern=f'^{ACTION_IDENTIFIER}.write_off_later$')
            ]
        ],
        item_queries.create_for_purchase,
        True
    )
    return builder.conversation_handler()


def is_item_selected(item):
    return item.purchase is not None


@session_wrapper
def ask_price(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    if not purchase_queries.has_selected_items(session, user_id):
        query.answer(trans.t('conversation.no_selection'))
        return ITEM_SELECT_STATE

    markup = InlineKeyboardMarkup([[abort_button(ACTION_IDENTIFIER, AbortTarget.MAIN_MENU)]])
    edit(query, trans.t(f'{ACTION_IDENTIFIER}.price.ask'), markup)
    return PRICE_SET_STATE


@session_wrapper
def check_price(session, update, context):
    message = update.message
    user_id = message.from_user.id
    try:
        # replacing commas with dots to turn all numbers into valid floats
        price_text = message.text.replace(',', '.')
        price = Calculator.evaluate(price_text)
    except SyntaxError:
        markup = InlineKeyboardMarkup([[abort_button(ACTION_IDENTIFIER, AbortTarget.MAIN_MENU)]])
        reply(message, trans.t(f'{ACTION_IDENTIFIER}.price.invalid'), markup)
        return PRICE_SET_STATE

    purchase_queries.set_price(session, user_id, price)

    text = trans.t(f'{ACTION_IDENTIFIER}.ask_write_off')
    markup = InlineKeyboardMarkup([[
        button(f'{ACTION_IDENTIFIER}.write_off_now', trans.t(f'{ACTION_IDENTIFIER}.write_off_now')),
        button(f'{ACTION_IDENTIFIER}.write_off_later', trans.t(f'{ACTION_IDENTIFIER}.write_off_later'))
    ]])
    reply(message, text, markup)
    return WRITE_OFF_SET_STATE


@session_wrapper
def write_off_now(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    purchase = purchase_queries.find_in_progress(session, user_id)
    checklist = purchase.checklist

    transactions = write_off_calculator.write_off(session, checklist, [purchase])
    if len(transactions) > 0:
        transaction_queries.add_all(session, checklist, transactions)
    purchase_queries.write_off_single(session, purchase)
    purchase_queries.set_not_in_progress(session, user_id)

    edit(query, trans.t(f'{ACTION_IDENTIFIER}.write_off_success'), InlineKeyboardMarkup([[main_menu.link_button()]]))
    return ConversationHandler.END


@session_wrapper
def write_off_later(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    purchase_queries.set_not_in_progress(session, user_id)

    text, markup = main_menu.checklist_menu_data(session, user_id)
    edit(query, text, markup)
    return ConversationHandler.END
