from telegram import InlineKeyboardMarkup

from ..db import session_wrapper
from ..db.queries import user_queries, item_queries
from ..i18n import trans
from ..services import emojis
from ..services.response_builder import button


@session_wrapper
def get_message_handler(session, update, context):
    text, markup = checklist_menu_data(session, update.message.from_user.id)
    update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')


@session_wrapper
def get_callback_handler(session, update, context):
    query = update.callback_query
    text, markup = checklist_menu_data(session, query.from_user.id)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')


def checklist_menu_data(session, user_id):
    checklist = user_queries.get_selected_checklist(session, user_id)
    if checklist is None:
        # return link to checklist picker
        return trans.t('checklist.menu.no_checklist'), \
               InlineKeyboardMarkup([[button('checklist-picker', trans.t('checklist.picker.link'), emojis.FORWARD)]])

    # build actual main menu
    items = item_queries.find_by_checklist(session, checklist.id)
    item_count = len(items)

    text = trans.t('checklist.menu.header', name=checklist.name) \
           + '\n\n' \
           + trans.t('checklist.menu.items', count=item_count)
    if item_count > 0:
        text += '\n' + '\n'.join(map(lambda checklist_item: checklist_item.name, items))

    markup = InlineKeyboardMarkup([
        [button('new-purchase', trans.t('purchase.create.link'), emojis.CART)],
        [button('purchase-list', trans.t('purchase.log.link'), emojis.BILL)],
        [button('new-transactions-info', trans.t('transaction.create.link'), emojis.MONEY)],
        [button('checklist-settings', trans.t('checklist.settings.link'), emojis.GEAR)],
    ])

    return text, markup
