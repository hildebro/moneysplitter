from telegram import InlineKeyboardMarkup

from . import main_menu
from ..db import session_wrapper, checklist_queries, user_queries
from ..helper import emojis, response_builder
from ..helper.function_wrappers import button
from ..i18n import trans


@session_wrapper
def menu_callback(session, update, context):
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
        keyboard.append([
            button('checklist-menu', trans.t('checklist.menu.link'), emojis.BACK),
            button('checklist-settings', trans.t('checklist.settings.link'), emojis.BACK)
        ])

    return trans.t('checklist.picker.text'), InlineKeyboardMarkup(keyboard)


@session_wrapper
def select_callback(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    checklist_id = response_builder.get_entity_id(query)

    if not checklist_queries.is_participant(session, checklist_id, user_id):
        text = trans.t('checklist.picker.not_participant')
        markup = InlineKeyboardMarkup([[button('checklist-picker', trans.t('checklist.picker.link'), emojis.BACK)]])
    else:
        user_queries.select_checklist(session, checklist_id, user_id)
        text, markup = main_menu.checklist_menu_data(session, user_id)

    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')
