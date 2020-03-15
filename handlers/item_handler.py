from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, ConversationHandler, CommandHandler

from db import session_wrapper
from handlers.menu_handler import render_checklist_menu
from main import conv_cancel
from queries import item_queries

ITEM_REMOVAL_MESSAGE = \
    'You are now removing items from checklist *{}*.\n\nClick on items to *(de)select* them for ' \
    'removal.\nWhen you are done, click *Commit* to remove all selected items.\nClick *Abort* to exit ' \
    'without removals. '


@session_wrapper
def add_item(session, update, context):
    if 'checklist' not in context.user_data:
        update.message.reply_text(
            'Sorry, I cannot handle messages while you are browsing the checklist overview.\nIf you were trying to '
            'add items to one of your checklists, you have to enter that checklist\'s main menu first.',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('Back to checklist overview', callback_data='checklist_overview')]]
            )
        )
        return

    item_names = update.message.text
    checklist = context.user_data['checklist']
    items = item_queries.create(session, item_names, checklist.id)
    context.user_data['last_items'] = items

    keyboard = [
        [
            InlineKeyboardButton('Undo', callback_data='undo_last_items'),
            InlineKeyboardButton('Back to main menu', callback_data='checklist_menu_{}'.format(checklist.id))
        ]
    ]
    update.message.reply_text(
        'I successfully added the following items to checklist *{}*:\n\n{}'.format(checklist.name, item_names),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


def undo_last_items(update, context):
    checklist = context.user_data['checklist']
    keyboard = [
        [
            InlineKeyboardButton('Back to main menu', callback_data='checklist_menu_{}'.format(checklist.id))
        ]
    ]

    last_items = context.user_data.pop('last_items', None)
    if last_items is None:
        update.callback_query.edit_message_text(
            text='Sorry, I did not find any items to undo.',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    item_queries.remove_all(map(lambda item: item.id, last_items))
    update.callback_query.edit_message_text(
        text='Successfully undid last added items.',
        reply_markup=InlineKeyboardMarkup(keyboard)
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


def initialize(update, context):
    context.user_data['removal_dict'] = {}
    items = item_queries.find_by_checklist(context.user_data['checklist'].id)
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


def abort(update, context):
    context.user_data['removal_dict'] = None
    render_checklist_menu(update, context)

    return ConversationHandler.END


def commit(update, context):
    ids_to_remove = []
    removal_dict = context.user_data['removal_dict']
    for item_id in removal_dict:
        if '🚫' in removal_dict[item_id]:
            ids_to_remove.append(item_id)

    item_queries.remove_all(ids_to_remove)
    render_checklist_menu(update, context)

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
    update.callback_query.edit_message_text(text=ITEM_REMOVAL_MESSAGE.format(checklist.name),
                                            reply_markup=reply_markup, parse_mode='Markdown')
