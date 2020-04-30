from ..db import session_wrapper, user_queries
from ..i18n import trans


# noinspection PyUnusedLocal
@session_wrapper
def handle_start_command(session, update, context):
    user = update.message.from_user
    if user_queries.exists(session, user.id):
        message = trans.t('start.already_started')
        update.message.reply_text(message)
        user_queries.refresh(session, user)
        return

    user_queries.register(session, update.message.from_user)
    message = trans.t('start.text')
    update.message.reply_text(message, parse_mode='Markdown')


# noinspection PyUnusedLocal
@session_wrapper
def refresh_username(session, update, context):
    user_queries.refresh(session, update.message.from_user)
