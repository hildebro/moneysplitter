from telegram import InlineKeyboardMarkup

from . import main_menu
from ..db import session_wrapper, user_queries
from ..helper import emojis
from ..helper.function_wrappers import button
from ..i18n import trans


@session_wrapper
def callback(session, update, context):
    query = update.callback_query
    text, markup = menu_data(session, query.from_user.id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')


def menu_data(session, user_id):
    checklist = user_queries.get_selected_checklist(session, user_id)

    text = trans.t('checklist.settings.text', name=checklist.name)
    markup = InlineKeyboardMarkup([
        [button('checklist-picker', trans.t('checklist.picker.link'), emojis.PICK)],
        [button('item.delete', trans.t('item.delete.link'), emojis.BIN)],
        [button('participant.delete', trans.t('participant.delete.link'), emojis.RUNNER)],
        [button('delete-checklist', trans.t('checklist.delete.link'), emojis.HAZARD)],
        [main_menu.link_button()]
    ])

    return text, markup


def link_button():
    return button('checklist-settings', trans.t('checklist.settings.link'), emojis.BACK)
