import logging
import operator

from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, \
    ConversationHandler

import dbqueries
import entity.queries.checklist_queries as checklist_queries
import entity.queries.user_queries as user_queries
import privatestorage

# conversation states
NEWCHECKLIST_NAME = 0
ADDUSER_NAME = 0
ADDITEMS_NAME = 0
REMOVEITEMS_NAME = 0
PURCHASE_ITEM, PURCHASE_PRICE = range(2)
EQUALIZE_SELECT = 0
DELETECHECKLIST_CONFIRM = 0


# group 0 methods
def start(update, context):
    user = update.message.from_user
    if user_queries.exists(user.id):
        update.message.reply_text('You already started the bot!')
        refresh_username(update, context)
        return

    user_queries.register(update.message.from_user)
    update.message.reply_text('Hello! This bot serves two functions:\n1) Allow a group of people to create a common '
                              'checklist for items which they want to buy together. Individual users can mark items '
                              'as purchased and define how much money they spend on them.\n2) Calculate the amounts '
                              'of money that have to be transferred between group members in order for everyone to be '
                              'even.')


def refresh_username(update, context):
    user_queries.refresh(update.message.from_user)


# main menu rendering
def main_menu_from_message(update, context):
    context.chat_data.pop('checklist_id', None)
    context.chat_data['checklist_names'] = {}
    reply_markup = main_menu_reply_markup(context, update.message.chat_id)
    update.message.reply_text('Choose a checklist to interact with:', reply_markup=reply_markup)


def main_menu_from_callback(update, context, as_new=False):
    context.chat_data.pop('checklist_id', None)
    context.chat_data['checklist_names'] = {}
    reply_markup = main_menu_reply_markup(context, update.callback_query.message.chat_id)
    if as_new:
        update.callback_query.message.reply_text('Choose a checklist to interact with:', reply_markup=reply_markup)
        return

    update.callback_query.edit_message_text(text='Choose a checklist to interact with:', reply_markup=reply_markup)


def main_menu_reply_markup(context, user_id):
    checklists = checklist_queries.find_by_participant(user_id)
    keyboard = []
    for checklist in checklists:
        context.chat_data['checklist_names'][checklist.id] = checklist.name
        keyboard.append([InlineKeyboardButton(checklist.name, callback_data='checklist_{}'.format(checklist.id))])
    keyboard.append([InlineKeyboardButton('Create new checklist', callback_data='newchecklist')])

    return InlineKeyboardMarkup(keyboard)


def checklist_options(update, context):
    context.chat_data['checklist_id'] = int(update.callback_query.data.split('_')[1])
    keyboard = [[InlineKeyboardButton('Show items', callback_data='showitems')],
                [InlineKeyboardButton('Add items', callback_data='additems')],
                [InlineKeyboardButton('Start purchase', callback_data='newpurchase')],
                [InlineKeyboardButton('Advanced Options', callback_data='advancedoptions')],
                [InlineKeyboardButton('Back to all checklists', callback_data='mainmenu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text='Choose an action:', reply_markup=reply_markup)


def advanced_options(update, context):
    checklist_id = context.chat_data['checklist_id']
    keyboard = [[InlineKeyboardButton('Show purchases', callback_data='showpurchases')],
                [InlineKeyboardButton('Equalize', callback_data='equalize')],
                [InlineKeyboardButton('Remove items', callback_data='removeitems')],
                [InlineKeyboardButton('Add user', callback_data='adduser')]]
    if checklist_queries.is_creator(checklist_id, update.callback_query.from_user.id):
        keyboard.append([InlineKeyboardButton('Delete checklist', callback_data='deletechecklist')])

    keyboard.append(
        [InlineKeyboardButton('Back to default options', callback_data='checklist_{}'.format(checklist_id))]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text='Choose an action:', reply_markup=reply_markup)

def conv_deletechecklist_init(update, context):
    update.callback_query.edit_message_text(text = 'You are about to delete the selected checklist. If you really want to do this, type /delete. Otherwise, type /cancel.')

    return DELETECHECKLIST_CONFIRM

def conv_deletechecklist_execute(update, context):
    checklist_id = context.chat_data['checklist_id']
    dbqueries.delete_checklist(checklist_id, update.message.chat_id)
    update.message.reply_text('Checklist deleted.')


def conv_cancel(update, context):
    update.message.reply_text('The action has been canceled.')
    main_menu_from_message(update, context)

    return ConversationHandler.END


def conv_new_checklist_init(update, context):
    update.callback_query.edit_message_text(text='What name should the new checklist have?')

    return NEWCHECKLIST_NAME


def conv_new_checklist_check(update, context):
    checklist_name = update.message.text
    user_id = update.message.from_user.id

    if checklist_queries.exists(user_id, checklist_name):
        update.message.reply_text('You already have a checklist with that name. Please provide a new name or stop the '
                                  'process with /cancel.')

        return NEWCHECKLIST_NAME

    checklist_queries.create(user_id, checklist_name)
    update.message.reply_text('Checklist created.')
    main_menu_from_message(update, context)

    return ConversationHandler.END

def conv_adduser_init(update, context):
    update.callback_query.edit_message_text(text = 'What is the username of the person you want to add?')

    return ADDUSER_NAME

def conv_adduser_check(update, context):
    args = update.message.text.split(' ')
    if len(args) > 1:
        # todo enable checklist of users to be added with @ annotation
        update.message.reply_text('Please provide a single username.')

        return ADDUSER_NAME

    user = dbqueries.find_user(args[0])
    if user is None:
        update.message.reply_text('Username not found. Make sure they initiated the bot with /start. If they changed their username since starting the bot, they have to execute /refresh_username. Provide a different name or cancel the transaction with /cancel.')

        return ADDUSER_NAME

    # todo ask user, whether they want to join. if they dont, ask if they want to shadowban the inviter
    checklist_id = context.chat_data['checklist_id']
    dbqueries.checklist_add(checklist_id, user['id'])
    update.message.reply_text(
        '{} was added to {}.'.format(
            user['username'],
            context.chat_data['checklist_names'][checklist_id]
        )
    )
    main_menu_from_message(update, context)

    return ConversationHandler.END

def conv_additems_init(update, context):
    checklist_name = context.chat_data['checklist_names'][context.chat_data['checklist_id']]
    update.callback_query.edit_message_text(text='Send me item names (one at a time) to add them to {}. Use /finish when you are done.'.format(checklist_name))

    return ADDITEMS_NAME

def conv_additems_check(update, context):
    item_name = update.message.text
    checklist_id = context.chat_data['checklist_id']
    dbqueries.add_item(item_name, checklist_id)
    update.message.reply_text(
        '{} added to {}. Provide more items or stop the action with /finish.'.format(
            item_name, context.chat_data['checklist_names'][checklist_id]
        )
    )

    return ADDITEMS_NAME

def conv_additems_finish(update, context):
    update.message.reply_text('Finished adding items.')
    main_menu_from_message(update, context)

    return ConversationHandler.END

def conv_removeitems_init(update, context):
    render_items_to_remove(update, context)

    return REMOVEITEMS_NAME

def conv_removeitems_check(update, context):
    query = update.callback_query
    item_name = query.data.split('_')[1]
    checklist_id = context.chat_data['checklist_id']
    dbqueries.remove_item(item_name, checklist_id)
    render_items_to_remove(update, context)

    return REMOVEITEMS_NAME

def conv_removeitems_finish(update, context):
    update.callback_query.edit_message_text(text = 'Finished removing items.')
    main_menu_from_callback(update, context)

    return ConversationHandler.END

def render_items_to_remove(update, context):
    item_names = dbqueries.find_checklist_items(context.chat_data['checklist_id'])
    keyboard = []
    for item_name in item_names:
        keyboard.append([InlineKeyboardButton(item_name, callback_data='ri_{}'.format(item_name))])

    # todo either buffer table like with purchases or use chat data for buffer
    #keyboard.append([
    #    InlineKeyboardButton('Revert', callback_data='ri'),
    #    InlineKeyboardButton('Abort', callback_data='ap')
    #])
    keyboard.append([
        InlineKeyboardButton('Finish', callback_data='finish')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text = 'Choose items to remove from the list:', reply_markup=reply_markup)

def show_items(update, context):
    query = update.callback_query
    checklist_id = context.chat_data['checklist_id']
    checklist_name = context.chat_data['checklist_names'][checklist_id]
    checklist_items = dbqueries.find_checklist_items(checklist_id)
    if len(checklist_items) == 0:
        query.edit_message_text(text = checklist_name + ' has no items.')
    else:
        query.edit_message_text(text =
                checklist_name
                + ' contains the following items:\n'
                + '\n'.join(checklist_items)
        )
    main_menu_from_callback(update, context, True)


def show_purchases(update, context):
    query = update.callback_query
    checklist_id = context.chat_data['checklist_id']
    checklist_name = context.chat_data['checklist_names'][checklist_id]
    purchases = dbqueries.find_purchases_by_checklist(checklist_id)
    if len(purchases) == 0:
        text = checklist_name + ' has no purchases.'
    else:
        text = ''
        for purchase in purchases.values():
            text += '{} has paid {} for the following items:\n'.format(purchase['username'], purchase['price']) + '\n'.join(purchase['items']) + '\n'

    query.edit_message_text(text = text)
    main_menu_from_callback(update, context, True)

def conv_purchase_init(update, context):
    user_id = update.callback_query.message.chat_id
    checklist_id = context.chat_data['checklist_id']
    purchase_id = dbqueries.start_purchase(user_id, checklist_id)
    context.chat_data['purchase_id'] = purchase_id
    render_items_to_purchase(update, context)

    return PURCHASE_ITEM

def conv_purchase_buffer_item(update, context):
    query = update.callback_query
    query_data = query.data.split('_')
    item_name = query_data[1]
    dbqueries.buffer_item(item_name, context.chat_data['purchase_id'])
    render_items_to_purchase(update, context)

    return PURCHASE_ITEM

def conv_purchase_revert_item(update, context):
    purchase_id = context.chat_data['purchase_id']
    reverted = dbqueries.unbuffer_last_item(purchase_id)
    if not reverted:
        # todo make popup: nothing to revert
        print('nothing to revert')
        return
    render_items_to_purchase(update, context)

    return PURCHASE_ITEM

def conv_purchase_abort(update, context):
    dbqueries.abort_purchase(context.chat_data['purchase_id'])
    update.callback_query.edit_message_text(text = 'Purchase aborted.')
    main_menu_from_callback(update, context, True)

    return ConversationHandler.END

def render_items_to_purchase(update, context):
    item_names = dbqueries.find_items_to_purchase(context.chat_data['purchase_id'])
    keyboard = []
    for item_name in item_names:
        keyboard.append([InlineKeyboardButton(item_name, callback_data='bi_{}'.format(item_name))])

    keyboard.append([
        InlineKeyboardButton('Revert', callback_data='ri'),
        InlineKeyboardButton('Abort', callback_data='ap')
    ])
    keyboard.append([
        InlineKeyboardButton('Finish', callback_data='fp')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text = 'Choose items to purchase:', reply_markup=reply_markup)

def conv_purchase_finish(update, context):
    purchase_id = context.chat_data['purchase_id']
    dbqueries.finish_purchase(purchase_id)
    update.callback_query.edit_message_text(text = 'Purchase comitted. How much did you spend?')

    return PURCHASE_PRICE

def conv_purchase_set_price(update, context):
    dbqueries.set_purchase_price(context.chat_data['purchase_id'], update.message.text)
    update.message.reply_text('Price has been set.')
    main_menu_from_message(update, context)

    return ConversationHandler.END

def conv_equalize_init(update, context):
    context.user_data['buffered_purchases'] = []
    render_purchases_to_equalize(update, context)

    return EQUALIZE_SELECT

def conv_equalize_buffer_purchase(update, context):
    query = update.callback_query
    query_data = query.data.split('_')
    purchase_id = query_data[1]
    context.user_data['buffered_purchases'].append(int(purchase_id))
    render_purchases_to_equalize(update, context)

    return EQUALIZE_SELECT

def conv_equalize_revert_purchase(update, context):
    buffered_purchases = context.user_data['buffered_purchases']
    if not buffered_purchases:
        # todo make popup: nothing to revert
        print('nothing to revert')
        return

    buffered_purchases.pop()
    render_purchases_to_equalize(update, context)

    return EQUALIZE_SELECT

def render_purchases_to_equalize(update, context):
    purchases = dbqueries.find_purchases_to_equalize(context.chat_data['checklist_id'])
    keyboard = []
    for purchase in purchases:
        if purchase[0] not in context.user_data['buffered_purchases']:
            keyboard.append([InlineKeyboardButton(
                '{} spent {}'.format(purchase[2], purchase[1]/100),
                callback_data='bp_{}'.format(purchase[0])
            )])

    keyboard.append([
        InlineKeyboardButton('Revert', callback_data='rp'),
        InlineKeyboardButton('Abort', callback_data='ae')
    ])
    keyboard.append([
        InlineKeyboardButton('Finish', callback_data='fe')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text = 'Choose purchases to equalize:', reply_markup=reply_markup)

def conv_equalize_abort(update, context):
    update.callback_query.edit_message_text(text = 'Equalization aborted.')
    main_menu_from_callback(update, context, True)

    return ConversationHandler.END

def conv_equalize_finish(update, context):
    summed_purchases = {}
    average_price = 0
    # sum up purchase prices
    purchases = dbqueries.find_purchases(context.user_data['buffered_purchases'])
    for purchase in purchases:
        average_price += purchase[1]
        if purchase[0] not in summed_purchases:
            summed_purchases[purchase[0]] = purchase[1]
        else:
            summed_purchases[purchase[0]] += purchase[1]

    # add entry with price of 0 for everyone who hasn't purchased anything
    participants = dbqueries.find_checklist_participants(context.chat_data['checklist_id'])
    for participant in participants:
        if participant[0] not in summed_purchases:
            summed_purchases[participant[0]] = 0

    # sort by price (has to be a tuple now)
    sorted_purchases = sorted(summed_purchases.items(), key=operator.itemgetter(1))
    average_price /= len(summed_purchases)
    lowboi = 0
    highboi = len(sorted_purchases) - 1
    transactions = []
    while lowboi < highboi:
        to_give = average_price - sorted_purchases[lowboi][1]
        if to_give == 0:
            lowboi += 1
            continue

        to_get = sorted_purchases[highboi][1] - average_price
        if to_get == 0:
            highboi -= 1
            continue

        if to_give > to_get:
            to_give = to_get

        sorted_purchases[lowboi] = (sorted_purchases[lowboi][0], sorted_purchases[lowboi][1] + to_give)
        sorted_purchases[highboi] = (sorted_purchases[highboi][0], sorted_purchases[highboi][1] - to_give)

        transactions.append({
            'from': sorted_purchases[lowboi][0],
            'to': sorted_purchases[highboi][0],
            'amount': to_give
        })

    dbqueries.equalize_purchases(context.user_data['buffered_purchases'])

    transaction_message = 'The chosen purchases have been equalized under the assumption that the following equalizations will be done:\n'
    for transaction in transactions:
        transaction_message += '{} has to send {} to {}\n'.format(
            dbqueries.find_username(transaction['from']),
            transaction['amount'] / 100,
            dbqueries.find_username(transaction['to'])
        )
    update.callback_query.edit_message_text(text = transaction_message)

    main_menu_from_callback(update, context, True)

    return ConversationHandler.END

def inlinequery_send_invite(update, context):
    query = update.inline_query.query

    inline_options = []
    for checklist in dbqueries.find_checklists_by_participant(update.inline_query.from_user['id']):
        if query and not checklist['name'].lower().startswith(query.lower()):
                continue

        inline_options.append(
            InlineQueryResultArticle(
                id=checklist['id'],
                title=checklist['name'],
                input_message_content=InputTextMessageContent(
                    "You are invited to join the checklist {}. Press the button under this message to confirm. If you don't know what this means, check out @PurchaseSplitterBot for more info.".format(checklist['name'])
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('Join checklist', callback_data='joinchecklist_{}'.format(checklist['id']))
                ]])
            )
        )
    context.bot.answer_inline_query(update.inline_query.id, inline_options)

def join_checklist(update, context):
    checklist_id = update.callback_query.data.split('_')[1]
    user_id = update.callback_query.from_user.id
    dbqueries.checklist_add(checklist_id, user_id)
    update.callback_query.answer('Successfully joined checklist!')

def main():
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    updater = Updater(privatestorage.get_token(), use_context=True)
    dp = updater.dispatcher
    # group 0: persist new user or update existing ones
    dp.add_handler(CommandHandler('start', start), group = 0)
    dp.add_handler(MessageHandler(Filters.all, refresh_username), group = 0)
    # group 1: actual interactions with the bot
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(conv_new_checklist_init, pattern='^newchecklist$')],
            states={
                NEWCHECKLIST_NAME: [MessageHandler(Filters.text, conv_new_checklist_check)],
            },
            fallbacks=[CommandHandler('cancel', conv_cancel)]
        ),
        group = 1
    )
    dp.add_handler(
        ConversationHandler(
            entry_points = [CallbackQueryHandler(conv_adduser_init, pattern = '^adduser$')],
            states = {
                ADDUSER_NAME: [MessageHandler(Filters.text, conv_adduser_check)]
            },
            fallbacks = [CommandHandler('cancel', conv_cancel)]
        ),
        group = 1
    )
    dp.add_handler(
        ConversationHandler(
           entry_points = [CallbackQueryHandler(conv_additems_init, pattern = '^additems$')],
           states = {
               ADDITEMS_NAME: [
                   CommandHandler('finish', conv_additems_finish),
                   MessageHandler(Filters.text, conv_additems_check)
                ]
            },
            fallbacks = [CommandHandler('cancel', conv_cancel)]
        ),
        group = 1
    )
    dp.add_handler(
        ConversationHandler(
            entry_points = [CallbackQueryHandler(conv_removeitems_init, pattern = '^removeitems$')],
            states = {
                REMOVEITEMS_NAME: [
                    CallbackQueryHandler(conv_removeitems_check, pattern = '^ri_.+'),
                    CallbackQueryHandler(conv_removeitems_finish, pattern = '^finish$')
                ]
            },
            fallbacks = [CommandHandler('cancel', conv_cancel)]
        ),
        group = 1
    )
    dp.add_handler(
        ConversationHandler(
            entry_points = [CallbackQueryHandler(conv_purchase_init, pattern = '^newpurchase$')],
            states = {
                PURCHASE_ITEM: [
                    CallbackQueryHandler(conv_purchase_buffer_item, pattern = '^bi_.+'),
                    CallbackQueryHandler(conv_purchase_revert_item, pattern = '^ri$'),
                    CallbackQueryHandler(conv_purchase_finish, pattern = '^fp$'),
                    CallbackQueryHandler(conv_purchase_abort, pattern = '^ap$')
                ],
                PURCHASE_PRICE: [MessageHandler(Filters.text, conv_purchase_set_price)]
            },
            fallbacks=[CommandHandler('cancel', conv_cancel)]
        ),
        group = 1
    )
    dp.add_handler(
        ConversationHandler(
            entry_points = [CallbackQueryHandler(conv_equalize_init, pattern = '^equalize$')],
            states = {
                EQUALIZE_SELECT: [
                    CallbackQueryHandler(conv_equalize_buffer_purchase, pattern = '^bp_.+'),
                    CallbackQueryHandler(conv_equalize_revert_purchase, pattern = '^rp$'),
                    CallbackQueryHandler(conv_equalize_finish, pattern = '^fe$'),
                    CallbackQueryHandler(conv_equalize_abort, pattern = '^ae$')
                ]
            },
            fallbacks=[CommandHandler('cancel', conv_cancel)]
        ),
        group = 1
    )

    dp.add_handler(
        ConversationHandler(
            entry_points = [CallbackQueryHandler(conv_deletechecklist_init, pattern = '^deletechecklist$')],
            states = {
                DELETECHECKLIST_CONFIRM: [
                    CommandHandler('delete', conv_deletechecklist_execute)
                ],
            },
            fallbacks=[CommandHandler('cancel', conv_cancel)]
        ),
        group = 1
    )

    dp.add_handler(InlineQueryHandler(inlinequery_send_invite), group = 1)

    dp.add_handler(CallbackQueryHandler(main_menu_from_callback, pattern = '^mainmenu$'), group = 1)
    dp.add_handler(CallbackQueryHandler(show_purchases, pattern = '^showpurchases$'), group = 1)
    dp.add_handler(CallbackQueryHandler(show_items, pattern = '^showitems$'), group = 1)
    dp.add_handler(CallbackQueryHandler(checklist_options, pattern = '^checklist_[0-9]+$'), group = 1)
    dp.add_handler(CallbackQueryHandler(advanced_options, pattern = '^advancedoptions$'), group = 1)
    dp.add_handler(CallbackQueryHandler(join_checklist, pattern = '^joinchecklist_[0-9]+$'), group = 1)

    dp.add_handler(MessageHandler(Filters.all, main_menu_from_message), group = 1)

    updater.start_polling()
    print('Started polling...')
    updater.idle()

if __name__ == '__main__':
    main()

