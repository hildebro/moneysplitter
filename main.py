import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters, InlineQueryHandler
import dbqueries
import privatestorage

def start(update, context):
    dbqueries.register_user(update.message.chat)
    update.message.reply_text('You are now registered.')

def refresh_username(update, context):
    dbqueries.refresh_username(update.message.chat)
    update.message.reply_text('Username refreshed.')

def make_party(update, context):
    args = context.args
    if len(args) == 0:
        update.message.reply_text('Please provide a name for the party.')
        return
    if len(args) > 1:
        update.message.reply_text('No whitespaces allowed in party names.')
        return

    party_name = args[0]
    user_id = update.message.chat_id

    dbqueries.make_party(party_name, user_id)
    update.message.reply_text('Party created.')

def party_add(update, context):
    args = context.args
    if len(args) != 2:
        update.message.reply_text('Bad syntax. /party_add {party_name} {username}')
        return

    group_id = dbqueries.find_party_id(update.message.chat_id, args[0])
    if group_id is None:
        update.message.reply_text('Party name not found. Check available parties with /show_parties.')
        return

    user = dbqueries.find_user(args[1])
    if user is None:
        update.message.reply_text('Username not found. Make sure they initiated the bot with /start. If they changed their username since starting the bot, they have to execute /refresh_username.')
        return

    dbqueries.party_add(group_id, user['id'])
    update.message.reply_text('User added.')

def show_parties(update, context):
    parties = dbqueries.find_parties(update.message.chat_id)
    if len(parties) == 0:
        update.message.reply_text("You don't have any parties yet.")
        return

    update.message.reply_text('Your parties:\n' + '\n'.join(parties))

def inline_handling(update, context):
    query = update.inline_query.query
    if not query:
        return
    results = list()
    results.append(
        InlineQueryResultArticle(
            id=query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    context.bot.answer_inline_query(update.inline_query.id, results)

def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text='Unrecognized command.')

def main():
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    updater = Updater(privatestorage.get_token(), use_context=True)
    dp = updater.dispatcher
    dp.add_handler(InlineQueryHandler(inline_handling))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('refresh_username', refresh_username))
    dp.add_handler(CommandHandler('make_party', make_party))
    dp.add_handler(CommandHandler('party_add', party_add))
    dp.add_handler(CommandHandler('show_parties', show_parties))
    dp.add_handler(MessageHandler(Filters.command, unknown))
    updater.start_polling()
    print('Started polling...')
    updater.idle()

if __name__ == '__main__':
    main()

