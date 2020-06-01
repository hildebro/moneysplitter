from telegram import InlineKeyboardMarkup

from . import main_menu
from ..db import session_wrapper, purchase_queries, user_queries, Activity
from ..helper import emojis, write_off_calculator
from ..helper.function_wrappers import button, edit
from ..i18n import trans

ACTION_IDENTIFIER = 'transaction.create'


@session_wrapper
def info_callback(session, update, context):
    query = update.callback_query
    checklist = user_queries.get_selected_checklist(session, query.from_user.id)
    purchases = purchase_queries.find_by_checklist(session, checklist.id)
    if len(purchases) == 0:
        query.answer(trans.t(f'{ACTION_IDENTIFIER}.no_purchases'))
        return

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
    user = user_queries.find(session, user_id)
    checklist = user_queries.get_selected_checklist(session, user_id)
    purchases = purchase_queries.find_by_checklist(session, checklist.id)

    write_off_calculator.write_off(session, checklist, purchases)

    session.add(Activity(trans.t('activity.write_off', name=user.display_name()), checklist.id))
    session.commit()

    edit(query, trans.t(f'{ACTION_IDENTIFIER}.success'), InlineKeyboardMarkup([[main_menu.link_button()]]))
