from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters, MessageHandler

from handlers.main_menu_handler import render_checklists
from main import cancel_conversation
from queries import checklist_queries

BASE_STATE = 0


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^new_checklist$')],
        states={
            BASE_STATE: [MessageHandler(Filters.text, create)],
        },
        fallbacks=[CallbackQueryHandler(cancel_conversation, 'cancel_conversation')]
    )


# noinspection PyUnusedLocal
def initialize(update, context):
    keyboard = [[InlineKeyboardButton('Back to main menu', callback_data='cancel_conversation')]]

    update.callback_query.edit_message_text(
        text='You are about to create a new checklist! Please send me a message with your desired name.',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return BASE_STATE


def create(update, context):
    checklist_name = update.message.text
    user_id = update.message.from_user.id

    if checklist_queries.exists(user_id, checklist_name):
        update.message.reply_text('You already have a checklist with that name. Please provide a new name or stop the '
                                  'process with /cancel.')

        return BASE_STATE

    checklist_queries.create(user_id, checklist_name)
    update.message.reply_text('Checklist created.')
    render_checklists(update, context)

    return ConversationHandler.END
