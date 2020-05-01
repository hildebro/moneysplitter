from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ConversationHandler

from ..db import session_wrapper, checklist_queries
from ..db.queries import item_queries
from ..i18n import trans
from ..services import response_builder, emojis
from ..services.response_builder import button


@session_wrapper
def add_item(session, update, context):
    if 'checklist' not in context.user_data:
        markup = InlineKeyboardMarkup([[button('checklist_overview', trans.t('checklist.overview.link'), emojis.BACK)]])
        update.message.reply_text(trans.t('item.add.no_checklist'), reply_markup=markup)
        return

    item_names = update.message.text
    checklist = context.user_data['checklist']
    items = item_queries.create(session, item_names, checklist.id)
    context.user_data['last_items'] = items
    markup = InlineKeyboardMarkup([[
        button('undo_last_items', trans.t('conversation.undo')),
        button(f'checklist-menu_{checklist.id}', trans.t('checklist.menu.link'), emojis.BACK)
    ]])

    update.message.reply_text(
        trans.t('item.add.success', name=checklist.name, items=item_names),
        reply_markup=markup,
        parse_mode='Markdown'
    )


@session_wrapper
def undo_last_items(session, update, context):
    checklist = context.user_data['checklist']
    markup = InlineKeyboardMarkup([[
        button(f'checklist-menu_{checklist.id}', trans.t('checklist.menu.link'), emojis.BACK)
    ]])

    last_items = context.user_data.pop('last_items', None)
    if last_items is None:
        update.callback_query.edit_message_text(text=trans.t('item.undo.unavailable'), reply_markup=markup)
        return

    item_queries.remove_all(session, map(lambda item: item.id, last_items))
    update.callback_query.edit_message_text(
        text=trans.t('item.undo.success'),
        reply_markup=markup
    )


BASE_STATE = 0


def get_removal_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^remove-items_[0-9]+$')],
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
    query_data = response_builder.interpret_data(query)
    user_id = query.from_user.id

    text, markup = build_item_state(session, query_data['checklist_id'], user_id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return BASE_STATE


# noinspection PyUnusedLocal
@session_wrapper
def mark_item(session, update, context):
    query = update.callback_query
    query_data = response_builder.interpret_data(query)
    user_id = query.from_user.id

    success = item_queries.mark_for_removal(session, user_id, query_data['item_id'])
    if not success:
        update.callback_query.answer(trans.t('item.delete.already_selected'))
        return BASE_STATE

    text, markup = build_item_state(session, query_data['checklist_id'], user_id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return BASE_STATE


def build_item_state(session, checklist_id, user_id):
    checklist = checklist_queries.find(session, checklist_id)
    items = item_queries.find_for_removal(session, checklist.id, user_id)
    text = trans.t('item.delete.text', name=checklist.name)
    markup = response_builder.entity_selector_markup(items, is_item_being_removed, checklist.id, 'remove-items')

    return text, markup


# noinspection PyUnusedLocal
@session_wrapper
def abort_removal(session, update, context):
    query = update.callback_query
    query_data = response_builder.interpret_data(query)
    checklist_id = query_data['checklist_id']
    item_queries.abort_removal(session, checklist_id, query.from_user.id)

    markup = response_builder.back_to_main_menu(checklist_id)
    query.edit_message_text(text=trans.t('conversation.cancel'), reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END


# noinspection PyUnusedLocal
@session_wrapper
def commit_removal(session, update, context):
    query = update.callback_query
    query_data = response_builder.interpret_data(query)
    checklist_id = query_data['checklist_id']
    success = item_queries.delete_pending(session, checklist_id, query.from_user.id)
    if not success:
        query.answer(trans.t('conversation.no_selection'))
        return BASE_STATE

    markup = response_builder.back_to_main_menu(checklist_id)
    query.edit_message_text(text=trans.t('item.delete.success'), reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END
