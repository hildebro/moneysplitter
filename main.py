import logging

from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, \
    PicklePersistence

print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__, __name__, str(__package__)))
import privatestorage
from moneysplitter.handlers import (
    checklist_handler,
    equalizer_handler,
    group_0_handler,
    inline_query_handler,
    item_handler,
    menu_handler,
    purchase_handler,
    user_handler
)


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
    dp.add_handler(CommandHandler('overview', menu_handler.checklist_overview_command), group=1)

    dp.add_handler(checklist_handler.get_creation_handler(), group=1)
    dp.add_handler(checklist_handler.get_removal_handler(), group=1)
    dp.add_handler(
        CallbackQueryHandler(menu_handler.refresh_checklists, pattern='^refresh_checklists$'), group=1
    )

    dp.add_handler(
        CallbackQueryHandler(menu_handler.checklist_overview_callback, pattern='^checklist_overview$'),
        group=1
    )
    dp.add_handler(
        CallbackQueryHandler(menu_handler.checklist_menu_callback, pattern='^checklist_menu_[0-9]+$'), group=1
    )
    dp.add_handler(
        CallbackQueryHandler(menu_handler.advanced_settings_callback, pattern='^checklist_settings$'), group=1
    )

    dp.add_handler(InlineQueryHandler(inline_query_handler.send_invite_message), group=1)
    dp.add_handler(
        CallbackQueryHandler(inline_query_handler.accept_invite_message, pattern='^join_checklist_[0-9]+$'), group=1
    )
    dp.add_handler(user_handler.get_removal_handler(), group=1)

    dp.add_handler(CallbackQueryHandler(purchase_handler.show_purchases, pattern='^show_purchases$'), group=1)
    dp.add_handler(purchase_handler.get_conversation_handler(), group=1)

    dp.add_handler(equalizer_handler.get_conversation_handler(), group=1)

    dp.add_handler(CallbackQueryHandler(item_handler.undo_last_items, pattern='^undo_last_items'), group=1)
    dp.add_handler(item_handler.get_removal_handler(), group=1)
    dp.add_handler(MessageHandler(Filters.text, item_handler.add_item), group=1)

    updater.start_polling()
    print('Started polling...')
    updater.idle()


if __name__ == '__main__':
    main()
