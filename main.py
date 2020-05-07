import logging

from telegram.ext import (
    Updater,
    InlineQueryHandler,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler)

import privatestorage
from moneysplitter.handlers import (
    inline_query,
    main_menu, settings, checklist_picker, start, checklist_create, purchase_create, purchase_list,
    new_transactions, checklist_delete, user_kick, item_delete, item_creation, user_refresh,
)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    updater = Updater(privatestorage.get_token(), use_context=True)
    dp = updater.dispatcher

    # refresh username, done on every input via group 0 (should probably also refresh other user info)
    dp.add_handler(MessageHandler(Filters.all, user_refresh.callback), group=0)

    # start
    dp.add_handler(CommandHandler('start', start.callback), group=1)
    # TODO dp.add_handler(CommandHandler('stop', stop.callback), group=1)

    # user invitation
    dp.add_handler(InlineQueryHandler(inline_query.query_callback), group=1)
    dp.add_handler(CallbackQueryHandler(inline_query.answer_callback, pattern='^join_checklist_[0-9]+$'), group=1)

    # ### main menu ###
    # link to menu
    dp.add_handler(CommandHandler('menu', main_menu.message_callback), group=1)
    dp.add_handler(CallbackQueryHandler(main_menu.callback_callback, pattern='^checklist-menu$'), group=1)
    # new purchase
    dp.add_handler(purchase_create.conversation_handler(), group=1)
    # purchase list
    dp.add_handler(CallbackQueryHandler(purchase_list.callback, pattern='^purchase-list$'), group=1)
    # new transactions
    dp.add_handler(CallbackQueryHandler(new_transactions.info_callback, pattern='^new-transactions-info$'), group=1)
    dp.add_handler(CallbackQueryHandler(new_transactions.execute_callback, pattern='^new-transactions-exe$'), group=1)
    # refresh item list
    # TODO dp.add_handler(CallbackQueryHandler(item_refresh.callback, pattern='^items-refresh$'), group=1)

    # ### checklist settings ###
    # link to menu
    dp.add_handler(CallbackQueryHandler(settings.callback, pattern='^checklist-settings$'), group=1)
    # checklist picker
    dp.add_handler(CallbackQueryHandler(checklist_picker.menu_callback, pattern='^checklist-picker$'), group=1)
    dp.add_handler(CallbackQueryHandler(checklist_picker.select_callback, pattern='^select-checklist_[0-9]+$'), group=1)
    # new checklist
    dp.add_handler(checklist_create.conversation_handler(), group=1)
    # delete items
    dp.add_handler(item_delete.conversation_handler(), group=1)
    # kick participants
    dp.add_handler(user_kick.conversation_handler(), group=1)
    # delete checklist
    dp.add_handler(checklist_delete.conversation_handler(), group=1)

    # catch any unsupported commands and deprecated buttons
    # TODO dp.add_handler(CallbackQueryHandler(generic.get_query_handler, pattern='*'), group=1)
    # TODO dp.add_handler(MessageHandler(Filters.command, generic.get_command_handler), group=1)

    # item creation
    dp.add_handler(MessageHandler(Filters.text, item_creation.callback), group=1)

    updater.start_polling()
    print('Started polling...')
    updater.idle()


if __name__ == '__main__':
    main()
