from handlers.main_menu_handler import render_main_menu_from_callback
from queries import purchase_queries, checklist_queries


def show_purchases(update, context):
    query = update.callback_query
    checklist = context.user_data['checklist']
    purchases = purchase_queries.find_by_checklist(checklist.id)
    if len(purchases) == 0:
        text = checklist.name + ' has no purchases.'
    else:
        text = ''
        for purchase in purchases:
            text += '{} has paid {} for the following items:\n'.format(purchase.buyer.username,
                                                                       purchase.get_price()) + '\n'.join(
                map(lambda item: item.name, purchase.items)) + '\n'

    query.edit_message_text(text=text)
    render_main_menu_from_callback(update, context, True)


def refresh_checklists(update, context):
    if len(context.user_data['all_checklists']) == checklist_queries.count_checklists(
            update.callback_query.from_user.id):
        update.callback_query.answer('Nothing new to show!')
        return

    render_main_menu_from_callback(update, context, False)
    update.callback_query.answer('Main menu refreshed!')
