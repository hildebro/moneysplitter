from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters, MessageHandler, CommandHandler

from .menu_handler import cancel_conversation, conv_cancel
from ..db import checklist_queries, session_wrapper
from ..i18n import trans
from ..services import response_builder, emojis
from ..services.response_builder import button

BASE_STATE = 0


def get_creation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize_creation, pattern='^new_checklist$')],
        states={BASE_STATE: [MessageHandler(Filters.text, create)]},
        fallbacks=[CallbackQueryHandler(cancel_conversation, pattern='^cancel_conversation$')]
    )


# noinspection PyUnusedLocal
def initialize_creation(update, context):
    markup = InlineKeyboardMarkup([[button('cancel_conversation', trans.t('checklist.overview.link'), emojis.BACK)]])
    update.callback_query.edit_message_text(text=trans.t('checklist.create.init'), reply_markup=markup)

    return BASE_STATE


@session_wrapper
def create(session, update, context):
    checklist_name = update.message.text
    user_id = update.message.from_user.id
    markup = InlineKeyboardMarkup([[button('cancel_conversation', trans.t('checklist.overview.link'), emojis.BACK)]])

    if checklist_queries.exists(session, user_id, checklist_name):
        update.message.reply_text(trans.t('checklist.create.not_unique'), reply_markup=markup)

        return BASE_STATE

    checklist_queries.create(session, user_id, checklist_name)
    reply_markup = response_builder.checklist_overview_markup(session, context, user_id)
    update.message.reply_text(trans.t('checklist.overview.text'), reply_markup=reply_markup, parse_mode='Markdown')

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


def initialize_removal(update, context):
    query = update.callback_query
    if context.user_data['checklist'].creator_id != query.from_user.id:
        query.answer(trans.t('checklist.delete.permission_denied'))

        return ConversationHandler.END

    checklist_name = context.user_data['checklist'].name
    markup = InlineKeyboardMarkup([[button('abort_removal', trans.t('checklist.menu.link'), emojis.BACK)]])
    query.edit_message_text(text=trans.t('checklist.delete.init', name=checklist_name), reply_markup=markup,
                            parse_mode='Markdown')

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
        markup = InlineKeyboardMarkup([[button('abort_removal', trans.t('checklist.menu.link'), emojis.BACK)]])
        update.message.reply_text(trans.t('checklist.delete.not_matching'), reply_markup=markup, parse_mode='Markdown')

        return BASE_STATE

    checklist_queries.delete(session, checklist.id, update.message.chat_id)
    markup = InlineKeyboardMarkup([[button('checklist_overview', trans.t('checklist.overview.link'), emojis.BACK)]])
    update.message.reply_text(trans.t('checklist.delete.done'), reply_markup=markup)

    return ConversationHandler.END
