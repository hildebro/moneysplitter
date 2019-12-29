from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, Filters

from handlers.main_menu_handler import render_checklists
from main import conv_cancel
from queries import item_queries

BASE_STATE = 0


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^additems$')],
        states={
            BASE_STATE: [
                CommandHandler('finish', finish),
                MessageHandler(Filters.text, add_item)
            ]
        },
        fallbacks=[CommandHandler('cancel', conv_cancel)]
    )


def initialize(update, context):
    checklist_name = context.chat_data['checklist_names'][context.chat_data['checklist_id']]
    update.callback_query.edit_message_text(text='Send me item names (one at a time) to add them to {}. Use /finish '
                                                 'when you are done.'.format(checklist_name))

    return BASE_STATE


def add_item(update, context):
    item_name = update.message.text
    checklist_id = context.chat_data['checklist_id']
    item_queries.create(item_name, checklist_id)
    update.message.reply_text(
        '{} added to {}. Provide more items or stop the action with /finish.'.format(
            item_name, context.chat_data['checklist_names'][checklist_id]
        )
    )

    return BASE_STATE


def finish(update, context):
    update.message.reply_text('Finished adding items.')
    render_checklists(update, context)

    return ConversationHandler.END
