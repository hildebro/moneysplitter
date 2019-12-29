from handlers.main_menu_handler import render_checklists_from_callback
from queries import item_queries, purchase_queries


def show_items(update, context):
    query = update.callback_query
    checklist_id = context.user_data['checklist_id']
    checklist_name = context.user_data['checklist_names'][checklist_id]
    checklist_items = item_queries.find_by_checklist(checklist_id)
    if len(checklist_items) == 0:
        query.edit_message_text(text=checklist_name + ' has no items.')
    else:
        query.edit_message_text(
            text='{} contains the following items:\n{}'.format(checklist_name, '\n'.join(
                map(lambda checklist_item: checklist_item.name, checklist_items)))
        )

    render_checklists_from_callback(update, context, True)


def show_purchases(update, context):
    query = update.callback_query
    checklist_id = context.user_data['checklist_id']
    checklist_name = context.user_data['checklist_names'][checklist_id]
    purchases = purchase_queries.find_by_checklist(checklist_id)
    if len(purchases) == 0:
        text = checklist_name + ' has no purchases.'
    else:
        text = ''
        for purchase in purchases:
            text += '{} has paid {} for the following items:\n'.format(purchase.buyer.username,
                                                                       purchase.get_price()) + '\n'.join(
                map(lambda item: item.name, purchase.items)) + '\n'

    query.edit_message_text(text=text)
    render_checklists_from_callback(update, context, True)
