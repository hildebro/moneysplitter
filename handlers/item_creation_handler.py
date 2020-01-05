from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from queries import item_queries


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
