from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ConversationHandler

from ..db import session_wrapper
from ..db.queries import user_queries
from ..i18n import trans
from ..services import response_builder, emojis
from ..services.response_builder import button

BASE_STATE = 0


def conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^users-kick$')],
        states={
            BASE_STATE: [
                CallbackQueryHandler(mark, pattern='^mark-remove-users_[0-9]+_[0-9]+'),
                CallbackQueryHandler(commit, pattern='^continue-remove-users_[0-9]+$'),
            ],
        },
        fallbacks=[CallbackQueryHandler(abort, pattern='^abort-remove-users_[0-9]+$')]
    )


def is_user_being_removed(participant):
    """To be used as a callback for entity_selector_markup"""
    return participant.deleting_user_id is not None


@session_wrapper
def initialize(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    checklist = user_queries.get_selected_checklist(session, user_id)

    if checklist.creator_id != user_id:
        query.answer(trans.t('checklist.participant.remove.permission_denied'))
        return ConversationHandler.END

    text, markup = selection_data(session, checklist, user_id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return BASE_STATE


@session_wrapper
def mark(session, update, context):
    query = update.callback_query
    query_data = response_builder.interpret_data(query)
    deleting_user_id = query.from_user.id
    checklist = user_queries.get_selected_checklist(session, deleting_user_id)

    success = user_queries.mark_for_removal(session, deleting_user_id, query_data['user_id'], checklist.id)
    if not success:
        update.callback_query.answer(trans.t('checklist.participant.remove.already_selected'))
        return BASE_STATE

    text, markup = selection_data(session, checklist, deleting_user_id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return BASE_STATE


def selection_data(session, checklist, user_id):
    participants = user_queries.find_participants_for_removal(session, checklist.id, user_id)
    text = trans.t('checklist.participant.remove.text', name=checklist.name)
    markup = response_builder.entity_selector_markup(participants, is_user_being_removed, checklist.id, 'remove-users')

    return text, markup


@session_wrapper
def commit(session, update, context):
    query = update.callback_query
    deleting_user_id = query.from_user.id
    checklist = user_queries.get_selected_checklist(session, deleting_user_id)

    success = user_queries.delete_pending(session, checklist.id, deleting_user_id)
    if not success:
        query.answer(trans.t('conversation.no_selection'))
        return BASE_STATE

    markup = InlineKeyboardMarkup([[button('checklist-settings', trans.t('checklist.settings.link'), emojis.BACK)]])
    query.edit_message_text(text=trans.t('checklist.participant.remove.success'), reply_markup=markup,
                            parse_mode='Markdown')
    return ConversationHandler.END


@session_wrapper
def abort(session, update, context):
    query = update.callback_query
    deleting_user_id = query.from_user.id
    checklist = user_queries.get_selected_checklist(session, deleting_user_id)

    user_queries.abort_removal(session, checklist.id, deleting_user_id)

    markup = InlineKeyboardMarkup([[button('checklist-settings', trans.t('checklist.settings.link'), emojis.BACK)]])
    query.edit_message_text(text=trans.t('conversation.canceled'), reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END
