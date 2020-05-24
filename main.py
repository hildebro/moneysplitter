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
    transaction_create, checklist_delete, participant_delete, item_delete, item_creation, user_refresh, item_refresh,
    fallback, transaction_list, transaction_payoff, instructions
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
    dp.add_handler(CallbackQueryHandler(transaction_create.info_callback, pattern='^transaction.create.info$'), group=1)
    dp.add_handler(CallbackQueryHandler(transaction_create.execute_callback, pattern='^transaction.create.execute$'),
                   group=1)
    # transaction list
    dp.add_handler(CallbackQueryHandler(transaction_list.callback, pattern='^transaction.list$'), group=1)
    # transaction pay-off
    dp.add_handler(transaction_payoff.conversation_handler(), group=1)
    # refresh item list
    dp.add_handler(CallbackQueryHandler(item_refresh.callback, pattern='^item-refresh$'), group=1)

    # ### instructions ###
    # link to instructions
    dp.add_handler(CallbackQueryHandler(instructions.callback, pattern='^instructions$'), group=1)
    # instruction topics
    dp.add_handler(CallbackQueryHandler(instructions.checklist, pattern='^instructions.checklist$'), group=1)
    dp.add_handler(CallbackQueryHandler(instructions.item, pattern='^instructions.item$'), group=1)
    dp.add_handler(CallbackQueryHandler(instructions.purchase, pattern='^instructions.purchase$'), group=1)
    dp.add_handler(CallbackQueryHandler(instructions.write_off, pattern='^instructions.write_off$'), group=1)
    dp.add_handler(CallbackQueryHandler(instructions.balance, pattern='^instructions.balance$'), group=1)

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
    dp.add_handler(participant_delete.conversation_handler(), group=1)
    # delete checklist
    dp.add_handler(checklist_delete.conversation_handler(), group=1)

    # catch any unsupported commands and deprecated buttons
    dp.add_handler(CallbackQueryHandler(fallback.button_callback, pattern='.*'), group=1)
    dp.add_handler(MessageHandler(Filters.command, fallback.command_callback), group=1)

    # item creation
    dp.add_handler(MessageHandler(Filters.text, item_creation.callback), group=1)

    updater.start_polling()
    print('Started polling...')
    updater.idle()


if __name__ == '__main__':
    main()
