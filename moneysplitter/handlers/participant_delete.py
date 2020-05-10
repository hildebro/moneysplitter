from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ConversationHandler

from . import main_menu, settings
from ..db import session_wrapper
from ..db.queries import user_queries
from ..helper import response_builder
from ..helper.function_wrappers import edit
from ..i18n import trans

BASE_STATE = 0

ACTION_IDENTIFIER = 'participant.delete'


def conversation_handler():
    return ConversationHandler(
        entry_points=[entry_handler()],
        states={
            BASE_STATE: [
                select_handler(),
                CallbackQueryHandler(commit_removal, pattern=response_builder.continue_pattern(ACTION_IDENTIFIER)),
            ]
        },
        fallbacks=[abort_handler()]
    )


def is_participant_selected(participant):
    """To be used as a callback for entity_selector_markup"""
    return participant.deleting_user_id is not None


def get_select_text(session, user_id):
    checklist = user_queries.get_selected_checklist(session, user_id)
    return trans.t(f'{ACTION_IDENTIFIER}.text', name=checklist.name)


def entry_handler():
    return response_builder.entry_handler(
        ACTION_IDENTIFIER,
        get_select_text,
        user_queries.find_participants_for_removal,
        is_participant_selected,
    )


def select_handler():
    return response_builder.select_handler(
        ACTION_IDENTIFIER,
        get_select_text,
        user_queries.find_participants_for_removal,
        is_participant_selected,
        user_queries.mark_for_removal
    )


def abort_handler():
    return response_builder.abort_handler(
        ACTION_IDENTIFIER,
        user_queries.abort_removal,
    )


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
