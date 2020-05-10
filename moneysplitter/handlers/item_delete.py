from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from . import settings, main_menu
from ..db import session_wrapper
from ..db.queries import item_queries, user_queries
from ..helper.entity_select_conversation_builder import ButtonConfig, EntitySelectConversationBuilder
from ..helper.function_wrappers import edit
from ..i18n import trans

BASE_STATE = 0

ACTION_IDENTIFIER = 'item.delete'


def conversation_handler():
    builder = EntitySelectConversationBuilder(
        ACTION_IDENTIFIER,
        item_queries.find_for_removal,
        is_item_selected,
        item_queries.select_for_removal,
        item_queries.abort_removal,
        commit_removal,
        ButtonConfig.BOTH
    )
    return builder.conversation_handler()


def is_item_selected(item):
    return item.deleting_user_id is not None


@session_wrapper
def commit_removal(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    checklist = user_queries.get_selected_checklist(session, user_id)
    success = item_queries.delete_pending(session, checklist.id, query.from_user.id)
    if not success:
        query.answer(trans.t('conversation.no_selection'))
        return BASE_STATE

    text = trans.t(f'{ACTION_IDENTIFIER}.success')
    markup = InlineKeyboardMarkup([[main_menu.link_button(), settings.link_button()]])
    edit(query, text, markup)
    return ConversationHandler.END
