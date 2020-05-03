from telegram import InlineKeyboardMarkup

from ..db import session_wrapper, user_queries
from ..i18n import trans
from ..services import emojis
from ..services.response_builder import button


@session_wrapper
def get_handler(session, update, context):
    query = update.callback_query
    text, markup = menu_data(session, query.from_user.id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')


def menu_data(session, user_id):
    checklist = user_queries.get_selected_checklist(session, user_id)

    text = trans.t('checklist.settings.text', name=checklist.name)
    markup = InlineKeyboardMarkup([
        [button('checklist-picker', trans.t('checklist.picker.link'), emojis.PICK)],
        [button('items-delete', trans.t('item.delete.link'), emojis.BIN)],
        [button('users-kick', trans.t('checklist.participant.remove.link'), emojis.RUNNER)],
        [button('delete-checklist', trans.t('checklist.delete.link'), emojis.HAZARD)],
        [button('checklist-menu', trans.t('checklist.menu.link'), emojis.BACK)]
    ])

    return text, markup
