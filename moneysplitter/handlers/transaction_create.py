from telegram import InlineKeyboardMarkup

from . import main_menu
from ..db import session_wrapper, purchase_queries, user_queries
from ..db.queries import transaction_queries
from ..helper import emojis, write_off_calculator
from ..helper.function_wrappers import button, edit
from ..i18n import trans

ACTION_IDENTIFIER = 'transaction.create'


@session_wrapper
def info_callback(session, update, context):
    query = update.callback_query
    checklist = user_queries.get_selected_checklist(session, query.from_user.id)
    purchases = purchase_queries.find_by_checklist(session, checklist.id)

    text = trans.t(f'{ACTION_IDENTIFIER}.text', count=len(purchases))
    markup = InlineKeyboardMarkup([[
        main_menu.link_button(),
        button(f'{ACTION_IDENTIFIER}.execute', trans.t(f'{ACTION_IDENTIFIER}.link'), emojis.MONEY)
    ]])
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')


@session_wrapper
def execute_callback(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    checklist = user_queries.get_selected_checklist(session, user_id)
    purchases = purchase_queries.find_by_checklist(session, checklist.id)

    transactions = write_off_calculator.write_off(session, checklist, purchases)
    if len(transactions) == 0:
        query.answer(trans.t(f'{ACTION_IDENTIFIER}.no_purchases'))
        return

    transaction_queries.add_all(session, checklist, transactions)
    purchase_queries.write_off(session, checklist.id, user_id)

    edit(query, trans.t(f'{ACTION_IDENTIFIER}.success'), InlineKeyboardMarkup([[main_menu.link_button()]]))
