from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

from ..db import session_wrapper, checklist_queries
from ..db.queries import purchase_queries, item_queries
from ..services import response_builder, emojis
from ..services.response_builder import button


@session_wrapper
def show_purchases(session, update, context):
    query = update.callback_query
    checklist = checklist_queries.find(session, response_builder.interpret_data(query)['checklist_id'])
    purchases = purchase_queries.find_by_checklist(session, checklist.id)
    if len(purchases) == 0:
        text = checklist.name + ' has no outstanding purchases.'
    else:
        text = ''
        for purchase in purchases:
            item_names = ', '.join(map(lambda item: item.name, purchase.items))
            text += f'*{purchase.buyer.username} paid {purchase.get_price()} for:* {item_names}\n\n'

    query.edit_message_text(text=text, reply_markup=response_builder.back_to_main_menu(checklist.id),
                            parse_mode='Markdown')


ITEM_STATE, PRICE_STATE = range(2)
ITEM_PURCHASE_MESSAGE = """
You are currently purchasing items for checklist *{}*.
      
Click on items to *(de)select* them for purchase.
You may also send me item names which will be added as preselected items.
Once you're done with items, click *Continue* to set a price.
"""
ITEM_PURCHASE_MESSAGE_EMPTY = """
You are currently purchasing items for checklist *{}*.

This checklist has no items, but you may send me item names which will be added as preselected items.
"""


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^new-purchase_[0-9]+$')],
        states={
            ITEM_STATE: [
                CallbackQueryHandler(mark_item, pattern='^mark-for-purchase_[0-9]+_[0-9]+'),
                CallbackQueryHandler(ask_price, pattern='^continue-for-purchase_[0-9]+$'),
                MessageHandler(Filters.text, add_item)
            ],
            PRICE_STATE: [MessageHandler(Filters.text, commit_purchase)]
        },
        fallbacks=[CallbackQueryHandler(abort, pattern='^abort-for-purchase_[0-9]+$')]
    )


def is_item_in_purchase(item):
    """To be used as a callback for entity_selector_markup"""
    return item.purchase is not None


@session_wrapper
def initialize(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    checklist = checklist_queries.find(session, response_builder.interpret_data(query)['checklist_id'])
    purchase = purchase_queries.new_purchase(session, checklist.id, user_id)

    text, markup = build_item_state(session, purchase)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return ITEM_STATE


@session_wrapper
def add_item(session, update, context):
    item_names = update.message.text
    purchase = purchase_queries.find_in_progress(session, update.message.from_user.id)
    checklist = purchase.checklist
    item_queries.create(session, item_names, checklist.id, purchase.id)

    text, markup = build_item_state(session, purchase)
    update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')

    return ITEM_STATE


@session_wrapper
def mark_item(session, update, context):
    query = update.callback_query
    query_data = response_builder.interpret_data(query)
    success = purchase_queries.mark_item(session, query_data['purchase_id'], query_data['item_id'])
    if not success:
        update.callback_query.answer('Someone else is purchasing right now and marked this item already!')
        return ITEM_STATE

    purchase = purchase_queries.find(session, query_data['purchase_id'])

    text, markup = build_item_state(session, purchase)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return ITEM_STATE


def build_item_state(session, purchase):
    checklist = purchase.checklist
    items = item_queries.find_for_purchase(session, purchase.id)
    text = ITEM_PURCHASE_MESSAGE if len(items) > 0 else ITEM_PURCHASE_MESSAGE_EMPTY
    text = text.format(checklist.name)
    markup = response_builder.entity_selector_markup(items, is_item_in_purchase, purchase.id, 'for-purchase')

    return text, markup


@session_wrapper
def abort(session, update, context):
    query = update.callback_query
    purchase_id = response_builder.interpret_data(query)['purchase_id']
    checklist = checklist_queries.find_by_purchase(session, purchase_id)
    purchase_queries.abort(session, purchase_id)

    markup = response_builder.back_to_main_menu(checklist.id)
    query.edit_message_text(text='Purchase aborted.', reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END


@session_wrapper
def ask_price(session, update, context):
    query = update.callback_query
    purchase_id = response_builder.interpret_data(query)['purchase_id']
    if not purchase_queries.has_items(session, purchase_id):
        query.answer('You cannot continue without selecting items!')
        return ITEM_STATE

    query.edit_message_text(text='How much did you spent? Please send me the amount.',
                            reply_markup=InlineKeyboardMarkup(
                                [[button(f'abort-for-purchase_{purchase_id}', 'Main menu', emojis.BACK)]]))
    return PRICE_STATE


@session_wrapper
def commit_purchase(session, update, context):
    purchase = purchase_queries.find_in_progress(session, update.message.from_user.id)
    try:
        price_text = update.message.text.replace(',', '.')
        price = float(price_text)
    except ValueError:
        update.message.reply_text('Please enter a valid amount! It may include a comma or a period, but no currency.',
                                  reply_markup=InlineKeyboardMarkup(
                                      [[button(f'abort-for-purchase_{purchase.id}', 'Main menu', emojis.BACK)]]))
        return PRICE_STATE

    purchase_queries.commit_purchase(session, purchase, price)

    update.message.reply_text('Purchase successful!',
                              reply_markup=response_builder.back_to_main_menu(purchase.checklist_id),
                              parse_mode='Markdown')
    return ConversationHandler.END
