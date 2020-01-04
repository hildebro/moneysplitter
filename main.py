import logging

from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, \
    ConversationHandler, PicklePersistence

import privatestorage
from handlers import *


def conv_cancel(update, context):
    update.message.reply_text('The action has been canceled.')
    main_menu_handler.render_checklists(update, context)

    return ConversationHandler.END


def cancel_conversation(update, context):
    main_menu_handler.render_checklists_from_callback(update, context)

    return ConversationHandler.END


def main():
    # noinspection SpellCheckingInspection
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    persistence = PicklePersistence(filename='bot_state_persistence')
    updater = Updater(privatestorage.get_token(), use_context=True, persistence=persistence)
    dp = updater.dispatcher
    # group 0: persist new user or update existing ones
    dp.add_handler(CommandHandler('start', group_0_handler.handle_start_command), group=0)
    dp.add_handler(MessageHandler(Filters.all, group_0_handler.refresh_username), group=0)
    # group 1: actual interactions with the bot
    dp.add_handler(checklist_creation_handler.get_conversation_handler(), group=1)
    dp.add_handler(checklist_removal_handler.get_conversation_handler(), group=1)

    dp.add_handler(item_creation_handler.get_conversation_handler(), group=1)
    dp.add_handler(item_removal_handler.get_conversation_handler(), group=1)

    dp.add_handler(purchase_handler.get_conversation_handler(), group=1)
    dp.add_handler(equalizer_handler.get_conversation_handler(), group=1)

    dp.add_handler(InlineQueryHandler(inline_query_handler.send_invite_message), group=1)
    dp.add_handler(CallbackQueryHandler(inline_query_handler.accept_invite_message, pattern='^join_checklist_[0-9]+$'),
                   group=1)

    dp.add_handler(CallbackQueryHandler(basic_callbacks_handler.show_purchases, pattern='^show_purchases$'), group=1)
    dp.add_handler(CallbackQueryHandler(basic_callbacks_handler.show_items, pattern='^show_items$'), group=1)
    dp.add_handler(CallbackQueryHandler(basic_callbacks_handler.refresh_checklists, pattern='^refresh_checklists$'),
                   group=1)
    dp.add_handler(CallbackQueryHandler(main_menu_handler.render_checklists_from_callback, pattern='^main_menu$'),
                   group=1)
    dp.add_handler(CallbackQueryHandler(main_menu_handler.render_basic_options, pattern='^checklist_[0-9]+$'), group=1)
    dp.add_handler(CallbackQueryHandler(main_menu_handler.render_advanced_options, pattern='^advanced_options$'),
                   group=1)

    dp.add_handler(MessageHandler(Filters.all, main_menu_handler.render_checklists), group=1)

    updater.start_polling()
    print('Started polling...')
    updater.idle()


if __name__ == '__main__':
    main()
