from telegram.ext import CallbackQueryHandler, ConversationHandler

from ..db import session_wrapper, checklist_queries
from ..db.queries import user_queries
from ..i18n import trans
from ..services import response_builder

BASE_STATE = 0


def get_removal_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^remove-users_[0-9]+$')],
        states={
            BASE_STATE: [
                CallbackQueryHandler(mark_user, pattern='^mark-remove-users_[0-9]+_[0-9]+'),
                CallbackQueryHandler(commit_removal, pattern='^continue-remove-users_[0-9]+$'),
            ],
        },
        fallbacks=[CallbackQueryHandler(abort_removal, pattern='^abort-remove-users_[0-9]+$')]
    )


def is_user_being_removed(user):
    """To be used as a callback for entity_selector_markup"""
    return user.deleting_user_id is not None


# noinspection PyUnusedLocal
@session_wrapper
def initialize(session, update, context):
    query = update.callback_query
    query_data = response_builder.interpret_data(query)
    user_id = query.from_user.id

    text, markup = build_user_state(session, query_data['checklist_id'], user_id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return BASE_STATE


# noinspection PyUnusedLocal
@session_wrapper
def mark_user(session, update, context):
    query = update.callback_query
    query_data = response_builder.interpret_data(query)
    user_id = query.from_user.id

    success = user_queries.mark_for_removal(session, user_id, query_data['participant_id'])
    if not success:
        update.callback_query.answer(trans.t('checklist.participant.delete.already_selected'))
        return BASE_STATE

    text, markup = build_user_state(session, query_data['checklist_id'], user_id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return BASE_STATE


def build_user_state(session, checklist_id, user_id):
    checklist = checklist_queries.find(session, checklist_id)
    participants = user_queries.find_participants_for_removal(session, checklist.id, user_id)
    text = trans.t('checklist.participant.remove.text', name=checklist.name)
    markup = response_builder.entity_selector_markup(participants, is_user_being_removed, checklist.id, 'remove-users')

    return text, markup


# noinspection PyUnusedLocal
@session_wrapper
def abort_removal(session, update, context):
    query = update.callback_query
    query_data = response_builder.interpret_data(query)
    checklist_id = query_data['checklist_id']
    user_queries.abort_removal(session, checklist_id, query.from_user.id)

    markup = response_builder.back_to_main_menu(checklist_id)
    query.edit_message_text(text=trans.t('conversation.cancel'), reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END


# noinspection PyUnusedLocal
@session_wrapper
def commit_removal(session, update, context):
    query = update.callback_query
    query_data = response_builder.interpret_data(query)
    checklist_id = query_data['checklist_id']
    success = user_queries.delete_pending(session, checklist_id, query.from_user.id)
    if not success:
        query.answer(trans.t('conversation.no_selection'))
        return BASE_STATE

    markup = response_builder.back_to_main_menu(checklist_id)
    query.edit_message_text(text=trans.t('checklist.participant.remove.success'), reply_markup=markup,
                            parse_mode='Markdown')
    return ConversationHandler.END
