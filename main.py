import logging

from telegram.ext import (
    Updater,
    InlineQueryHandler,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    PicklePersistence)

import privatestorage
from moneysplitter.handlers import (
    inline_query,
    main_menu, settings, checklist_picker, start, checklist_create, new_purchase, purchase_list,
    new_transactions, checklist_delete, user_kick, item_delete, item_creation, user_refresh,
)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    persistence = PicklePersistence(filename='bot_state_persistence')
    updater = Updater(privatestorage.get_token(), use_context=True, persistence=persistence)
    dp = updater.dispatcher

    # refresh username, done on every input via group 0 (should probably also refresh other user info)
    dp.add_handler(MessageHandler(Filters.all, user_refresh.get_handler), group=0)

    # start (and at some point stop)
    dp.add_handler(CommandHandler('start', start.get_handler), group=1)

    # user invitation
    dp.add_handler(InlineQueryHandler(inline_query.get_send_handler), group=1)
    dp.add_handler(CallbackQueryHandler(inline_query.get_join_handler, pattern='^join_checklist_[0-9]+$'), group=1)

    # ### main menu ###
    # link to menu
    dp.add_handler(CommandHandler('menu', main_menu.get_message_handler), group=1)
    dp.add_handler(CallbackQueryHandler(main_menu.get_callback_handler, pattern='^checklist-menu$'), group=1)
    # new purchase
    dp.add_handler(new_purchase.get_handler(), group=1)
    # purchase list
    dp.add_handler(CallbackQueryHandler(purchase_list.get_handler, pattern='^purchase-list$'), group=1)
    # new transactions
    dp.add_handler(CallbackQueryHandler(new_transactions.info_handler, pattern='^new-transactions-info$'), group=1)
    dp.add_handler(CallbackQueryHandler(new_transactions.execute_handler, pattern='^new-transactions-exe$'), group=1)
    # refresh item list
    # TODO dp.add_handler(CallbackQueryHandler(item_refresh.get_handler, pattern='^items-refresh$'), group=1)

    # ### checklist settings ###
    # link to menu
    dp.add_handler(CallbackQueryHandler(settings.get_handler, pattern='^checklist-settings$'), group=1)
    # checklist picker
    dp.add_handler(CallbackQueryHandler(checklist_picker.get_menu_handler, pattern='^checklist-picker$'), group=1)
    dp.add_handler(CallbackQueryHandler(checklist_picker.get_selection_handler, pattern='^select-checklist_[0-9]+$'),
                   group=1)
    # new checklist
    dp.add_handler(checklist_create.get_handler(), group=1)
    # delete items
    dp.add_handler(item_delete.get_handler(), group=1)
    # kick participants
    dp.add_handler(user_kick.get_handler(), group=1)
    # delete checklist
    dp.add_handler(checklist_delete.get_handler(), group=1)

    # catch any unsupported commands and deprecated buttons
    # TODO dp.add_handler(CallbackQueryHandler(generic.get_query_handler, pattern='*'), group=1)
    # TODO dp.add_handler(MessageHandler(Filters.command, generic.get_command_handler), group=1)

    # item creation
    dp.add_handler(MessageHandler(Filters.text, item_creation.get_handler), group=1)

    updater.start_polling()
    print('Started polling...')
    updater.idle()


if __name__ == '__main__':
    main()
