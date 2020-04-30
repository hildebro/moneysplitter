from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, ConversationHandler, CommandHandler

from ..db import session_wrapper
from ..db.queries import item_queries
from ..handlers.menu_handler import conv_cancel
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
        entry_points=[CallbackQueryHandler(initialize, pattern='^remove_items$')],
        states={
            BASE_STATE: [
                CallbackQueryHandler(mark_item, pattern='^mark_[0-9]+$'),
                CallbackQueryHandler(abort, pattern='^abort_[0-9]+$'),
                CallbackQueryHandler(commit, pattern='^commit_[0-9]+$')
            ]
        },
        fallbacks=[CommandHandler('cancel', conv_cancel)]
    )


@session_wrapper
def initialize(session, update, context):
    context.user_data['removal_dict'] = {}
    items = item_queries.find_by_checklist(session, context.user_data['checklist'].id)
    for item in items:
        context.user_data['removal_dict'][item.id] = item.name

    render_removal_buttons(update, context)

    return BASE_STATE


def mark_item(update, context):
    query = update.callback_query
    item_id = int(query.data.split('_')[-1])
    item_name = context.user_data['removal_dict'][item_id]
    if '🚫' in item_name:
        item_name = item_name.replace('🚫', '')
    else:
        item_name = '🚫' + item_name + '🚫'

    context.user_data['removal_dict'][item_id] = item_name
    render_removal_buttons(update, context)

    return BASE_STATE


@session_wrapper
def abort(session, update, context):
    context.user_data['removal_dict'] = None
    text, markup = response_builder.checklist_menu(session, update.callback_query.from_user, context)
    update.callback_query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return ConversationHandler.END


@session_wrapper
def commit(session, update, context):
    ids_to_remove = []
    removal_dict = context.user_data['removal_dict']
    for item_id in removal_dict:
        if '🚫' in removal_dict[item_id]:
            ids_to_remove.append(item_id)

    if len(ids_to_remove) == 0:
        update.callback_query.answer(trans.t('conversation.no_selection'))
        return BASE_STATE

    item_queries.remove_all(session, ids_to_remove)
    text, markup = response_builder.checklist_menu(session, update.callback_query.from_user, context)
    update.callback_query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return ConversationHandler.END


def render_removal_buttons(update, context):
    checklist = context.user_data['checklist']
    removal_dict = context.user_data['removal_dict']

    keyboard = []
    for item_id in removal_dict:
        keyboard.append([InlineKeyboardButton(removal_dict[item_id], callback_data='mark_{}'.format(item_id))])
    keyboard.append([
        InlineKeyboardButton('Abort', callback_data='abort_{}'.format(checklist.id)),
        InlineKeyboardButton('Commit', callback_data='commit_{}'.format(checklist.id))
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text=trans.t('item.delete', name=checklist.name),
                                            reply_markup=reply_markup, parse_mode='Markdown')
