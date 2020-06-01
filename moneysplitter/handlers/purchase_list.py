from telegram import InlineKeyboardMarkup

from . import main_menu
from ..db import session_wrapper
from ..db.queries import purchase_queries, user_queries
from ..helper import emojis
from ..helper.function_wrappers import button
from ..i18n import trans


@session_wrapper
def callback(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id

    text, markup = purchase_log_data(session, user_id)
    if markup is None:
        query.answer(text)

    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')


def purchase_log_data(session, user_id):
    checklist = user_queries.get_selected_checklist(session, user_id)
    purchases = purchase_queries.find_by_checklist(session, checklist.id)
    purchase_count = len(purchases)

    if purchase_count == 0:
        return trans.t('purchase.log.no_purchases'), None

    keyboard = []
    for purchase in purchases:
        keyboard.append([button(f'purchase.edit_{purchase.id}', purchase.display_name())])

    keyboard.append([
        main_menu.link_button(),
        button('transaction.create.info', trans.t('transaction.create.link'), emojis.MONEY)
    ])

    text = trans.t('purchase.log.text')
    markup = InlineKeyboardMarkup(keyboard)
    return text, markup
