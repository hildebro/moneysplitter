from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler

from handlers.basic_callbacks_handler import render_item_menu
from main import conv_cancel
from queries import item_queries

BASE_STATE = 0

MESSAGE_TEXT = 'You are now removing items from checklist *{}*.\n\nClick on items to *(de)select* them for ' \
               'removal.\nWhen you are done, click *Commit* to remove all selected items.\nClick *Abort* to exit ' \
               'without removals. '


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^remove_items$')],
        states={
            BASE_STATE: [
                CallbackQueryHandler(mark_item, pattern='^mark_.+'),
                CallbackQueryHandler(abort, pattern='^abort$'),
                CallbackQueryHandler(commit, pattern='^commit$')
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
    render_item_menu(update, context)

    return ConversationHandler.END


def commit(update, context):
    ids_to_remove = []
    removal_dict = context.user_data['removal_dict']
    for item_id in removal_dict:
        if '🚫' in removal_dict[item_id]:
            ids_to_remove.append(item_id)

    item_queries.remove_all(ids_to_remove)
    render_item_menu(update, context)

    return ConversationHandler.END


def render_removal_buttons(update, context):
    keyboard = []
    removal_dict = context.user_data['removal_dict']
    for item_id in removal_dict:
        keyboard.append([InlineKeyboardButton(removal_dict[item_id], callback_data='mark_{}'.format(item_id))])

    keyboard.append([
        InlineKeyboardButton('Abort', callback_data='abort'),
        InlineKeyboardButton('Commit', callback_data='commit')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text=MESSAGE_TEXT.format(context.user_data['checklist'].name),
                                            reply_markup=reply_markup, parse_mode='Markdown')
