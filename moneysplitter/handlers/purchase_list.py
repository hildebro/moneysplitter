from telegram import InlineKeyboardMarkup

from ..db import session_wrapper
from ..db.queries import purchase_queries, user_queries
from ..i18n import trans
from ..services import emojis
from ..services.response_builder import button


@session_wrapper
def get_handler(session, update, context):
    query = update.callback_query
    checklist = user_queries.get_selected_checklist(session, query.from_user.id)
    purchases = purchase_queries.find_by_checklist(session, checklist.id)
    purchase_count = len(purchases)

    text = trans.t('purchase.log.header', name=checklist.name, count=purchase_count)
    if purchase_count > 0:
        text += '\n\n' + '\n\n'.join(map(lambda purchase: purchase.display_name(), purchases))

    markup = InlineKeyboardMarkup([[button('checklist-menu', trans.t('checklist.menu.link'), emojis.BACK)]])
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')
