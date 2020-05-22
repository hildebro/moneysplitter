from telegram import InlineKeyboardMarkup

from . import main_menu
from ..db import session_wrapper
from ..db.queries import transaction_queries
from ..helper import emojis
from ..helper.function_wrappers import edit, button
from ..i18n import trans


@session_wrapper
def callback(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    transactions = transaction_queries.find(session, user_id)

    if len(transactions) == 0:
        query.answer(trans.t('transaction.list.no_transactions'))
        return

    text = '\n\n' + '\n\n'.join(map(lambda transaction: transaction.display_name(user_id), transactions))

    markup = InlineKeyboardMarkup([[
        main_menu.link_button(),
        button('transaction.payoff', trans.t('transaction.payoff.link'), emojis.MONEY)
    ]])
    edit(query, text, markup)
