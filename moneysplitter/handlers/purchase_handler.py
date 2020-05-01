from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

from ..db import session_wrapper, checklist_queries
from ..db.queries import purchase_queries, item_queries
from ..i18n import trans
from ..services import response_builder, emojis
from ..services.response_builder import button


# noinspection PyUnusedLocal
@session_wrapper
def show_purchases(session, update, context):
    query = update.callback_query
    checklist = checklist_queries.find(session, response_builder.interpret_data(query)['checklist_id'])
    purchases = purchase_queries.find_by_checklist(session, checklist.id)
    purchase_count = len(purchases)
    text = trans.t('purchase.log.header', name=checklist.name, count=purchase_count)
    if purchase_count != 0:
        text += '\n\n'
        for purchase in purchases:
            item_names = ', '.join(map(lambda item: item.name, purchase.items))
            text += trans.t('purchase.log.list', name=purchase.buyer.username, price=purchase.get_price(),
                            items=item_names) + '\n\n'

    query.edit_message_text(text=text, reply_markup=response_builder.back_to_main_menu(checklist.id),
                            parse_mode='Markdown')


ITEM_STATE, PRICE_STATE = range(2)


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^new-purchase_[0-9]+$')],
        states={
            ITEM_STATE: [
                CallbackQueryHandler(mark_item, pattern='^mark-purchase_[0-9]+_[0-9]+'),
                CallbackQueryHandler(ask_price, pattern='^continue-purchase_[0-9]+$'),
                MessageHandler(Filters.text, add_item)
            ],
            PRICE_STATE: [MessageHandler(Filters.text, commit_purchase)]
        },
        fallbacks=[CallbackQueryHandler(abort, pattern='^abort-purchase_[0-9]+$')]
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


# noinspection PyUnusedLocal
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
        update.callback_query.answer(trans.t('purchase.create.already_selected'))
        return ITEM_STATE

    purchase = purchase_queries.find(session, query_data['purchase_id'])

    text, markup = build_item_state(session, purchase)
    query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return ITEM_STATE


def build_item_state(session, purchase):
    items = item_queries.find_for_purchase(session, purchase.id)
    text = trans.t('purchase.create.header', name=purchase.checklist.name) + '\n\n' + trans.t('purchase.create.text',
                                                                                              count=len(items))
    markup = response_builder.entity_selector_markup(items, is_item_in_purchase, purchase.id, 'purchase')

    return text, markup


# noinspection PyUnusedLocal
@session_wrapper
def abort(session, update, context):
    query = update.callback_query
    purchase_id = response_builder.interpret_data(query)['purchase_id']
    checklist = checklist_queries.find_by_purchase(session, purchase_id)
    purchase_queries.abort(session, purchase_id)

    markup = response_builder.back_to_main_menu(checklist.id)
    query.edit_message_text(text=trans.t('conversation.cancel'), reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END


# noinspection PyUnusedLocal
@session_wrapper
def ask_price(session, update, context):
    query = update.callback_query
    purchase_id = response_builder.interpret_data(query)['purchase_id']
    if not purchase_queries.has_items(session, purchase_id):
        query.answer(trans.t('conversation.no_selection'))
        return ITEM_STATE

    markup = InlineKeyboardMarkup(
        [[button(f'abort-purchase_{purchase_id}', trans.t('checklist.menu.link'), emojis.BACK)]])
    query.edit_message_text(text=trans.t('purchase.create.price.ask'), reply_markup=markup)
    return PRICE_STATE


# noinspection PyUnusedLocal
@session_wrapper
def commit_purchase(session, update, context):
    purchase = purchase_queries.find_in_progress(session, update.message.from_user.id)
    if len(purchase.items) == 0:
        update.callback_query.answer(trans.t('conversation.no_selection'))
        return ITEM_STATE

    try:
        price_text = update.message.text.replace(',', '.')
        price = float(price_text)
    except ValueError:
        markup = InlineKeyboardMarkup(
            [[button(f'abort-purchase_{purchase.id}', trans.t('checklist.menu.link'), emojis.BACK)]])
        update.message.reply_text(trans.t('purchase.create.price.invalid'), reply_markup=markup)
        return PRICE_STATE

    purchase_queries.commit_purchase(session, purchase, price)
    markup = response_builder.back_to_main_menu(purchase.checklist_id)
    update.message.reply_text(trans.t('purchase.create.success'), reply_markup=markup, parse_mode='Markdown')
    return ConversationHandler.END
