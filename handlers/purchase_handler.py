from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, Filters, CommandHandler

from handlers.main_menu_handler import render_main_menu, render_main_menu_from_callback
from main import conv_cancel
from queries import purchase_queries, item_queries

PURCHASE_MENU_MESSAGE = 'This is the purchase menu for checklist *{}*.'


def render_purchase_menu(update, context):
    checklist = context.user_data['checklist']
    keyboard = [
        [InlineKeyboardButton('Show unresolved purchases', callback_data='show_purchases')],
        [InlineKeyboardButton('Start new purchase', callback_data='new_purchase')],
        [InlineKeyboardButton('Back to main menu', callback_data='checklist_menu_{}'.format(checklist.id))]
    ]
    update.callback_query.edit_message_text(text=PURCHASE_MENU_MESSAGE.format(checklist.name),
                                            reply_markup=InlineKeyboardMarkup(keyboard),
                                            parse_mode='Markdown')


def show_purchases(update, context):
    query = update.callback_query
    checklist = context.user_data['checklist']
    purchases = purchase_queries.find_by_checklist(checklist.id)
    if len(purchases) == 0:
        text = checklist.name + ' has no unresolved purchases.'
    else:
        text = ''
        for purchase in purchases:
            text += '*{}* has paid *{}* for the following items:\n'.format(
                purchase.buyer.username,
                purchase.get_price()
            ) + '\n'.join(map(lambda item: item.name, purchase.items)) + '\n'

    query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Back to purchase menu', callback_data='purchase_menu')]]
        ),
        parse_mode='Markdown'
    )


TYPE_STATE, NAMED_STATE, ITEM_STATE, PRICE_STATE = range(4)


def get_conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^new_purchase$')],
        states={
            TYPE_STATE: [
                CallbackQueryHandler(item_purchase, pattern='^item_purchase$'),
                CallbackQueryHandler(named_purchase, pattern='^named_purchase$')
            ],
            NAMED_STATE: [
                MessageHandler(Filters.text, set_name)
            ],
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

    update.callback_query.edit_message_text(
        text='Would you like to buy items from the list or create a named purchase?',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('Item purchase', callback_data='item_purchase')],
            [InlineKeyboardButton('Named purchase', callback_data='named_purchase')]
        ])
    )

    return TYPE_STATE


def named_purchase(update, context):
    update.callback_query.edit_message_text(text='Please enter a name for your purchase.')

    return NAMED_STATE


def set_name(update, context):
    purchase_id = context.user_data['purchase_id']
    name = update.message.text
    item_queries.create_for_named_purchase(name, purchase_id)
    purchase_queries.finish(purchase_id)
    update.message.reply_text('Purchase committed. How much did you spend?')

    return PRICE_STATE


def item_purchase(update, context):
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
