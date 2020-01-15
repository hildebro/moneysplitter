from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

from handlers.menu_handler import render_checklist_menu, \
    render_checklist_menu_as_new
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
            [[InlineKeyboardButton('🔙 Main menu 🔙', callback_data='checklist_menu_{}'.format(checklist.id))]]
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
            PRICE_STATE: [MessageHandler(Filters.text, commit_purchase)]
        },
        fallbacks=[CallbackQueryHandler(abort, pattern='^abort_[0-9]+$')]
    )


# noinspection PyUnusedLocal
def initialize(update, context):
    update.callback_query.edit_message_text(
        text='Would you like to buy items of this checklist or create a named purchase?',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('🎁 Start item purchase 🎁', callback_data='item_purchase')],
            [InlineKeyboardButton('🖊️ Start named purchase 🖊️', callback_data='named_purchase')],
            [InlineKeyboardButton('🔙 Abort 🔙',
                                  callback_data='abort_{}'.format(context.user_data['checklist'].id))]
        ])
    )

    return TYPE_STATE


# noinspection PyUnusedLocal
def named_purchase(update, context):
    update.callback_query.edit_message_text(
        text='Please send me a message containing the name for your purchase.',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('🔙 Abort 🔙',
                                  callback_data='abort_{}'.format(context.user_data['checklist'].id))]
        ])
    )

    return NAMED_STATE


def set_name(update, context):
    context.user_data['purchase_name'] = update.message.text
    update.message.reply_text('Purchase name has been accepted. How much money did you spend?',
                              reply_markup=InlineKeyboardMarkup([
                                  [InlineKeyboardButton('🔙 Abort 🔙',
                                                        callback_data='abort_{}'.format(
                                                            context.user_data['checklist'].id))]
                              ]))

    return PRICE_STATE


def item_purchase(update, context):
    items = item_queries.find_by_checklist(context.user_data['checklist'].id)
    if len(items) == 0:
        update.callback_query.answer('This checklist has no items!')

        return TYPE_STATE

    context.user_data['purchase_dict'] = {}
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
        InlineKeyboardButton('🔙 Main menu 🔙', callback_data='abort_{}'.format(checklist.id)),
        InlineKeyboardButton('➡️ Continue ➡️', callback_data='ask_price')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text=ITEM_PURCHASE_MESSAGE.format(checklist.name),
                                            reply_markup=reply_markup, parse_mode='Markdown')


def abort(update, context):
    context.user_data.pop('purchase_dict', None)
    context.user_data.pop('purchase_name', None)
    render_checklist_menu(update, context)

    return ConversationHandler.END


# noinspection PyUnusedLocal
def ask_price(update, context):
    update.callback_query.edit_message_text(text='Now please send me a message containing the price of your purchase.',
                                            reply_markup=InlineKeyboardMarkup([
                                                [InlineKeyboardButton('🔙 Main menu 🔙',
                                                                      callback_data='abort_{}'.format(
                                                                          context.user_data['checklist'].id))]
                                            ]))

    return PRICE_STATE


def commit_purchase(update, context):
    price_text = update.message.text.replace(',', '.')
    checklist_id = context.user_data['checklist'].id
    user_id = update.message.from_user.id
    try:
        price = float(price_text)
    except ValueError:
        update.message.reply_text('Please enter a valid number; No currency or thousands separator.',
                                  reply_markup=InlineKeyboardMarkup([
                                      [InlineKeyboardButton('🔙 Main menu 🔙',
                                                            callback_data='abort_{}'.format(
                                                                checklist_id))]
                                  ]))

        return PRICE_STATE

    if 'purchase_name' in context.user_data:
        purchase_name = context.user_data.pop('purchase_name')
        purchase_queries.create_named_purchase(user_id, checklist_id, purchase_name, price)
    else:
        item_ids_to_purchase = []
        purchase_dict = context.user_data.pop('purchase_dict')
        for item_id in purchase_dict:
            if '✔️' in purchase_dict[item_id]:
                item_ids_to_purchase.append(item_id)
        purchase_queries.create_item_purchase(user_id, checklist_id, item_ids_to_purchase, price)

    render_checklist_menu_as_new(update, context)

    return ConversationHandler.END
