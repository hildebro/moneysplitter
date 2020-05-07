from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

from . import main_menu
from ..db import session_wrapper
from ..db.queries import purchase_queries, item_queries, user_queries
from ..helper import response_builder
from ..helper.function_wrappers import reply, edit
from ..i18n import trans

ITEM_SELECT_STATE, PRICE_SET_STATE = range(2)

ACTION_IDENTIFIER = 'purchase.create'


def conversation_handler():
    return ConversationHandler(
        entry_points=[entry_handler()],
        states={
            ITEM_SELECT_STATE: [
                select_handler(),
                CallbackQueryHandler(ask_price, pattern=response_builder.continue_pattern(ACTION_IDENTIFIER)),
                MessageHandler(Filters.text, add_item)
            ],
            PRICE_SET_STATE: [MessageHandler(Filters.text, check_price)]
        },
        fallbacks=[abort_handler()]
    )


def is_item_selected(item):
    return item.purchase is not None


def get_select_text(session, user_id):
    checklist = user_queries.get_selected_checklist(session, user_id)
    items = item_queries.find_for_purchase(session, user_id)

    return trans.t(f'{ACTION_IDENTIFIER}.header', name=checklist.name) \
           + '\n\n' \
           + trans.t(f'{ACTION_IDENTIFIER}.text', count=len(items))


def entry_handler():
    return response_builder.entry_handler(
        ACTION_IDENTIFIER,
        get_select_text,
        item_queries.find_for_purchase,
        is_item_selected,
        purchase_queries.create
    )


def select_handler():
    return response_builder.select_handler(
        ACTION_IDENTIFIER,
        get_select_text,
        item_queries.find_for_purchase,
        is_item_selected,
        purchase_queries.mark_item
    )


def abort_handler():
    return response_builder.abort_handler(
        ACTION_IDENTIFIER,
        purchase_queries.delete_in_progress,
    )


@session_wrapper
def add_item(session, update, context):
    message = update.message
    user_id = message.from_user.id
    item_names = message.text

    item_queries.create_for_purchase(session, user_id, item_names)

    text = get_select_text(session, user_id)
    markup = response_builder.entity_select_markup(
        ACTION_IDENTIFIER,
        item_queries.find_for_purchase(session, user_id),
        is_item_selected
    )

    reply(message, text, markup)
    return ITEM_SELECT_STATE


@session_wrapper
def ask_price(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    if not purchase_queries.has_selected_items(session, user_id):
        query.answer(trans.t('conversation.no_selection'))
        return ITEM_SELECT_STATE

    markup = InlineKeyboardMarkup([[response_builder.abort_button(ACTION_IDENTIFIER)]])
    edit(query, trans.t(f'{ACTION_IDENTIFIER}.price.ask'), markup)
    return PRICE_SET_STATE


@session_wrapper
def check_price(session, update, context):
    message = update.message
    user_id = message.from_user.id
    try:
        price_text = message.text.replace(',', '.')
        price = float(price_text)
    except ValueError:
        markup = InlineKeyboardMarkup([[response_builder.abort_button(ACTION_IDENTIFIER)]])
        reply(message, trans.t(f'{ACTION_IDENTIFIER}.price.invalid'), markup)
        return PRICE_SET_STATE

    purchase_queries.finalize_purchase(session, user_id, price)

    text = trans.t(f'{ACTION_IDENTIFIER}.success')
    markup = InlineKeyboardMarkup([[main_menu.link_button()]])
    reply(message, text, markup)
    return ConversationHandler.END
