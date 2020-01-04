from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler

from handlers.main_menu_handler import render_main_menu_from_callback
from main import conv_cancel
from queries import item_queries

BASE_STATE = 0


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^remove_items$')],
        states={
            BASE_STATE: [
                CallbackQueryHandler(remove_item, pattern='^ri_.+'),
                CallbackQueryHandler(finish, pattern='^finish$')
            ]
        },
        fallbacks=[CommandHandler('cancel', conv_cancel)]
    )


def initialize(update, context):
    render_items_to_remove(update, context)

    return BASE_STATE


def remove_item(update, context):
    query = update.callback_query
    item_id = query.data.split('_')[-1]
    item_queries.remove(item_id)
    render_items_to_remove(update, context)

    return BASE_STATE


def finish(update, context):
    update.callback_query.edit_message_text(text='Finished removing items.')
    render_main_menu_from_callback(update, context)

    return ConversationHandler.END


def render_items_to_remove(update, context):
    items = item_queries.find_by_checklist(context.user_data['checklist_id'])
    keyboard = []
    for item in items:
        keyboard.append([InlineKeyboardButton(item.name, callback_data='ri_{}'.format(item.id))])

    # todo either buffer table like with purchases or use chat data for buffer
    # keyboard.append([
    #    InlineKeyboardButton('Revert', callback_data='ri'),
    #    InlineKeyboardButton('Abort', callback_data='ap')
    # ])
    keyboard.append([
        InlineKeyboardButton('Finish', callback_data='finish')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text='Choose items to remove from the list:', reply_markup=reply_markup)
