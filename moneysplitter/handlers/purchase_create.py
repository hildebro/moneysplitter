from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler, MessageHandler, Filters

from . import main_menu
from ..db import session_wrapper
from ..db.queries import purchase_queries, item_queries
from ..helper import entity_select_conversation_builder
from ..helper.entity_select_conversation_builder import EntitySelectConversationBuilder, ButtonConfig
from ..helper.function_wrappers import reply, edit
from ..i18n import trans

ITEM_SELECT_STATE, PRICE_SET_STATE = range(2)

ACTION_IDENTIFIER = 'purchase.create'


def conversation_handler():
    builder = EntitySelectConversationBuilder(
        ACTION_IDENTIFIER,
        item_queries.find_for_purchase,
        is_item_selected,
        purchase_queries.mark_item,
        purchase_queries.delete_in_progress,
        ask_price,
        ButtonConfig.MAIN_MENU,
        purchase_queries.create,
        [MessageHandler(Filters.text, check_price)],
        item_queries.create_for_purchase
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

    markup = InlineKeyboardMarkup([[entity_select_conversation_builder.abort_button(ACTION_IDENTIFIER)]])
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
        markup = InlineKeyboardMarkup([[entity_select_conversation_builder.abort_button(ACTION_IDENTIFIER)]])
        reply(message, trans.t(f'{ACTION_IDENTIFIER}.price.invalid'), markup)
        return PRICE_SET_STATE

    purchase_queries.finalize_purchase(session, user_id, price)

    text = trans.t(f'{ACTION_IDENTIFIER}.success')
    markup = InlineKeyboardMarkup([[main_menu.link_button()]])
    reply(message, text, markup)
    return ConversationHandler.END
