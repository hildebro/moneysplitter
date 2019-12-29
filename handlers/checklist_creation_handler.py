from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters, MessageHandler, CommandHandler

from handlers.main_menu_handler import render_checklists
from main import conv_cancel
from queries import checklist_queries

BASE_STATE = 0


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^newchecklist$')],
        states={
            BASE_STATE: [MessageHandler(Filters.text, create)],
        },
        fallbacks=[CommandHandler('cancel', conv_cancel)]
    )


def initialize(update, context):
    update.callback_query.edit_message_text(text='What name should the new checklist have?')

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
