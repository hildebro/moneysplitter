from db import session_wrapper
from handlers import menu_handler
from queries import checklist_queries


@session_wrapper
def refresh_checklists(session, update, context):
    user_id = update.callback_query.from_user.id
    currently_displayed_checklists = context.user_data['all_checklists']
    db_checklist_count = checklist_queries.count_checklists(session, user_id)

    if len(currently_displayed_checklists) == db_checklist_count:
        update.callback_query.answer('Nothing new to show!')
        return

    reply_markup = menu_handler.build_checklist_overview_markup(context, user_id)
    update.message.reply_text(menu_handler.CHECKLIST_OVERVIEW_TEXT, reply_markup=reply_markup, parse_mode='Markdown')

    update.callback_query.answer('Checklist overview refreshed!')
