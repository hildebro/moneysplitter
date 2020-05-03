from telegram import InlineKeyboardMarkup

from . import main_menu
from ..db import session_wrapper, checklist_queries, user_queries
from ..i18n import trans
from ..services import emojis
from ..services.response_builder import button, interpret_data


@session_wrapper
def get_menu_handler(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id

    text, markup = get_menu_data(session, user_id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')


def get_menu_data(session, user_id):
    checklists = checklist_queries.find_by_participant(session, user_id)
    selected_checklist = user_queries.get_selected_checklist(session, user_id)

    keyboard = []
    for checklist in checklists:
        keyboard.append([button(f'select-checklist_{checklist.id}', checklist.name)])

    keyboard.append([button('new-checklist', trans.t('checklist.create.link'), emojis.NEW)])
    if selected_checklist is not None:
        # can't go back, if there is no checklist to go back to
        keyboard.append([button('checklist-menu', trans.t('checklist.menu.link'), emojis.BACK)])

    return trans.t('checklist.picker.text'), InlineKeyboardMarkup(keyboard)


@session_wrapper
def get_selection_handler(session, update, context):
    query = update.callback_query
    query_data = interpret_data(query)
    user_id = query.from_user.id
    checklist_id = query_data['checklist_id']

    if not checklist_queries.is_participant(session, checklist_id, user_id):
        text = trans.t('checklist.picker.not_participant')
        markup = InlineKeyboardMarkup([[button('checklist-picker', trans.t('checklist.picker.link'), emojis.BACK)]])
    else:
        user_queries.select_checklist(session, checklist_id, user_id)
        text, markup = main_menu.checklist_menu_data(session, user_id)

    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')
