from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters, MessageHandler, CommandHandler

from handlers.main_menu_handler import render_main_menu, render_advanced_checklist_menu
from main import cancel_conversation, conv_cancel
from queries import checklist_queries

BASE_STATE = 0


def get_creation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize_creation, pattern='^new_checklist$')],
        states={
            BASE_STATE: [MessageHandler(Filters.text, create)],
        },
        fallbacks=[CallbackQueryHandler(cancel_conversation, 'cancel_conversation')]
    )


# noinspection PyUnusedLocal
def initialize_creation(update, context):
    keyboard = [[InlineKeyboardButton('Back to checklist overview', callback_data='cancel_conversation')]]

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
    render_main_menu(update, context)

    return ConversationHandler.END


def get_removal_handler():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(initialize_removal, pattern='^delete_checklist$')],
        states={
            BASE_STATE: [
                CallbackQueryHandler(abort_removal, pattern='^abort_removal$'),
                MessageHandler(Filters.text, remove)
            ],
        },
        fallbacks=[CommandHandler('cancel', conv_cancel)]
    )


# noinspection PyUnusedLocal
def initialize_removal(update, context):
    update.callback_query.edit_message_text(
        text='You are about to delete the checklist *{}*. This *cannot be undone*. If you are certain about deleting '
             'this checklist, send me the checklist\'s name.'.format(context.user_data['checklist'].name),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('Back to advanced options', callback_data='advanced_options')]
        ]),
        parse_mode='Markdown'
    )

    return BASE_STATE


def abort_removal(update, context):
    render_advanced_checklist_menu(update, context)

    return ConversationHandler.END


def remove(update, context):
    user_input = update.message.text
    checklist = context.user_data['checklist']
    if user_input != checklist.name:
        update.message.reply_text(
            'Your message and the checklist name do not match. Please send the *exact* name.',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('Back to advanced options',
                                      callback_data='advanced_options')]
            ]),
            parse_mode='Markdown'
        )
        return

    checklist_queries.delete(checklist.id, update.message.chat_id)
    update.message.reply_text(
        'The checklist has been deleted.',
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Back to checklist overview', callback_data='checklist_overview')]]
        )
    )

    return ConversationHandler.END
