from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from . import main_menu, settings
from ..db import session_wrapper
from ..db.queries import user_queries
from ..helper.entity_select_conversation_builder import EntitySelectConversationBuilder, BackButtonConfig
from ..helper.function_wrappers import edit
from ..i18n import trans

BASE_STATE = 0

ACTION_IDENTIFIER = 'participant.delete'


def conversation_handler():
    builder = EntitySelectConversationBuilder(
        ACTION_IDENTIFIER,
        user_queries.find_participants_for_removal,
        is_participant_selected,
        user_queries.mark_for_removal,
        user_queries.abort_removal,
        commit_removal,
        BackButtonConfig.BOTH
    )
    return builder.conversation_handler()


@session_wrapper
def commit_removal(session, update, context):
    query = update.callback_query
    deleting_user_id = query.from_user.id
    checklist = user_queries.get_selected_checklist(session, deleting_user_id)

    success = user_queries.delete_pending(session, checklist.id, deleting_user_id)
    if not success:
        query.answer(trans.t('conversation.no_selection'))
        return BASE_STATE

    markup = InlineKeyboardMarkup([[main_menu.link_button(), settings.link_button()]])
    edit(query, trans.t(f'{ACTION_IDENTIFIER}.success'), markup)
    return ConversationHandler.END


def is_participant_selected(participant):
    return participant.deleting_user_id is not None
