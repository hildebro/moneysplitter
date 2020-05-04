from telegram import InlineKeyboardMarkup

from ..db import session_wrapper
from ..db.queries import item_queries, user_queries
from ..i18n import trans
from ..services import emojis
from ..services.response_builder import button


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
    markup = InlineKeyboardMarkup([[button('checklist-menu', trans.t('checklist.menu.link'), emojis.BACK)]])
    update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')
