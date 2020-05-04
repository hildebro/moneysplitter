from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters, MessageHandler

from . import checklist_picker
from ..db import checklist_queries, session_wrapper, user_queries
from ..i18n import trans
from ..services import emojis
from ..services.response_builder import button

BASE_STATE = 0


def conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize_creation, pattern='^new-checklist$')],
        states={BASE_STATE: [MessageHandler(Filters.text, create)]},
        fallbacks=[CallbackQueryHandler(cancel_conversation, pattern='^cancel-conversation$')]
    )


def initialize_creation(update, context):
    text = trans.t('checklist.create.init')
    markup = InlineKeyboardMarkup([[button('cancel-conversation', trans.t('checklist.picker.link'), emojis.BACK)]])
    update.callback_query.edit_message_text(text=text, reply_markup=markup)

    return BASE_STATE


@session_wrapper
def create(session, update, context):
    checklist_name = update.message.text
    user_id = update.message.from_user.id

    if checklist_queries.exists(session, user_id, checklist_name):
        text = trans.t('checklist.create.not_unique')
        markup = InlineKeyboardMarkup([[button('cancel-conversation', trans.t('checklist.picker.link'), emojis.BACK)]])
        update.message.reply_text(text, reply_markup=markup)
        return BASE_STATE

    new_checklist = checklist_queries.create(session, user_id, checklist_name)
    if user_queries.get_selected_checklist(session, user_id) is None:
        user_queries.select_checklist(session, new_checklist.id, user_id)

    text = trans.t('checklist.create.success')
    markup = InlineKeyboardMarkup([[button('checklist-menu', trans.t('checklist.menu.link'), emojis.BACK)]])

    update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END


@session_wrapper
def cancel_conversation(session, update, context):
    query = update.callback_query

    text, markup = checklist_picker.get_menu_data(session, query.from_user.id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return ConversationHandler.END
