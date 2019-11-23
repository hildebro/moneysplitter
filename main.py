import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, ChosenInlineResultHandler, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
import dbqueries
import privatestorage

# conversation states
NEWCHECKLIST_NAME = 0
ADDUSER_NAME = 0
ADDITEMS_NAME = 0
REMOVEITEMS_NAME = 0
PURCHASE_ITEM, PURCHASE_PRICE = range(2)
DELETECHECKLIST_CONFIRM = 0

# group 0 methods
def start(update, context):
    if dbqueries.check_user_exists(update.message.chat_id):
        update.message.reply_text('You already started the bot!')
        refresh_username(update, context)
        return

    dbqueries.register_user(update.message.chat)
    update.message.reply_text('Hello! This bot serves two functions:\n1) Allow a group of people to create a common checklist for items which they want to buy together. Individual users can mark items as purchased and define how much money they spend on them.\n2) Calculate the amounts of money that have to be transfered between group members in order for everyone to be even.')

def refresh_username(update, context):
    dbqueries.refresh_username(update.message.chat)

# main menu rendering
def main_menu_from_message(update, context):
    context.chat_data.pop('checklist_id', None)
    context.chat_data['checklist_names'] = {}
    reply_markup = main_menu_reply_markup(context, update.message.chat_id)
    update.message.reply_text('Choose a checklist to interact with:', reply_markup=reply_markup)

def main_menu_from_callback(update, context, as_new = False):
    context.chat_data.pop('checklist_id', None)
    context.chat_data['checklist_names'] = {}
    reply_markup = main_menu_reply_markup(context, update.callback_query.message.chat_id)
    if as_new:
        update.callback_query.message.reply_text('Choose a checklist to interact with:', reply_markup=reply_markup)
        return

    update.callback_query.edit_message_text(text = 'Choose a checklist to interact with:', reply_markup=reply_markup)

def main_menu_reply_markup(context, user_id):
    checklists = dbqueries.find_checklists_by_participant(user_id)
    keyboard = []
    for checklist in checklists:
        context.chat_data['checklist_names'][checklist['id']] = checklist['name']
        keyboard.append([InlineKeyboardButton(checklist['name'], callback_data= 'checklist_{}'.format(checklist['id']))])
    keyboard.append([InlineKeyboardButton('Create new checklist', callback_data='newchecklist')])

    return InlineKeyboardMarkup(keyboard)

def checklist_options(update, context):
    context.chat_data['checklist_id'] = int(update.callback_query.data.split('_')[1])
    keyboard = []
    keyboard.append([InlineKeyboardButton('Show items', callback_data='showitems')])
    keyboard.append([InlineKeyboardButton('Add items', callback_data='additems')])
    keyboard.append([InlineKeyboardButton('Start purchase', callback_data='newpurchase')])
    keyboard.append([InlineKeyboardButton('Advanced Options', callback_data='advancedoptions')])
    keyboard.append([InlineKeyboardButton('Back to all checklists', callback_data='mainmenu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text = 'Choose an action:', reply_markup=reply_markup)

def advanced_options(update, context):
    checklist_id = context.chat_data['checklist_id']
    keyboard = []
    keyboard.append([InlineKeyboardButton('Show purchases', callback_data='showpurchases')])
    keyboard.append([InlineKeyboardButton('Remove items', callback_data='removeitems')])
    keyboard.append([InlineKeyboardButton('Add user', callback_data='adduser')])
    if dbqueries.is_creator(checklist_id, update.callback_query.from_user.id):
        keyboard.append([InlineKeyboardButton('Delete checklist', callback_data='deletechecklist')])
    keyboard.append([InlineKeyboardButton('Back to default options', callback_data='checklist_{}'.format(checklist_id))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text = 'Choose an action:', reply_markup=reply_markup)

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

def conv_newchecklist_init(update, context):
    update.callback_query.edit_message_text(text = 'What name should the new checklist have?')

    return NEWCHECKLIST_NAME

def conv_newchecklist_check(update, context):
    checklist_name = update.message.text
    user_id = update.message.chat_id

    if dbqueries.checklist_name_exists(user_id, checklist_name):
        update.message.reply_text('You already have a checklist with that name. Please provide a new name or stop the process with /cancel.')

        return NEWCHECKLIST_NAME

    dbqueries.make_checklist(checklist_name, user_id)
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
    purchases = dbqueries.find_purchases(checklist_id)
    if len(purchases) == 0:
        text = checklist_name + ' has no purchases.'
    else:
        text = ''
        for username, purchase in purchases.items():
            text += '{} has paid {} for the following items:\n'.format(username, purchase['price']) + '\n'.join(purchase['items']) + '\n'

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
            entry_points = [CallbackQueryHandler(conv_newchecklist_init, pattern = '^newchecklist$')],
            states = {
                NEWCHECKLIST_NAME: [MessageHandler(Filters.text, conv_newchecklist_check)],
            },
            fallbacks = [CommandHandler('cancel', conv_cancel)]
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

