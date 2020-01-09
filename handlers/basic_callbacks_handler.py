from handlers.menu_handler import render_checklist_overview_from_callback
from queries import checklist_queries


def refresh_checklists(update, context):
    if len(context.user_data['all_checklists']) == checklist_queries.count_checklists(
            update.callback_query.from_user.id):
        update.callback_query.answer('Nothing new to show!')
        return

    render_checklist_overview_from_callback(update, context, False)
    update.callback_query.answer('Main menu refreshed!')
