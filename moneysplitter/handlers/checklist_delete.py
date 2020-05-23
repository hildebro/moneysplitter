from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters, MessageHandler

from . import settings
from ..db import checklist_queries, session_wrapper, user_queries
from ..helper import emojis
from ..helper.function_wrappers import button
from ..i18n import trans

BASE_STATE = 0


def conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^delete-checklist$')],
        states={BASE_STATE: [MessageHandler(Filters.text, execute)]},
        fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')]
    )


@session_wrapper
def initialize(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    selected_checklist = user_queries.get_selected_checklist(session, user_id)

    if selected_checklist.creator_id != user_id:
        query.answer(trans.t('checklist.delete.permission_denied'))
        return ConversationHandler.END

    user_queries.set_deleting_checklist(session, user_id, selected_checklist.id)
    text = trans.t('checklist.delete.init', name=selected_checklist.name)
    markup = InlineKeyboardMarkup([[button('cancel', trans.t('checklist.settings.link'), emojis.BACK)]])
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return BASE_STATE


@session_wrapper
def execute(session, update, context):
    message = update.message
    user_input = message.text
    user_id = message.from_user.id
    deleting_checklist = user_queries.get_deleting_checklist(session, user_id)

    if user_input != deleting_checklist.name:
        text = trans.t('checklist.delete.not_matching')
        markup = InlineKeyboardMarkup([[button('cancel', trans.t('checklist.settings.link'), emojis.BACK)]])
        message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
        return BASE_STATE

    checklist_queries.delete(session, deleting_checklist.id)

    text = trans.t('checklist.delete.done')
    markup = InlineKeyboardMarkup([[button('checklist-picker', trans.t('checklist.picker.link'), emojis.BACK)]])
    message.reply_text(text, reply_markup=markup)
    return ConversationHandler.END


@session_wrapper
def cancel(session, update, context):
    query = update.callback_query

    text, markup = settings.menu_data(session, query.from_user.id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END
