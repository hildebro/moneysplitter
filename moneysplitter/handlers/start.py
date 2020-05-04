from telegram import InlineKeyboardMarkup

from ..db import session_wrapper, user_queries
from ..i18n import trans
from ..services import emojis
from ..services.response_builder import button


@session_wrapper
def callback(session, update, context):
    user = update.message.from_user
    if user_queries.exists(session, user.id):
        text = trans.t('start.already_started')
        markup_button = button('checklist-menu', trans.t('checklist.menu.link'), emojis.BACK)
    else:
        user_queries.register(session, update.message.from_user)
        text = trans.t('start.text')
        markup_button = button('checklist-picker', trans.t('conversation.continue'), emojis.FORWARD)

    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([[markup_button]]), parse_mode='Markdown')
