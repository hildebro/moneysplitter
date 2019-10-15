import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, ChosenInlineResultHandler, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
import dbqueries
import privatestorage

NEWCHECKLIST_NAME = 0
ADDUSER_NAME = 0
ADDITEMS_NAME = 0
PURCHASE_ITEM, PURCHASE_PRICE = range(2)

def start(update, context):
    # todo you already started the bot
    dbqueries.register_user(update.message.chat)
    update.message.reply_text('Hello! This bot serves two functions:\n1) Allow a group of people to create a common checklist for items which they want to buy together. Individual users can mark items as purchased and define how much money they spend on them.\n2) Calculate the amounts of money that have to be transfered between group members in order for everyone to be even.')

def refresh_username(update, context):
    dbqueries.refresh_username(update.message.chat)

def main_menu_from_message(update, context):
    # todo check whether chat_data persists between callbacks
    checklists = dbqueries.find_checklists_by_creator(update.message.chat_id)
    keyboard = []
    for checklist in checklists:
        keyboard.append([InlineKeyboardButton(checklist['name'], callback_data= 'checklist_{}'.format(checklist['id']))])

    keyboard.append([InlineKeyboardButton('Create new checklist', callback_data='newchecklist')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a checklist to interact with:', reply_markup=reply_markup)

def main_menu_from_callback(update, context):
    # todo check whether chat_data persists between callbacks
    checklists = dbqueries.find_checklists_by_creator(update.callback_query.message.chat_id)
    keyboard = []
    for checklist in checklists:
        keyboard.append([InlineKeyboardButton(checklist['name'], callback_data= 'checklist_{}'.format(checklist['id']))])

    keyboard.append([InlineKeyboardButton('Create new checklist', callback_data='newchecklist')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text = 'Choose a checklist to interact with:', reply_markup=reply_markup)


def checklist_options(update, context):
    context.chat_data['checklist_id'] = update.callback_query.data.split('_')[1]
    keyboard = []
    keyboard.append([InlineKeyboardButton('Show items', callback_data='showitems')])
    keyboard.append([InlineKeyboardButton('Add items', callback_data='additems')])
    keyboard.append([InlineKeyboardButton('Add user', callback_data='adduser')])
    keyboard.append([InlineKeyboardButton('Start purchase', callback_data='purchase')])
    keyboard.append([InlineKeyboardButton('Back to all checklists', callback_data='mainmenu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text = 'Choose an action:', reply_markup=reply_markup)

def conv_cancel(update, context):
    update.message.reply_text('The command has been canceled.')
    # todo back to main menu

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
    # todo back to main menu

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
    dbqueries.checklist_add(context.chat_data['checklist_id'], user['id'])
    update.message.reply_text('User added.')
    # todo back to main menu

    return ConversationHandler.END

def conv_additems_init(update, context):
    update.callback_query.edit_message_text(text='Now send me an item name to add to the list. Send one message per item. Use /finish when you are done.')

    return ADDITEMS_NAME

def conv_additems_check(update, context):
    item_name = update.message.text
    dbqueries.add_item(item_name, context.chat_data['checklist_id'])
    update.message.reply_text('Item added. Provide more names or stop adding by using /finish.')

    return ADDITEMS_NAME

def conv_additems_finish(update, context):
    update.message.reply_text('Finished adding items.')
    # tod back to main menu

    return ConversationHandler.END

def show_items(update, context):
    query = update.callback_query
    checklist_id = context.chat_data['checklist_id']
    checklist_items = dbqueries.find_checklist_items(checklist_id)
    if len(checklist_items) == 0:
        query.edit_message_text(text = 'That checklist has no items.')
        # todo back to main menu
        return

    query.edit_message_text(text = 'Items in that checklist:\n' + '\n'.join(checklist_items))
    # todo back to main menu

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
    # todo back to main menu

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
    # todo back to main menu

    return ConversationHandler.END

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
            entry_points = [CallbackQueryHandler(conv_purchase_init, pattern = '^purchase$')],
            states = {
                PURCHASE_ITEM: [
                    CallbackQueryHandler(conv_purchase_buffer_item, pattern = '^bi_.*'),
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

    #dp.add_handler(InlineQueryHandler(inline_query_handling), group = 1)
    #dp.add_handler(ChosenInlineResultHandler(inline_result_handling), group = 1)

    dp.add_handler(CallbackQueryHandler(main_menu_from_callback, pattern = '^mainmenu$'), group = 1)
    dp.add_handler(CallbackQueryHandler(show_items, pattern = '^showitems$'), group = 1)
    dp.add_handler(CallbackQueryHandler(checklist_options, pattern = '^checklist_[0-9]+$'), group = 1)

    dp.add_handler(MessageHandler(Filters.all, main_menu_from_message), group = 1)

    updater.start_polling()
    print('Started polling...')
    updater.idle()

if __name__ == '__main__':
    main()

