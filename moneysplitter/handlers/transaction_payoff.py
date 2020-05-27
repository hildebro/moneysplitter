from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from . import main_menu
from ..db import session_wrapper
from ..db.queries import transaction_queries
from ..helper.entity_select_conversation_builder import EntitySelectConversationBuilder, AbortTarget
from ..helper.function_wrappers import edit
from ..i18n import trans

BASE_STATE = 0

ACTION_IDENTIFIER = 'transaction.payoff'


def conversation_handler():
    builder = EntitySelectConversationBuilder(
        ACTION_IDENTIFIER,
        transaction_queries.find_for_payoff,
        is_transaction_selected,
        transaction_queries.select_for_payoff,
        transaction_queries.abort_payoff,
        AbortTarget.MAIN_MENU,
        commit_payoff
    )
    return builder.conversation_handler()


def is_transaction_selected(transaction):
    return transaction.payoff_user_id is not None


@session_wrapper
def commit_payoff(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    success = transaction_queries.commit_payoff(session, user_id)
    if not success:
        query.answer(trans.t('conversation.no_selection'))
        return BASE_STATE

    text = trans.t(f'{ACTION_IDENTIFIER}.success')
    markup = InlineKeyboardMarkup([[main_menu.link_button()]])
    edit(query, text, markup)
    return ConversationHandler.END
