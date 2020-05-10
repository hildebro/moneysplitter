from telegram.error import BadRequest

from . import main_menu
from ..db import session_wrapper
from ..helper.function_wrappers import edit
from ..i18n import trans


@session_wrapper
def callback(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id

    text, markup = main_menu.checklist_menu_data(session, user_id)
    try:
        edit(query, text, markup)
        query.answer(trans.t('item.refresh.success'))
    except BadRequest:
        query.answer(trans.t('item.refresh.fail'))
