from telegram import InlineKeyboardMarkup

from . import settings
from ..db import session_wrapper, purchase_queries, user_queries
from ..db.queries import participant_queries
from ..helper import emojis
from ..helper.function_wrappers import button, edit
from ..i18n import trans

ACTION_IDENTIFIER = 'participant.leave'


@session_wrapper
def info_callback(session, update, context):
    query = update.callback_query
    checklist = user_queries.get_selected_checklist(session, query.from_user.id)
    purchases = purchase_queries.find_by_checklist(session, checklist.id)

    text = trans.t(f'{ACTION_IDENTIFIER}.text', count=len(purchases))
    markup = InlineKeyboardMarkup([[
        settings.link_button(),
        button(f'{ACTION_IDENTIFIER}.execute', trans.t(f'{ACTION_IDENTIFIER}.link'), emojis.RUNNER)
    ]])
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')


@session_wrapper
def execute_callback(session, update, context):
    query = update.callback_query
    success = participant_queries.leave(session, query.from_user.id)
    if not success:
        query.answer(trans.t(f'{ACTION_IDENTIFIER}.not_allowed'))
        return

    edit(query, trans.t(f'{ACTION_IDENTIFIER}.success'),
         InlineKeyboardMarkup([[button('checklist-picker', trans.t('checklist.picker.link'), emojis.BACK)]]))
