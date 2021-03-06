from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from . import main_menu, settings
from ..db import session_wrapper
from ..db.queries import user_queries, participant_queries
from ..helper.entity_select_conversation_builder import EntitySelectConversationBuilder, AbortTarget
from ..helper.function_wrappers import edit
from ..i18n import trans

BASE_STATE = 0

ACTION_IDENTIFIER = 'participant.delete'


def conversation_handler():
    builder = EntitySelectConversationBuilder(
        ACTION_IDENTIFIER,
        participant_queries.find_for_removal,
        is_participant_selected,
        participant_queries.mark_for_removal,
        participant_queries.abort_removal,
        AbortTarget.SETTINGS,
        commit_removal,
        user_queries.set_participant_delete
    )
    return builder.conversation_handler()


@session_wrapper
def commit_removal(session, update, context):
    query = update.callback_query
    deleting_user_id = query.from_user.id

    success = participant_queries.commit_removal(session, deleting_user_id)
    if not success:
        query.answer(trans.t('conversation.no_selection'))
        return BASE_STATE

    markup = InlineKeyboardMarkup([[main_menu.link_button(), settings.link_button()]])
    edit(query, trans.t(f'{ACTION_IDENTIFIER}.success'), markup)
    return ConversationHandler.END


def is_participant_selected(participant):
    return participant.deleting_user_id is not None
