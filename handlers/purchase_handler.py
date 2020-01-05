from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, Filters, CommandHandler

from handlers.main_menu_handler import render_main_menu, render_main_menu_from_callback
from main import conv_cancel
from queries import purchase_queries, item_queries

ITEM_STATE, PRICE_STATE = range(2)


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^new_purchase$')],
        states={
            ITEM_STATE: [
                CallbackQueryHandler(buffer_item, pattern='^bi_.+'),
                CallbackQueryHandler(revert_item, pattern='^ri$'),
                CallbackQueryHandler(finish, pattern='^fp$'),
                CallbackQueryHandler(abort, pattern='^ap$')
            ],
            PRICE_STATE: [MessageHandler(Filters.text, set_price)]
        },
        fallbacks=[CommandHandler('cancel', conv_cancel)]
    )


def initialize(update, context):
    user_id = update.callback_query.message.chat_id
    checklist_id = context.user_data['checklist'].id
    purchase = purchase_queries.create(user_id, checklist_id)
    context.user_data['purchase_id'] = purchase.id
    render_items_to_purchase(update, context)

    return ITEM_STATE


def buffer_item(update, context):
    query = update.callback_query
    item_id = query.data.split('_')[-1]
    item_queries.buffer(item_id, context.user_data['purchase_id'])
    render_items_to_purchase(update, context)

    return ITEM_STATE


def revert_item(update, context):
    purchase_id = context.user_data['purchase_id']
    reverted = item_queries.unbuffer(purchase_id)
    if not reverted:
        update.callback_query.answer('Nothing to revert.')
        return
    render_items_to_purchase(update, context)

    return ITEM_STATE


def render_items_to_purchase(update, context):
    items = item_queries.find_for_purchase(context.user_data['purchase_id'])
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
    purchase_queries.abort(context.user_data['purchase_id'])
    update.callback_query.edit_message_text(text='Purchase aborted.')
    render_main_menu_from_callback(update, context, True)

    return ConversationHandler.END


def finish(update, context):
    purchase_id = context.user_data['purchase_id']
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

    purchase_queries.set_price(context.user_data['purchase_id'], price)
    update.message.reply_text('Price has been set.')
    render_main_menu(update, context)

    return ConversationHandler.END
