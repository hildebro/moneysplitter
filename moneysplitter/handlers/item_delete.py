from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ConversationHandler

from ..db import session_wrapper
from ..db.queries import item_queries, user_queries
from ..i18n import trans
from ..services import response_builder, emojis
from ..services.response_builder import button

BASE_STATE = 0


def get_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^items-delete+$')],
        states={
            BASE_STATE: [
                CallbackQueryHandler(mark_item, pattern='^mark-remove-items_[0-9]+_[0-9]+'),
                CallbackQueryHandler(commit_removal, pattern='^continue-remove-items_[0-9]+$'),
            ],
        },
        fallbacks=[CallbackQueryHandler(abort_removal, pattern='^abort-remove-items_[0-9]+$')]
    )


def is_item_being_removed(item):
    """To be used as a callback for entity_selector_markup"""
    return item.deleting_user_id is not None


# noinspection PyUnusedLocal
@session_wrapper
def initialize(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    checklist = user_queries.get_selected_checklist(session, user_id)

    text, markup = selection_data(session, checklist, user_id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return BASE_STATE


# noinspection PyUnusedLocal
@session_wrapper
def mark_item(session, update, context):
    query = update.callback_query
    query_data = response_builder.interpret_data(query)
    user_id = query.from_user.id
    checklist = user_queries.get_selected_checklist(session, user_id)

    success = item_queries.mark_for_removal(session, user_id, query_data['item_id'])
    if not success:
        update.callback_query.answer(trans.t('item.delete.already_selected'))
        return BASE_STATE

    text, markup = selection_data(session, checklist, user_id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return BASE_STATE


def selection_data(session, checklist, user_id):
    items = item_queries.find_for_removal(session, checklist.id, user_id)
    text = trans.t('item.delete.text', name=checklist.name)
    markup = response_builder.entity_selector_markup(items, is_item_being_removed, checklist.id, 'remove-items')

    return text, markup


@session_wrapper
def abort_removal(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    checklist = user_queries.get_selected_checklist(session, user_id)
    item_queries.abort_removal(session, checklist.id, user_id)

    markup = InlineKeyboardMarkup([[button('checklist-settings', trans.t('checklist.settings.link'), emojis.BACK)]])
    query.edit_message_text(text=trans.t('conversation.canceled'), reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END


@session_wrapper
def commit_removal(session, update, context):
    query = update.callback_query
    query_data = response_builder.interpret_data(query)
    checklist_id = query_data['checklist_id']
    success = item_queries.delete_pending(session, checklist_id, query.from_user.id)
    if not success:
        query.answer(trans.t('conversation.no_selection'))
        return BASE_STATE

    markup = InlineKeyboardMarkup([[button('checklist-settings', trans.t('checklist.settings.link'), emojis.BACK)]])
    query.edit_message_text(text=trans.t('item.delete.success'), reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END
