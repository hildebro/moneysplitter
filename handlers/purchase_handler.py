from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from handlers.main_menu_handler import render_checklists, render_checklists_from_callback
from queries import purchase_queries, item_queries

ITEM_STATE, PRICE_STATE = range(2)


def initialize(update, context):
    user_id = update.callback_query.message.chat_id
    checklist_id = context.chat_data['checklist_id']
    purchase = purchase_queries.create(user_id, checklist_id)
    context.chat_data['purchase_id'] = purchase.id
    render_items_to_purchase(update, context)

    return ITEM_STATE


def buffer_item(update, context):
    query = update.callback_query
    query_data = query.data.split('_')
    item_id = query_data[1]
    item_queries.buffer(item_id, context.chat_data['purchase_id'])
    render_items_to_purchase(update, context)

    return ITEM_STATE


def revert_item(update, context):
    purchase_id = context.chat_data['purchase_id']
    reverted = item_queries.unbuffer(purchase_id)
    if not reverted:
        update.callback_query.answer('Nothing to revert.')
        return
    render_items_to_purchase(update, context)

    return ITEM_STATE


def render_items_to_purchase(update, context):
    items = item_queries.find_for_purchase(context.chat_data['purchase_id'])
    keyboard = []
    for item in items:
        keyboard.append([InlineKeyboardButton(item.name, callback_data='bi_{}'.format(item.id))])

    keyboard.append([
        InlineKeyboardButton('Revert', callback_data='ri'),
        InlineKeyboardButton('Abort', callback_data='ap')
    ])
    keyboard.append([
        InlineKeyboardButton('Finish', callback_data='fp')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text='Choose items to purchase:', reply_markup=reply_markup)


def abort(update, context):
    purchase_queries.abort(context.chat_data['purchase_id'])
    update.callback_query.edit_message_text(text='Purchase aborted.')
    render_checklists_from_callback(update, context, True)

    return ConversationHandler.END


def finish(update, context):
    purchase_id = context.chat_data['purchase_id']
    purchase_queries.finish(purchase_id)
    update.callback_query.edit_message_text(text='Purchase committed. How much did you spend?')

    return PRICE_STATE


def set_price(update, context):
    price_text = update.message.text.replace(',', '.')
    try:
        price = float(price_text)
    except ValueError:
        update.message.reply_text('Please enter a valid number (no thousands separators allowed).')

        return PRICE_STATE

    purchase_queries.set_price(context.chat_data['purchase_id'], price)
    update.message.reply_text('Price has been set.')
    render_checklists(update, context)

    return ConversationHandler.END
