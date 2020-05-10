from telegram import InlineKeyboardMarkup

from . import main_menu
from ..db import session_wrapper
from ..db.queries import item_queries, user_queries
from ..helper import emojis
from ..helper.function_wrappers import button
from ..i18n import trans


@session_wrapper
def callback(session, update, context):
    user_id = update.message.from_user.id
    checklist = user_queries.get_selected_checklist(session, user_id)
    if checklist is None:
        # link to checklist picker
        text = trans.t('checklist.menu.no_checklist'),
        markup = InlineKeyboardMarkup([[button('checklist-picker', trans.t('checklist.picker.link'), emojis.FORWARD)]])
        update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
        return

    item_names = update.message.text
    item_queries.create(session, item_names, checklist.id)

    text = trans.t('item.add.success', name=checklist.name, items=item_names)
    markup = InlineKeyboardMarkup([[main_menu.link_button()]])
    update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
