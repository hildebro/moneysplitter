from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from queries import checklist_queries

MAIN_MENU_TEXT = 'This is the *Main Menu*.\nAll checklists that you are participating in will be listed as buttons. ' \
                 'Click on any of them to see more options.\nYou may also create a *new checklist* or *refresh* the ' \
                 'menu after joining someone else\'s checklist.'
CHECKLIST_MENU_TEXT = 'This is the basic menu for checklist called *{}*. Please choose an action below.'
ADVANCED_CHECKLIST_MENU_TEXT = 'This is the advanced menu for checklist called *{}*. Please choose an action below.'


def render_main_menu(update, context):
    reply_markup = build_main_menu_reply_markup(context, update.message.chat_id)
    update.message.reply_text(MAIN_MENU_TEXT, reply_markup=reply_markup, parse_mode='Markdown')


def render_main_menu_from_callback(update, context, as_new=False):
    reply_markup = build_main_menu_reply_markup(context, update.callback_query.message.chat_id)
    if as_new:
        update.callback_query.message.reply_text(MAIN_MENU_TEXT, reply_markup=reply_markup, parse_mode='Markdown')
        return

    update.callback_query.edit_message_text(text=MAIN_MENU_TEXT, reply_markup=reply_markup, parse_mode='Markdown')


def build_main_menu_reply_markup(context, user_id):
    context.user_data.pop('checklist_id', None)
    context.user_data['checklist_names'] = {}

    keyboard = []
    checklists = checklist_queries.find_by_participant(user_id)
    for checklist in checklists:
        context.user_data['checklist_names'][checklist.id] = checklist.name
        keyboard.append([InlineKeyboardButton(checklist.name, callback_data='checklist_{}'.format(checklist.id))])
    keyboard.append([InlineKeyboardButton('🌟 New checklist 🌟', callback_data='new_checklist')])
    keyboard.append([InlineKeyboardButton('🔄 Refresh 🔄', callback_data='refresh_checklists')])

    return InlineKeyboardMarkup(keyboard)


def render_checklist_menu(update, context):
    checklist_id = int(update.callback_query.data.split('_')[-1])
    context.user_data['checklist_id'] = checklist_id
    keyboard = [[InlineKeyboardButton('Item Menu', callback_data='item_menu')],
                [InlineKeyboardButton('Add items', callback_data='add_items')],
                [InlineKeyboardButton('Start purchase', callback_data='new_purchase')],
                [InlineKeyboardButton('Advanced Options', callback_data='advanced_options')],
                [InlineKeyboardButton('Back to all checklists', callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(
        text=CHECKLIST_MENU_TEXT.format(context.user_data['checklist_names'][checklist_id]),
        reply_markup=reply_markup, parse_mode='Markdown')


def render_advanced_checklist_menu(update, context):
    checklist_id = context.user_data['checklist_id']
    keyboard = [
        [InlineKeyboardButton('Show purchases', callback_data='show_purchases')],
        [InlineKeyboardButton('Equalize', callback_data='equalize')]
    ]
    if checklist_queries.is_creator(checklist_id, update.callback_query.from_user.id):
        keyboard.append([InlineKeyboardButton('Delete checklist', callback_data='delete_checklist')])

    keyboard.append(
        [InlineKeyboardButton('Back to default options', callback_data='checklist_{}'.format(checklist_id))]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(
        text=ADVANCED_CHECKLIST_MENU_TEXT.format(context.user_data['checklist_names'][checklist_id]),
        reply_markup=reply_markup, parse_mode='Markdown')
