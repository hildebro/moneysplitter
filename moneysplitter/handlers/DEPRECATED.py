# TODO use for item refresh
# @session_wrapper
# def refresh_checklists(session, update, context):
#     user_id = update.callback_query.from_user.id
#     current_checklist = context.user_data['all_checklists']
#     db_checklist_count = checklist_queries.count_checklists(session, user_id)
#
#     if len(current_checklist) == db_checklist_count:
#         update.callback_query.answer('Nothing new to show!')
#         return
#
#     reply_markup = response_builder.checklist_overview_markup(session, context, user_id)
#     update.message.reply_text(trans.t('checklist.menu.text'), reply_markup=reply_markup, parse_mode='Markdown')
#     update.callback_query.answer('Checklist overview refreshed!')
