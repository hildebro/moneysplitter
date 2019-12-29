import logging

from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, \
    ConversationHandler

import privatestorage
import queries.checklist_queries as checklist_queries
import queries.item_queries as item_queries
from handlers import purchase_handler, equalizer_handler, group_0_handler
from handlers.main_menu_handler import render_checklists, render_checklists_from_callback, render_basic_options, \
    render_advanced_options
from queries import purchase_queries

NEWCHECKLIST_NAME = 0
ADDUSER_NAME = 0
ADDITEMS_NAME = 0
REMOVEITEMS_NAME = 0
DELETECHECKLIST_CONFIRM = 0


def conv_delete_checklist_init(update, context):
    update.callback_query.edit_message_text(text='You are about to delete the selected checklist. If you really '
                                                 'want to do this, type /delete. Otherwise, type /cancel.')

    return DELETECHECKLIST_CONFIRM


def conv_delete_checklist_execute(update, context):
    checklist_id = context.chat_data['checklist_id']
    checklist_queries.delete(checklist_id, update.message.chat_id)
    update.message.reply_text('Checklist deleted.')

    render_checklists(update, context)

    return ConversationHandler.END


def conv_cancel(update, context):
    update.message.reply_text('The action has been canceled.')
    render_checklists(update, context)

    return ConversationHandler.END


def conv_new_checklist_init(update, context):
    update.callback_query.edit_message_text(text='What name should the new checklist have?')

    return NEWCHECKLIST_NAME


def conv_new_checklist_check(update, context):
    checklist_name = update.message.text
    user_id = update.message.from_user.id

    if checklist_queries.exists(user_id, checklist_name):
        update.message.reply_text('You already have a checklist with that name. Please provide a new name or stop the '
                                  'process with /cancel.')

        return NEWCHECKLIST_NAME

    checklist_queries.create(user_id, checklist_name)
    update.message.reply_text('Checklist created.')
    render_checklists(update, context)

    return ConversationHandler.END


def conv_add_items_init(update, context):
    checklist_name = context.chat_data['checklist_names'][context.chat_data['checklist_id']]
    update.callback_query.edit_message_text(text='Send me item names (one at a time) to add them to {}. Use /finish '
                                                 'when you are done.'.format(checklist_name))

    return ADDITEMS_NAME


def conv_add_items_check(update, context):
    item_name = update.message.text
    checklist_id = context.chat_data['checklist_id']
    item_queries.create(item_name, checklist_id)
    update.message.reply_text(
        '{} added to {}. Provide more items or stop the action with /finish.'.format(
            item_name, context.chat_data['checklist_names'][checklist_id]
        )
    )

    return ADDITEMS_NAME


def conv_add_items_finish(update, context):
    update.message.reply_text('Finished adding items.')
    render_checklists(update, context)

    return ConversationHandler.END


def conv_remove_items_init(update, context):
    render_items_to_remove(update, context)

    return REMOVEITEMS_NAME


def conv_remove_items_check(update, context):
    query = update.callback_query
    item_id = query.data.split('_')[1]
    item_queries.remove(item_id)
    render_items_to_remove(update, context)

    return REMOVEITEMS_NAME


def conv_remove_items_finish(update, context):
    update.callback_query.edit_message_text(text='Finished removing items.')
    render_checklists_from_callback(update, context)

    return ConversationHandler.END


def render_items_to_remove(update, context):
    items = item_queries.find_by_checklist(context.chat_data['checklist_id'])
    keyboard = []
    for item in items:
        keyboard.append([InlineKeyboardButton(item.name, callback_data='ri_{}'.format(item.id))])

    # todo either buffer table like with purchases or use chat data for buffer
    # keyboard.append([
    #    InlineKeyboardButton('Revert', callback_data='ri'),
    #    InlineKeyboardButton('Abort', callback_data='ap')
    # ])
    keyboard.append([
        InlineKeyboardButton('Finish', callback_data='finish')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text='Choose items to remove from the list:', reply_markup=reply_markup)


def show_items(update, context):
    query = update.callback_query
    checklist_id = context.chat_data['checklist_id']
    checklist_name = context.chat_data['checklist_names'][checklist_id]
    checklist_items = item_queries.find_by_checklist(checklist_id)
    if len(checklist_items) == 0:
        query.edit_message_text(text=checklist_name + ' has no items.')
    else:
        query.edit_message_text(
            text='{} contains the following items:\n{}'.format(checklist_name, '\n'.join(
                map(lambda checklist_item: checklist_item.name, checklist_items)))
        )

    render_checklists_from_callback(update, context, True)


def show_purchases(update, context):
    query = update.callback_query
    checklist_id = context.chat_data['checklist_id']
    checklist_name = context.chat_data['checklist_names'][checklist_id]
    purchases = purchase_queries.find_by_checklist(checklist_id)
    if len(purchases) == 0:
        text = checklist_name + ' has no purchases.'
    else:
        text = ''
        for purchase in purchases:
            text += '{} has paid {} for the following items:\n'.format(purchase.buyer.username,
                                                                       purchase.get_price()) + '\n'.join(
                map(lambda item: item.name, purchase.items)) + '\n'

    query.edit_message_text(text=text)
    render_checklists_from_callback(update, context, True)


def inline_query_send_invite(update, context):
    query = update.inline_query.query

    inline_options = []
    for checklist in checklist_queries.find_by_creator(update.inline_query.from_user['id']):
        if query and not checklist.name.lower().startswith(query.lower()):
            continue

        inline_options.append(
            InlineQueryResultArticle(
                id=checklist.id,
                title=checklist.name,
                input_message_content=InputTextMessageContent(
                    'You are invited to join the checklist {}. Press the button under this message to confirm. If you '
                    'don\'t know what this means, check out @PurchaseSplitterBot for more info.'.format(checklist.name)
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('Join checklist', callback_data='joinchecklist_{}'.format(checklist.id))
                ]])
            )
        )
    context.bot.answer_inline_query(update.inline_query.id, inline_options)


def join_checklist(update, context):
    checklist_id = update.callback_query.data.split('_')[1]
    user_id = update.callback_query.from_user.id
    checklist_queries.join(checklist_id, user_id)
    update.callback_query.answer('Successfully joined checklist!')


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    updater = Updater(privatestorage.get_token(), use_context=True)
    dp = updater.dispatcher
    # group 0: persist new user or update existing ones
    dp.add_handler(CommandHandler('start', group_0_handler.handle_start_command), group=0)
    dp.add_handler(MessageHandler(Filters.all, group_0_handler.refresh_username), group=0)
    # group 1: actual interactions with the bot
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(conv_new_checklist_init, pattern='^newchecklist$')],
            states={
                NEWCHECKLIST_NAME: [MessageHandler(Filters.text, conv_new_checklist_check)],
            },
            fallbacks=[CommandHandler('cancel', conv_cancel)]
        ),
        group=1
    )
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(conv_add_items_init, pattern='^additems$')],
            states={
                ADDITEMS_NAME: [
                    CommandHandler('finish', conv_add_items_finish),
                    MessageHandler(Filters.text, conv_add_items_check)
                ]
            },
            fallbacks=[CommandHandler('cancel', conv_cancel)]
        ),
        group=1
    )
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(conv_remove_items_init, pattern='^removeitems$')],
            states={
                REMOVEITEMS_NAME: [
                    CallbackQueryHandler(conv_remove_items_check, pattern='^ri_.+'),
                    CallbackQueryHandler(conv_remove_items_finish, pattern='^finish$')
                ]
            },
            fallbacks=[CommandHandler('cancel', conv_cancel)]
        ),
        group=1
    )
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(purchase_handler.initialize, pattern='^newpurchase$')],
            states={
                purchase_handler.ITEM_STATE: [
                    CallbackQueryHandler(purchase_handler.buffer_item, pattern='^bi_.+'),
                    CallbackQueryHandler(purchase_handler.revert_item, pattern='^ri$'),
                    CallbackQueryHandler(purchase_handler.finish, pattern='^fp$'),
                    CallbackQueryHandler(purchase_handler.abort, pattern='^ap$')
                ],
                purchase_handler.PRICE_STATE: [MessageHandler(Filters.text, purchase_handler.set_price)]
            },
            fallbacks=[CommandHandler('cancel', conv_cancel)]
        ),
        group=1
    )
    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(equalizer_handler.initialize, pattern='^equalize$')],
            states={
                equalizer_handler.PURCHASE_STATE: [
                    CallbackQueryHandler(equalizer_handler.buffer_purchase, pattern='^bp_.+'),
                    CallbackQueryHandler(equalizer_handler.revert_purchase, pattern='^rp$'),
                    CallbackQueryHandler(equalizer_handler.finish, pattern='^fe$'),
                    CallbackQueryHandler(equalizer_handler.abort, pattern='^ae$')
                ]
            },
            fallbacks=[CommandHandler('cancel', conv_cancel)]
        ),
        group=1
    )

    dp.add_handler(
        ConversationHandler(
            entry_points=[CallbackQueryHandler(conv_delete_checklist_init, pattern='^deletechecklist$')],
            states={
                DELETECHECKLIST_CONFIRM: [
                    CommandHandler('delete', conv_delete_checklist_execute)
                ],
            },
            fallbacks=[CommandHandler('cancel', conv_cancel)]
        ),
        group=1
    )

    dp.add_handler(InlineQueryHandler(inline_query_send_invite), group=1)

    dp.add_handler(CallbackQueryHandler(render_checklists_from_callback, pattern='^mainmenu$'), group=1)
    dp.add_handler(CallbackQueryHandler(show_purchases, pattern='^showpurchases$'), group=1)
    dp.add_handler(CallbackQueryHandler(show_items, pattern='^showitems$'), group=1)
    dp.add_handler(CallbackQueryHandler(render_basic_options, pattern='^checklist_[0-9]+$'), group=1)
    dp.add_handler(CallbackQueryHandler(render_advanced_options, pattern='^advancedoptions$'), group=1)
    dp.add_handler(CallbackQueryHandler(join_checklist, pattern='^joinchecklist_[0-9]+$'), group=1)

    dp.add_handler(MessageHandler(Filters.all, render_checklists), group=1)

    updater.start_polling()
    print('Started polling...')
    updater.idle()


if __name__ == '__main__':
    main()
