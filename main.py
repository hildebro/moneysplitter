from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters
import dbqueries
import privatestorage

def make_party(update, context):
    party_name = ' '.join(context.args)
    dbqueries.make_party(party_name, update.message.chat_id)
    update.message.reply_text('Party created.')

def add_user(update, context):
    print('empty')

def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text='Unrecognized command.')

def main():
    import logging
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    updater = Updater(privatestorage.get_token(), use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('make_party', make_party))
    dp.add_handler(CommandHandler('add_user', add_user))
    dp.add_handler(MessageHandler(Filters.command, unknown))
    updater.start_polling()
    print('Started polling...')
    updater.idle()

if __name__ == '__main__':
    main()

