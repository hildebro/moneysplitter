from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from queries import checklist_queries


def render_checklists(update, context):
    context.chat_data.pop('checklist_id', None)
    context.chat_data['checklist_names'] = {}
    reply_markup = build_checklist_keyboard_markup(context, update.message.chat_id)
    update.message.reply_text('Choose a checklist to interact with:', reply_markup=reply_markup)


def render_checklists_from_callback(update, context, as_new=False):
    context.chat_data.pop('checklist_id', None)
    context.chat_data['checklist_names'] = {}
    reply_markup = build_checklist_keyboard_markup(context, update.callback_query.message.chat_id)
    if as_new:
        update.callback_query.message.reply_text('Choose a checklist to interact with:', reply_markup=reply_markup)
        return

    update.callback_query.edit_message_text(text='Choose a checklist to interact with:', reply_markup=reply_markup)


def build_checklist_keyboard_markup(context, user_id):
    checklists = checklist_queries.find_by_participant(user_id)
    keyboard = []
    for checklist in checklists:
        context.chat_data['checklist_names'][checklist.id] = checklist.name
        keyboard.append([InlineKeyboardButton(checklist.name, callback_data='checklist_{}'.format(checklist.id))])
    keyboard.append([InlineKeyboardButton('Create new checklist', callback_data='newchecklist')])

    return InlineKeyboardMarkup(keyboard)


def render_basic_options(update, context):
    context.chat_data['checklist_id'] = int(update.callback_query.data.split('_')[1])
    keyboard = [[InlineKeyboardButton('Show items', callback_data='showitems')],
                [InlineKeyboardButton('Add items', callback_data='additems')],
                [InlineKeyboardButton('Start purchase', callback_data='newpurchase')],
                [InlineKeyboardButton('Advanced Options', callback_data='advancedoptions')],
                [InlineKeyboardButton('Back to all checklists', callback_data='mainmenu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text='Choose an action:', reply_markup=reply_markup)


def render_advanced_options(update, context):
    checklist_id = context.chat_data['checklist_id']
    keyboard = [[InlineKeyboardButton('Show purchases', callback_data='showpurchases')],
                [InlineKeyboardButton('Equalize', callback_data='equalize')],
                [InlineKeyboardButton('Remove items', callback_data='removeitems')]]
    if checklist_queries.is_creator(checklist_id, update.callback_query.from_user.id):
        keyboard.append([InlineKeyboardButton('Delete checklist', callback_data='deletechecklist')])

    keyboard.append(
        [InlineKeyboardButton('Back to default options', callback_data='checklist_{}'.format(checklist_id))]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text='Choose an action:', reply_markup=reply_markup)
