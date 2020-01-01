from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from queries import checklist_queries


def render_checklists(update, context):
    context.user_data.pop('checklist_id', None)
    context.user_data['checklist_names'] = {}
    reply_markup = build_checklist_keyboard_markup(context, update.message.chat_id)
    update.message.reply_text(
        'This is the *Main Menu*.\n'
        'All checklists that you are participating in will be listed as buttons. Click on any of them to see more '
        'options.\n'
        'You may also create a *new checklist* or *refresh* the buttons to see other people\'s checklist after joining.',
        reply_markup=reply_markup, parse_mode='Markdown')


def render_checklists_from_callback(update, context, as_new=False):
    context.user_data.pop('checklist_id', None)
    context.user_data['checklist_names'] = {}
    message_text = \
        'This is the *Main Menu*. All checklists that you are participating in will be listed as buttons. Click on ' \
        'any of them to see more options.\nYou may also create a *new checklist* or *refresh* the buttons to see ' \
        'other people\'s checklist after joining.',
    reply_markup = build_checklist_keyboard_markup(context, update.callback_query.message.chat_id)
    if as_new:
        update.callback_query.message.reply_text(message_text, reply_markup=reply_markup, parse_mode='Markdown')
        return

    update.callback_query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')


def build_checklist_keyboard_markup(context, user_id):
    checklists = checklist_queries.find_by_participant(user_id)
    keyboard = []
    for checklist in checklists:
        context.user_data['checklist_names'][checklist.id] = checklist.name
        keyboard.append([InlineKeyboardButton(checklist.name, callback_data='checklist_{}'.format(checklist.id))])
    keyboard.append([InlineKeyboardButton('New checklist...', callback_data='new_checklist')])
    keyboard.append([InlineKeyboardButton('Refresh', callback_data='refresh_checklists')])

    return InlineKeyboardMarkup(keyboard)


def render_basic_options(update, context):
    context.user_data['checklist_id'] = int(update.callback_query.data.split('_')[1])
    keyboard = [[InlineKeyboardButton('Show items', callback_data='show_items')],
                [InlineKeyboardButton('Add items', callback_data='add_items')],
                [InlineKeyboardButton('Start purchase', callback_data='new_purchase')],
                [InlineKeyboardButton('Advanced Options', callback_data='advanced_options')],
                [InlineKeyboardButton('Back to all checklists', callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text='Choose an action:', reply_markup=reply_markup)


def render_advanced_options(update, context):
    checklist_id = context.user_data['checklist_id']
    keyboard = [[InlineKeyboardButton('Show purchases', callback_data='show_purchases')],
                [InlineKeyboardButton('Equalize', callback_data='equalize')],
                [InlineKeyboardButton('Remove items', callback_data='remove_items')]]
    if checklist_queries.is_creator(checklist_id, update.callback_query.from_user.id):
        keyboard.append([InlineKeyboardButton('Delete checklist', callback_data='delete_checklist')])

    keyboard.append(
        [InlineKeyboardButton('Back to default options', callback_data='checklist_{}'.format(checklist_id))]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text='Choose an action:', reply_markup=reply_markup)
