from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from queries import checklist_queries

CHECKLIST_OVERVIEW_TEXT = \
    'This is your personal *checklist overview*.\n\nAll checklists that you create or join will be listed here. ' \
    'Click on a checklist button to enter its main menu.\nYou may also create a *new checklist* or *refresh* this ' \
    'overview in order for checklists that you have recently joined to appear.'
CHECKLIST_MENU_TEXT = \
    'This is the *main menu* for the checklist called *{}*.\n\nIf you want to interact with this ' \
    'checklist, please enter one of the submenus. Otherwise, return to the checklist overview'
ADVANCED_CHECKLIST_MENU_TEXT = 'This is the advanced menu for the checklist called *{}*. Please choose an action below.'


def render_main_menu(update, context):
    reply_markup = build_main_menu_reply_markup(context, update.message.chat_id)
    update.message.reply_text(CHECKLIST_OVERVIEW_TEXT, reply_markup=reply_markup, parse_mode='Markdown')


def render_main_menu_from_callback(update, context, as_new=False):
    reply_markup = build_main_menu_reply_markup(context, update.callback_query.message.chat_id)
    if as_new:
        update.callback_query.message.reply_text(CHECKLIST_OVERVIEW_TEXT, reply_markup=reply_markup,
                                                 parse_mode='Markdown')
        return

    update.callback_query.edit_message_text(text=CHECKLIST_OVERVIEW_TEXT, reply_markup=reply_markup,
                                            parse_mode='Markdown')


def build_main_menu_reply_markup(context, user_id):
    context.user_data.pop('checklist', None)
    context.user_data['all_checklists'] = {}

    keyboard = []
    checklists = checklist_queries.find_by_participant(user_id)
    for checklist in checklists:
        context.user_data['all_checklists'][checklist.id] = checklist
        keyboard.append([InlineKeyboardButton(checklist.name, callback_data='checklist_menu_{}'.format(checklist.id))])
    keyboard.append([InlineKeyboardButton('🌟 New checklist 🌟', callback_data='new_checklist')])
    keyboard.append([InlineKeyboardButton('🔄 Refresh 🔄', callback_data='refresh_checklists')])

    return InlineKeyboardMarkup(keyboard)


def render_checklist_menu(update, context):
    checklist_id = int(update.callback_query.data.split('_')[-1])
    context.user_data['checklist'] = context.user_data['all_checklists'][checklist_id]
    keyboard = [[InlineKeyboardButton('Item Menu', callback_data='item_menu')],
                [InlineKeyboardButton('Purchase Menu', callback_data='purchase_menu')],
                [InlineKeyboardButton('Advanced Options', callback_data='advanced_options')],
                [InlineKeyboardButton('Back to checklist overview', callback_data='checklist_overview')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(
        text=CHECKLIST_MENU_TEXT.format(context.user_data['checklist'].name),
        reply_markup=reply_markup, parse_mode='Markdown')


def render_advanced_checklist_menu(update, context):
    checklist_id = context.user_data['checklist'].id
    keyboard = [
        [InlineKeyboardButton('Show purchases', callback_data='show_purchases')],
        [InlineKeyboardButton('Equalize', callback_data='equalize')]
    ]
    if checklist_queries.is_creator(checklist_id, update.callback_query.from_user.id):
        keyboard.append([InlineKeyboardButton('Delete checklist', callback_data='delete_checklist')])

    keyboard.append(
        [InlineKeyboardButton('Back to default options', callback_data='checklist_menu_{}'.format(checklist_id))]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(
        text=ADVANCED_CHECKLIST_MENU_TEXT.format(context.user_data['checklist'].name),
        reply_markup=reply_markup, parse_mode='Markdown')
