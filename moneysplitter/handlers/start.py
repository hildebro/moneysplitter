from telegram import InlineKeyboardMarkup

from . import main_menu
from ..db import session_wrapper, user_queries
from ..helper import emojis
from ..helper.function_wrappers import button
from ..i18n import trans


@session_wrapper
def callback(session, update, context):
    user = update.message.from_user
    if user_queries.exists(session, user.id):
        text = trans.t('start.already_started')
        markup_button = main_menu.link_button()
    else:
        user_queries.register(session, update.message.from_user)
        text = trans.t('start.text')
        markup_button = button('checklist-picker', trans.t('conversation.continue'), emojis.FORWARD)

    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[markup_button]]), parse_mode='Markdown')
