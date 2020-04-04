from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, Filters

from ..db.db import session_wrapper
from ..db.queries import purchase_queries, item_queries
from ..services import response_builder


@session_wrapper
def show_purchases(session, update, context):
    query = update.callback_query
    checklist = context.user_data['checklist']
    purchases = purchase_queries.find_by_checklist(session, checklist.id)
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
        entry_points=[CallbackQueryHandler(initialize, pattern='^new_purchase$')],
        states={
            ITEM_STATE: [
                CallbackQueryHandler(mark_item, pattern='^mark_.+'),
                CallbackQueryHandler(abort, pattern='^abort_[0-9]+$'),
                CallbackQueryHandler(ask_price, pattern='^ask_price$'),
                MessageHandler(Filters.text, add_item)
            ],
            PRICE_STATE: [MessageHandler(Filters.text, commit_purchase)]
        },
        fallbacks=[CallbackQueryHandler(abort, pattern='^abort_[0-9]+$')]
    )


@session_wrapper
def initialize(session, update, context):
    items = item_queries.find_by_checklist(session, context.user_data['checklist'].id)
    context.user_data['purchase_dict'] = {}
    for item in items:
        context.user_data['purchase_dict'][item.id] = item.name
    render_purchase_menu_from_callback(update, context)

    return ITEM_STATE


@session_wrapper
def add_item(session, update, context):
    item_names = update.message.text
    items = item_queries.create(session, item_names, context.user_data['checklist'].id)
    for item in items:
        context.user_data['purchase_dict'][item.id] = '✔️' + item.name + '✔️'
    render_purchase_menu(update, context)

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
    render_purchase_menu_from_callback(update, context)

    return ITEM_STATE


def render_purchase_menu(update, context):
    checklist = context.user_data['checklist']
    purchase_dict = context.user_data['purchase_dict']
    text, reply_markup = build_item_reply(checklist, purchase_dict)
    update.message.reply_text(text.format(checklist.name),
                              reply_markup=reply_markup, parse_mode='Markdown')


def render_purchase_menu_from_callback(update, context):
    checklist = context.user_data['checklist']
    purchase_dict = context.user_data['purchase_dict']
    text, reply_markup = build_item_reply(checklist, purchase_dict)
    update.callback_query.edit_message_text(text=text.format(checklist.name),
                                            reply_markup=reply_markup, parse_mode='Markdown')


def build_item_reply(checklist, purchase_dict):
    keyboard = []
    for item_id in purchase_dict:
        keyboard.append([InlineKeyboardButton(purchase_dict[item_id], callback_data='mark_{}'.format(item_id))])
    abort_button = InlineKeyboardButton('🔙 Main menu 🔙', callback_data='abort_{}'.format(checklist.id))
    if len(keyboard) == 0:
        keyboard.append([abort_button])
        text = ITEM_PURCHASE_MESSAGE_EMPTY
    else:
        keyboard.append([
            abort_button,
            InlineKeyboardButton('➡️ Continue ➡️', callback_data='ask_price')
        ])
        text = ITEM_PURCHASE_MESSAGE
    return text, InlineKeyboardMarkup(keyboard)


@session_wrapper
def abort(session, update, context):
    context.user_data.pop('purchase_dict', None)
    text, markup = response_builder.checklist_menu(session, update.callback_query.from_user, context)
    update.callback_query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return ConversationHandler.END


def ask_price(update, context):
    any_marked_items = False
    purchase_dict = context.user_data['purchase_dict']
    for item_id in purchase_dict:
        if '✔️' in purchase_dict[item_id]:
            any_marked_items = True
            break

    if not any_marked_items:
        update.callback_query.answer('You cannot continue without selecting items!')

        return ITEM_STATE

    update.callback_query.edit_message_text(text='Now please send me a message containing the price of your purchase.',
                                            reply_markup=InlineKeyboardMarkup([
                                                [InlineKeyboardButton('🔙 Main menu 🔙',
                                                                      callback_data='abort_{}'.format(
                                                                          context.user_data['checklist'].id))]
                                            ]))

    return PRICE_STATE


@session_wrapper
def commit_purchase(session, update, context):
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

    item_ids_to_purchase = []
    purchase_dict = context.user_data.pop('purchase_dict')
    for item_id in purchase_dict:
        if '✔️' in purchase_dict[item_id]:
            item_ids_to_purchase.append(item_id)
    purchase_queries.create_purchase(session, user_id, checklist_id, item_ids_to_purchase, price)

    text, markup = response_builder.checklist_menu(session, update.message.from_user, context)
    update.message.reply_text(text, reply_markup=markup, parse_mode='Markdown')

    return ConversationHandler.END
