from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters, MessageHandler, CommandHandler

from .menu_handler import cancel_conversation, conv_cancel
from ..db.db import session_wrapper
from ..db.queries import checklist_queries
from ..services import response_builder, emojis
from ..services.response_builder import button

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
    keyboard = [[button('cancel_conversation', 'Checklist overview', emojis.BACK)]]

    update.callback_query.edit_message_text(
        text='You are about to create a new checklist! Please send me a message with your desired name.',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return BASE_STATE


@session_wrapper
def create(session, update, context):
    checklist_name = update.message.text
    user_id = update.message.from_user.id
    keyboard = [[button('cancel_conversation', 'Checklist overview', emojis.BACK)]]

    if checklist_queries.exists(session, user_id, checklist_name):
        update.message.reply_text(
            'You already have a checklist with that name. Please choose a unique name.',
            reply_markup=InlineKeyboardMarkup(keyboard))

        return BASE_STATE

    checklist_queries.create(session, user_id, checklist_name)
    reply_markup = response_builder.checklist_overview_markup(session, context, user_id)
    update.message.reply_text(response_builder.CHECKLIST_OVERVIEW_TEXT, reply_markup=reply_markup,
                              parse_mode='Markdown')

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
    if context.user_data['checklist'].creator_id != update.callback_query.from_user.id:
        update.callback_query.answer('You are not allowed to do this!')

        return ConversationHandler.END

    update.callback_query.edit_message_text(
        text='You are about to delete the checklist *{}*. This *cannot be undone*. If you are certain about deleting '
             'this checklist, send me the checklist\'s name.'.format(context.user_data['checklist'].name),
        reply_markup=InlineKeyboardMarkup([[button('abort_removal', 'Main menu', emojis.BACK)]]),
        parse_mode='Markdown'
    )

    return BASE_STATE


@session_wrapper
def abort_removal(session, update, context):
    text, markup = response_builder.checklist_menu(session, update.callback_query.from_user, context)
    update.callback_query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return ConversationHandler.END


@session_wrapper
def remove(session, update, context):
    user_input = update.message.text
    checklist = context.user_data['checklist']
    if user_input != checklist.name:
        update.message.reply_text(
            'Your message and the checklist name do not match. Please send the *exact* name.',
            reply_markup=InlineKeyboardMarkup([
                [button('abort_removal', 'Main menu', emojis.BACK)]
            ]),
            parse_mode='Markdown'
        )
        return BASE_STATE

    checklist_queries.delete(session, checklist.id, update.message.chat_id)
    update.message.reply_text(
        'The checklist has been deleted.',
        reply_markup=InlineKeyboardMarkup(
            [[button('checklist_overview', 'Checklist overview', emojis.BACK)]]
        )
    )

    return ConversationHandler.END
