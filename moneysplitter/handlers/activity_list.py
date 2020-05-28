from telegram import InlineKeyboardMarkup

from . import main_menu
from ..db import session_wrapper
from ..db.queries import activity_queries
from ..helper.function_wrappers import edit
from ..i18n import trans


@session_wrapper
def callback(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    activities = activity_queries.find_by_checklist(session, user_id)

    if len(activities) == 0:
        query.answer(trans.t('activity.log.empty'))
        return

    text = '\n\n'.join(map(lambda activity: activity.display_name(), activities))
    markup = InlineKeyboardMarkup([[main_menu.link_button()]])
    edit(query, text, markup)
