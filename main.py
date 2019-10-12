import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, ChosenInlineResultHandler, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
import dbqueries
import privatestorage

PARTY_NAME = 0
ADD_USER_PARTY, ADD_USER_NAME = range(2)
PURCHASE_PARTY, PURCHASE_ITEM, PURCHASE_PRICE = range(3)

def start(update, context):
    dbqueries.register_user(update.message.chat)
    update.message.reply_text('You are now registered.')

def refresh_username(update, context):
    dbqueries.refresh_username(update.message.chat)
    update.message.reply_text('Username refreshed.')

def conv_cancel(update, context):
    update.message.reply_text('The command has been canceled.')

    return ConversationHandler.END

def conv_make_party_init(update, context):
    update.message.reply_text('Now provide a name for the new party.')

    return PARTY_NAME

def conv_make_party_name(update, context):
    party_name = update.message.text
    user_id = update.message.chat_id

    if dbqueries.find_party_id(user_id, party_name) is not None:
        update.message.reply_text('You already have a party with that name. Please provide something new.')

        return PARTY_NAME

    dbqueries.make_party(party_name, user_id)
    update.message.reply_text('Party created.')

    return ConversationHandler.END

def conv_add_user_init(update, context):
    parties = dbqueries.find_parties_by_creator(update.message.chat_id)
    keyboard = []
    for party in parties:
        keyboard.append([InlineKeyboardButton(party['name'], callback_data=party['id'])])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a party to add users to:', reply_markup=reply_markup)

    return ADD_USER_PARTY

def conv_add_user_pick_party(update, context):
    context.chat_data['party_id'] = update.callback_query.data
    update.callback_query.edit_message_text(text='Now provide the username of who you want to add.')

    return ADD_USER_NAME

def conv_add_user_get_name(update, context):
    args = update.message.text.split(' ')
    if len(args) > 1:
        print('todo enable list of users to be added with @ annotation for groups.')
        update.message.reply_text('Please provide a single username.')

        return ADD_USER_NAME

    user = dbqueries.find_user(args[0])
    if user is None:
        update.message.reply_text('Username not found. Make sure they initiated the bot with /start. If they changed their username since starting the bot, they have to execute /refresh_username. Provide a different name or cancel the transaction with /cancel.')

        return ADD_USER_NAME

    print('todo ask user, whether they want to join. if they dont, ask if they want to shadowban the inviter.')
    dbqueries.party_add(context.chat_data['party_id'], user['id'])
    update.message.reply_text('User added.')

    return ConversationHandler.END

def show_parties(update, context):
    parties = dbqueries.find_parties_by_creator(update.message.chat_id)
    if len(parties) == 0:
        update.message.reply_text("You don't have any parties yet.")
        return

    update.message.reply_text('Your parties:\n' + '\n'.join(parties))

def show_items(update, context):
    parties = dbqueries.find_parties_by_participant(update.message.chat_id)
    keyboard = []
    for party in parties:
        keyboard.append([InlineKeyboardButton(party['name'], callback_data = 'showitems_' + str(party['id']))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a party to show items for:', reply_markup=reply_markup)

def show_items_callback(update, context):
    query = update.callback_query
    party_id = query.data.split('_')[1]
    party_items = dbqueries.find_party_items(party_id = party_id)
    if len(party_items) == 0:
        query.edit_message_text(text = 'That party has no items.')
        return

    query.edit_message_text(
        text = 'Items in that party:\n' + '\n'.join(party_items),
        parse_mode='Markdown'
    )

def conv_purchase_init(update, context):
    parties = dbqueries.find_parties_by_participant(update.message.chat_id)
    keyboard = []
    for party in parties:
        keyboard.append([InlineKeyboardButton(party['name'], callback_data=party['id'])])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a group to make purchases for:', reply_markup=reply_markup)

    return PURCHASE_PARTY

def conv_purchase_list_items(update, context):
    user_id = update.callback_query.message.chat_id
    party_id = update.callback_query.data
    purchase_id = dbqueries.start_purchase(user_id, party_id)
    context.chat_data['purchase_id'] = purchase_id
    render_items_to_purchase(update, context)

    return PURCHASE_ITEM

def conv_purchase_buffer_item(update, context):
    query = update.callback_query
    query_data = query.data.split('_')
    item_name = query_data[1]
    dbqueries.buffer_purchase(item_name, context.chat_data['purchase_id'])
    render_items_to_purchase(update, context)

    return PURCHASE_ITEM

def conv_purchase_revert_item(update, context):
    purchase_id = context.chat_data['purchase_id']
    reverted = dbqueries.revert_purchase(purchase_id)
    if not reverted:
        '''todo make popup: nothing to revert'''
        print('nothing to revert')
        return
    render_items_to_purchase(update, context)

    return PURCHASE_ITEM

def render_items_to_purchase(update, context):
    item_names = dbqueries.find_items_to_purchase(context.chat_data['purchase_id'])
    keyboard = []
    for item_name in item_names:
        keyboard.append([InlineKeyboardButton(item_name, callback_data='bi_{}'.format(item_name))])

    keyboard.append([
        InlineKeyboardButton('Revert', callback_data='ri'),
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
    dbqueries.set_price(context.chat_data['purchase_id'], update.message.text)
    update.message.reply_text('Price has been set.')

    return ConversationHandler.END

def conv_purchase_cancel(update, context):
    update.message.reply_text('canceled TODO.')

def inline_query_handling(update, context):
    query = update.inline_query.query
    if not query:
        context.bot.answer_inline_query(update.inline_query.id, [])
        return

    inline_options = []
    for party in dbqueries.find_parties_by_participant(update.inline_query.from_user['id']):
        inline_options.append(
            InlineQueryResultArticle(
                id=party['id'],
                title='Add item "{}" to party "{}"'.format(query, party['name']),
                input_message_content=InputTextMessageContent(
                    'New item *{}* being added to party *{}*...'.format(query, party['name']),
                    parse_mode = 'Markdown'
                )
            )
        )
    context.bot.answer_inline_query(update.inline_query.id, inline_options)

def inline_result_handling(update, context):
    result = update.chosen_inline_result
    dbqueries.add_item(result.query, result.result_id)
    result.from_user.send_message('Item *{}* added successfully'.format(result.query), parse_mode='Markdown')

def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text='Unrecognized command.')

def main():
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    updater = Updater(privatestorage.get_token(), use_context=True)
    dp = updater.dispatcher
    dp.add_handler(
            ConversationHandler(
                entry_points = [CommandHandler('make_party', conv_make_party_init)],
                states = {
                    PARTY_NAME: [MessageHandler(Filters.text, conv_make_party_name)],
                },
                fallbacks = [CommandHandler('cancel', conv_cancel)]
            )
    )
    dp.add_handler(
            ConversationHandler(
                entry_points = [CommandHandler('add_user', conv_add_user_init)],
                states = {
                    ADD_USER_PARTY: [CallbackQueryHandler(conv_add_user_pick_party)],
                    ADD_USER_NAME: [MessageHandler(Filters.text, conv_add_user_get_name)]
                },
                fallbacks = [CommandHandler('cancel', conv_cancel)]
            )
    )
    dp.add_handler(
            ConversationHandler(
                entry_points = [CommandHandler('make_purchase', conv_purchase_init)],
                states = {
                    PURCHASE_PARTY: [CallbackQueryHandler(conv_purchase_list_items)],
                    PURCHASE_ITEM: [
                        CallbackQueryHandler(conv_purchase_buffer_item, pattern = '^bi_.*'),
                        CallbackQueryHandler(conv_purchase_revert_item, pattern = '^ri$'),
                        CallbackQueryHandler(conv_purchase_finish, pattern = '^fp$')
                    ],
                    PURCHASE_PRICE: [MessageHandler(Filters.text, conv_purchase_set_price)]
                },
                fallbacks=[CommandHandler('cancel', conv_cancel)]
            )
    )
    dp.add_handler(InlineQueryHandler(inline_query_handling))
    dp.add_handler(ChosenInlineResultHandler(inline_result_handling))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('refresh_username', refresh_username))
    dp.add_handler(CommandHandler('show_parties', show_parties))
    dp.add_handler(CommandHandler('show_items', show_items))
    dp.add_handler(CallbackQueryHandler(show_items_callback, pattern = '^showitems_[0-9]+$'))
    dp.add_handler(MessageHandler(Filters.command, unknown))
    updater.start_polling()
    print('Started polling...')
    updater.idle()

if __name__ == '__main__':
    main()

