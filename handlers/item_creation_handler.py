from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from handlers.main_menu_handler import render_main_menu
from queries import item_queries


def add_item(update, context):
    if context.user_data['checklist'] is None:
        update.message.reply_text(
            'Sorry, I cannot handle messages while you are browsing the checklist overview.\nIf you were trying to '
            'add items to one of your checklists, you have to enter that checklist\'s main menu first.')
        render_main_menu(update, context)
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
