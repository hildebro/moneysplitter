from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, ConversationHandler, CommandHandler

from main import conv_cancel
from queries import item_queries

ITEM_MENU_MESSAGE = \
    '*{}* contains the following items:\n{}\n\nIf you want to add new items, simply send me a message with a single ' \
    'item name. You may do this in any menu of this checklist. '

ITEM_REMOVAL_MESSAGE = \
    'You are now removing items from checklist *{}*.\n\nClick on items to *(de)select* them for ' \
    'removal.\nWhen you are done, click *Commit* to remove all selected items.\nClick *Abort* to exit ' \
    'without removals. '


def render_item_menu(update, context):
    checklist = context.user_data['checklist']
    checklist_name = checklist.name
    checklist_items = item_queries.find_by_checklist(checklist.id)
    if len(checklist_items) == 0:
        text = checklist_name + ' has no items.'
    else:
        text = ITEM_MENU_MESSAGE.format(checklist_name,
                                        '\n'.join(map(lambda checklist_item: checklist_item.name, checklist_items)))

    keyboard = [
        [InlineKeyboardButton('Remove items', callback_data='remove_items')],
        [InlineKeyboardButton('Back to main menu', callback_data='checklist_menu_{}'.format(checklist.id))]
    ]

    update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard),
                                            parse_mode='Markdown')


def add_item(update, context):
    if 'checklist' not in context.user_data:
        update.message.reply_text(
            'Sorry, I cannot handle messages while you are browsing the checklist overview.\nIf you were trying to '
            'add items to one of your checklists, you have to enter that checklist\'s main menu first.',
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('Back to checklist overview', callback_data='checklist_overview')]]
            )
        )
        return

    item_name = update.message.text
    checklist = context.user_data['checklist']
    item = item_queries.create(item_name, checklist.id)
    keyboard = [
        [
            InlineKeyboardButton('Undo last item', callback_data='undo_{}'.format(item.id)),
            InlineKeyboardButton('Back to main menu', callback_data='checklist_menu_{}'.format(checklist.id))
        ]
    ]
    update.message.reply_text(
        'New item *{}* has been added to checklist *{}*. You may add more items or return to the main menu'.format(
            item_name, checklist.name),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


def undo_item(update, context):
    item_id = update.callback_query.data.split('_')[-1]
    item_queries.remove(item_id)
    checklist = context.user_data['checklist']
    keyboard = [
        [
            InlineKeyboardButton('Back to main menu', callback_data='checklist_menu_{}'.format(checklist.id))
        ]
    ]
    update.callback_query.edit_message_text(
        text='The item creation has been undone.',
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )


BASE_STATE = 0


def get_removal_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^remove_items$')],
        states={
            BASE_STATE: [
                CallbackQueryHandler(mark_item, pattern='^mark_.+'),
                CallbackQueryHandler(abort, pattern='^abort$'),
                CallbackQueryHandler(commit, pattern='^commit$')
            ]
        },
        fallbacks=[CommandHandler('cancel', conv_cancel)]
    )


def initialize(update, context):
    context.user_data['removal_dict'] = {}
    items = item_queries.find_by_checklist(context.user_data['checklist'].id)
    for item in items:
        context.user_data['removal_dict'][item.id] = item.name

    render_removal_buttons(update, context)

    return BASE_STATE


def mark_item(update, context):
    query = update.callback_query
    item_id = int(query.data.split('_')[-1])
    item_name = context.user_data['removal_dict'][item_id]
    if '🚫' in item_name:
        item_name = item_name.replace('🚫', '')
    else:
        item_name = '🚫' + item_name + '🚫'

    context.user_data['removal_dict'][item_id] = item_name
    render_removal_buttons(update, context)

    return BASE_STATE


def abort(update, context):
    context.user_data['removal_dict'] = None
    render_item_menu(update, context)

    return ConversationHandler.END


def commit(update, context):
    ids_to_remove = []
    removal_dict = context.user_data['removal_dict']
    for item_id in removal_dict:
        if '🚫' in removal_dict[item_id]:
            ids_to_remove.append(item_id)

    item_queries.remove_all(ids_to_remove)
    render_item_menu(update, context)

    return ConversationHandler.END


def render_removal_buttons(update, context):
    keyboard = []
    removal_dict = context.user_data['removal_dict']
    for item_id in removal_dict:
        keyboard.append([InlineKeyboardButton(removal_dict[item_id], callback_data='mark_{}'.format(item_id))])

    keyboard.append([
        InlineKeyboardButton('Abort', callback_data='abort'),
        InlineKeyboardButton('Commit', callback_data='commit')
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text=ITEM_REMOVAL_MESSAGE.format(context.user_data['checklist'].name),
                                            reply_markup=reply_markup, parse_mode='Markdown')
