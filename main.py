import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, ChosenInlineResultHandler, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
import dbqueries
import privatestorage

PARTY_NAME = 0
ADD_USER_PARTY, ADD_USER_NAME = range(2)
ADD_ITEMS_PARTY, ADD_ITEMS_NAME = range(2)
PURCHASE_PARTY, PURCHASE_ITEM, PURCHASE_PRICE = range(3)

def start(update, context):
    dbqueries.register_user(update.message.chat)
    update.message.reply_text('Hello! This bot serves two functions:\n1) Allow a group of people to create a common checklist for items which they want to buy together. Individual users can mark items as purchased and define how much money they spend on them.\n2) Calculate the amounts of money that have to be transfered between group members in order for everyone to be even.')

def refresh_username(update, context):
    dbqueries.refresh_username(update.message.chat)

def show_commands(update, context):
    commands = '\n'.join([
        '/start Starts the bot',
        '/make_checklist Creates a new checklist',
        '/show_checklists Shows all checklists that you have created',
        '/add_user Adds other telegram users to one of your checklists',
        '/add_items Adds items to a checklist',
        '/show_items Shows all items of a checklist',
        '/make_purchase Allows you to mark checklist items as purchased',
        '/cancel Can be used during the execution of other commands in order to cancel them'
    ])
    update.message.reply_text(commands)

def conv_cancel(update, context):
    update.message.reply_text('The command has been canceled.')

    return ConversationHandler.END

def conv_make_checklist_init(update, context):
    update.message.reply_text('What name should the new checklist have?')

    return PARTY_NAME

def conv_make_checklist_name(update, context):
    checklist_name = update.message.text
    user_id = update.message.chat_id

    if dbqueries.checklist_name_exists(user_id, checklist_name):
        update.message.reply_text('You already have a checklist with that name. Please provide a new name or stop the process with /cancel.')

        return PARTY_NAME

    dbqueries.make_checklist(checklist_name, user_id)
    update.message.reply_text('Checklist created.')

    return ConversationHandler.END

def conv_add_user_init(update, context):
    checklists = dbqueries.find_checklists_by_creator(update.message.chat_id)
    keyboard = []
    for checklist in checklists:
        keyboard.append([InlineKeyboardButton(checklist['name'], callback_data=checklist['id'])])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a checklist to add users to:', reply_markup=reply_markup)

    return ADD_USER_PARTY

def conv_add_user_pick_checklist(update, context):
    context.chat_data['checklist_id'] = update.callback_query.data
    update.callback_query.edit_message_text(text='Now provide the username of who you want to add.')

    return ADD_USER_NAME

def conv_add_user_get_name(update, context):
    args = update.message.text.split(' ')
    if len(args) > 1:
        # todo enable checklist of users to be added with @ annotation
        update.message.reply_text('Please provide a single username.')

        return ADD_USER_NAME

    user = dbqueries.find_user(args[0])
    if user is None:
        update.message.reply_text('Username not found. Make sure they initiated the bot with /start. If they changed their username since starting the bot, they have to execute /refresh_username. Provide a different name or cancel the transaction with /cancel.')

        return ADD_USER_NAME

    # todo ask user, whether they want to join. if they dont, ask if they want to shadowban the inviter
    dbqueries.checklist_add(context.chat_data['checklist_id'], user['id'])
    update.message.reply_text('User added.')

    return ConversationHandler.END

def conv_add_items_init(update, context):
    checklists = dbqueries.find_checklists_by_participant(update.message.chat_id)
    keyboard = []
    for checklist in checklists:
        keyboard.append([InlineKeyboardButton(checklist['name'], callback_data=checklist['id'])])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a checklist to add items to:', reply_markup=reply_markup)

    return ADD_ITEMS_PARTY

def conv_add_items_pick_checklist(update, context):
    context.chat_data['checklist_id'] = update.callback_query.data
    update.callback_query.edit_message_text(text='Now provide item names to add them to the checklist. Please send one message per item. Use /finish when you are done.')

    return ADD_ITEMS_NAME

def conv_add_items_get_names(update, context):
    item_name = update.message.text

    dbqueries.add_item(item_name, context.chat_data['checklist_id'])
    update.message.reply_text('Item added. Provide more item names or use /finish.')

    return ADD_ITEMS_NAME

def conv_add_items_finish(update, context):
    update.message.reply_text('Finished adding items.')

    return ConversationHandler.END

def show_checklists(update, context):
    checklists = dbqueries.find_checklists_by_creator(update.message.chat_id)
    if len(checklists) == 0:
        update.message.reply_text("You don't have any checklists yet.")
        return

    checklists = map(lambda checklist: checklist['name'], checklists)
    update.message.reply_text('Your checklists:\n' + '\n'.join(checklists))

def show_items(update, context):
    checklists = dbqueries.find_checklists_by_participant(update.message.chat_id)
    keyboard = []
    for checklist in checklists:
        keyboard.append([InlineKeyboardButton(checklist['name'], callback_data = 'showitems_' + str(checklist['id']))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a checklist to show items for:', reply_markup=reply_markup)

def show_items_callback(update, context):
    query = update.callback_query
    checklist_id = query.data.split('_')[1]
    checklist_items = dbqueries.find_checklist_items(checklist_id)
    if len(checklist_items) == 0:
        query.edit_message_text(text = 'That checklist has no items.')
        return

    query.edit_message_text(text = 'Items in that checklist:\n' + '\n'.join(checklist_items))

def conv_purchase_init(update, context):
    checklists = dbqueries.find_checklists_by_participant(update.message.chat_id)
    keyboard = []
    for checklist in checklists:
        keyboard.append([InlineKeyboardButton(checklist['name'], callback_data=checklist['id'])])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a group to make purchases for:', reply_markup=reply_markup)

    return PURCHASE_PARTY

def conv_purchase_checklist_items(update, context):
    user_id = update.callback_query.message.chat_id
    checklist_id = update.callback_query.data
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

    return ConversationHandler.END

def inline_query_handling(update, context):
    query = update.inline_query.query
    if not query:
        context.bot.answer_inline_query(update.inline_query.id, [])
        return

    inline_options = []
    for checklist in dbqueries.find_checklists_by_participant(update.inline_query.from_user['id']):
        inline_options.append(
            InlineQueryResultArticle(
                id=checklist['id'],
                title='Add item "{}" to checklist "{}"'.format(query, checklist['name']),
                input_message_content=InputTextMessageContent(
                    'New item *{}* being added to checklist *{}*...'.format(query, checklist['name']),
                    parse_mode = 'Markdown'
                )
            )
        )
    context.bot.answer_inline_query(update.inline_query.id, inline_options)

def inline_result_handling(update, context):
    result = update.chosen_inline_result
    dbqueries.add_item(result.query, result.result_id)
    # todo change to message only displayed when error happens
    result.from_user.send_message('Item *{}* added successfully'.format(result.query), parse_mode='Markdown')

def unknown_command(update, context):
    update.message.reply_text('Unrecognized command. Use /help for a checklist of valid commands..')

def unexpected_text(update, context):
    update.message.reply_text('I did not expect a text from you at this time. Please refer to /help for instructions. If you called a command which asked you for input, it might have timed out. There might also be an issue on my end. If the problem persists, please write a bug report at https://github.com/hillburn/moneysplitter/issues')

def main():
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    updater = Updater(privatestorage.get_token(), use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.all, refresh_username), group = 0)
    dp.add_handler(
        ConversationHandler(
            entry_points = [CommandHandler('make_checklist', conv_make_checklist_init)],
            states = {
                PARTY_NAME: [MessageHandler(Filters.text, conv_make_checklist_name)],
            },
            fallbacks = [CommandHandler('cancel', conv_cancel)]
        ),
        group = 1
    )
    dp.add_handler(
        ConversationHandler(
           entry_points = [CommandHandler('add_user', conv_add_user_init)],
           states = {
               ADD_USER_PARTY: [CallbackQueryHandler(conv_add_user_pick_checklist)],
               ADD_USER_NAME: [MessageHandler(Filters.text, conv_add_user_get_name)]
            },
            fallbacks = [CommandHandler('cancel', conv_cancel)]
        ),
        group = 1
    )
    dp.add_handler(
        ConversationHandler(
           entry_points = [CommandHandler('add_items', conv_add_items_init)],
           states = {
               ADD_ITEMS_PARTY: [CallbackQueryHandler(conv_add_items_pick_checklist)],
               ADD_ITEMS_NAME: [
                   CommandHandler('finish', conv_add_items_finish),
                   MessageHandler(Filters.text, conv_add_items_get_names)
                ]
            },
            fallbacks = [CommandHandler('cancel', conv_cancel)]
        ),
        group = 1
    )
    dp.add_handler(
        ConversationHandler(
            entry_points = [CommandHandler('make_purchase', conv_purchase_init)],
            states = {
                PURCHASE_PARTY: [CallbackQueryHandler(conv_purchase_checklist_items)],
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
    dp.add_handler(InlineQueryHandler(inline_query_handling), group = 1)
    dp.add_handler(ChosenInlineResultHandler(inline_result_handling), group = 1)
    dp.add_handler(CommandHandler('start', start), group = 1)
    dp.add_handler(CommandHandler('refresh_username', refresh_username))
    dp.add_handler(CommandHandler('help', show_commands), group = 1)
    dp.add_handler(CommandHandler('show_checklists', show_checklists), group = 1)
    dp.add_handler(CommandHandler('show_items', show_items), group = 1)
    dp.add_handler(CallbackQueryHandler(show_items_callback, pattern = '^showitems_[0-9]+$'), group = 1)
    dp.add_handler(MessageHandler(Filters.command, unknown_command), group = 1)
    dp.add_handler(MessageHandler(Filters.text, unexpected_text), group = 1)
    updater.start_polling()
    print('Started polling...')
    updater.idle()

if __name__ == '__main__':
    main()

