from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, Filters, CommandHandler

from handlers.menu_handler import render_checklist_menu, \
    render_checklist_menu_as_new
from main import conv_cancel
from queries import purchase_queries, item_queries


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
            [[InlineKeyboardButton('Back to main menu', callback_data='checklist_menu_{}'.format(checklist.id))]]
        ),
        parse_mode='Markdown'
    )


TYPE_STATE, NAMED_STATE, ITEM_STATE, PRICE_STATE = range(4)
ITEM_PURCHASE_MESSAGE = \
    'You are now purchasing items from checklist *{}*.\n\nClick on items to *(de)select* them for ' \
    'purchase.\nWhen you are done, click *Continue* to set a price.\nClick *Abort* to exit without purchasing items'


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
                CallbackQueryHandler(mark_item, pattern='^mark_.+'),
                CallbackQueryHandler(abort, pattern='^abort_[0-9]+$'),
                CallbackQueryHandler(ask_price, pattern='^ask_price$')
            ],
            PRICE_STATE: [MessageHandler(Filters.text, set_price)]
        },
        fallbacks=[CommandHandler('cancel', conv_cancel)]
    )


# noinspection PyUnusedLocal
def initialize(update, context):
    update.callback_query.edit_message_text(
        text='Would you like to buy items of this checklist or create a named purchase?',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('🎁 Start item purchase 🎁', callback_data='item_purchase')],
            [InlineKeyboardButton('🖊️ Start named purchase 🖊️', callback_data='named_purchase')]
        ])
    )

    return TYPE_STATE


def named_purchase(update, context):
    update.callback_query.edit_message_text(text='Please send me a message containing the name for your purchase.')

    return NAMED_STATE


def set_name(update, context):
    name = update.message.text
    item = item_queries.create(name, context.user_data['checklist'].id)
    # kind of a hack. when entering PRICE_STATE, the method will see this as the user having clicked the new item
    # this results in a purchase of just this new item, effectively giving the purchase a name /shrug
    context.user_data['purchase_dict'] = {
        item.id: '✔️' + item.name + '✔️'
    }
    update.message.reply_text('Name has been accepted. Now enter the price for this purchase?')

    return PRICE_STATE


def item_purchase(update, context):
    context.user_data['purchase_dict'] = {}
    items = item_queries.find_by_checklist(context.user_data['checklist'].id)
    for item in items:
        context.user_data['purchase_dict'][item.id] = item.name
    render_item_buttons(update, context)

    return ITEM_STATE


def mark_item(update, context):
    query = update.callback_query
    item_id = int(query.data.split('_')[-1])
    item_name = context.user_data['purchase_dict'][item_id]
    if '✔️' in item_name:
        item_name = item_name.replace('✔️', '')
    else:
        item_name = '✔️' + item_name + '✔️'

    context.user_data['purchase_dict'][item_id] = item_name
    render_item_buttons(update, context)

    return ITEM_STATE


def render_item_buttons(update, context):
    checklist = context.user_data['checklist']
    purchase_dict = context.user_data['purchase_dict']

    keyboard = []
    for item_id in purchase_dict:
        keyboard.append([InlineKeyboardButton(purchase_dict[item_id], callback_data='mark_{}'.format(item_id))])
    keyboard.append([
        InlineKeyboardButton('Abort', callback_data='abort_{}'.format(checklist.id)),
        InlineKeyboardButton('Continue', callback_data='ask_price')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text=ITEM_PURCHASE_MESSAGE.format(checklist.name),
                                            reply_markup=reply_markup, parse_mode='Markdown')


def abort(update, context):
    context.user_data['purchase_dict'] = None
    render_checklist_menu(update, context)

    return ConversationHandler.END


# noinspection PyUnusedLocal
def ask_price(update, context):
    update.callback_query.edit_message_text(text='Now please send me a message containing the price of your purchase.')

    return PRICE_STATE


def set_price(update, context):
    price_text = update.message.text.replace(',', '.')
    try:
        price = float(price_text)
    except ValueError:
        update.message.reply_text('Please enter a valid number; No currency or thousands separator.')

        return PRICE_STATE

    item_ids_to_purchase = []
    purchase_dict = context.user_data['purchase_dict']
    for item_id in purchase_dict:
        if '✔️' in purchase_dict[item_id]:
            item_ids_to_purchase.append(item_id)

    purchase_queries.create(update.message.from_user.id, context.user_data['checklist'].id, item_ids_to_purchase, price)
    render_checklist_menu_as_new(update, context)

    return ConversationHandler.END
