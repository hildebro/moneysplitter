from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from queries import checklist_queries, item_queries

CHECKLIST_OVERVIEW_TEXT = \
    'This is your personal *checklist overview*.\n\nAll checklists that you create or join will be listed here. ' \
    'Click on a checklist button to enter its main menu.\nYou may also create a *new checklist* or *refresh* this ' \
    'overview in order for checklists that you have recently joined to appear.'


def checklist_overview_markup(session, context, user_id):
    context.user_data.pop('checklist', None)
    context.user_data['all_checklists'] = {}

    keyboard = []
    checklists = checklist_queries.find_by_participant(session, user_id)
    for checklist in checklists:
        context.user_data['all_checklists'][checklist.id] = checklist
        keyboard.append([InlineKeyboardButton(checklist.name, callback_data='checklist_menu_{}'.format(checklist.id))])
    keyboard.append([InlineKeyboardButton('🔄 Refresh overview 🔄', callback_data='refresh_checklists')])
    keyboard.append([InlineKeyboardButton('🌟 New checklist 🌟', callback_data='new_checklist')])

    return InlineKeyboardMarkup(keyboard)


MAIN_MENU_HEADER = \
    'This is the *main menu* for the checklist called *{}*.'

ITEM_LISTING = \
    'It contains the following items:\n{}'

NO_ITEMS = \
    'It contains no items.'

MAIN_MENU_INFO = \
    'If you want to *add new items*, simply send me a *message* containing the item name.'


def checklist_menu_text(session, checklist):
    checklist_items = item_queries.find_by_checklist(session, checklist.id)
    text = MAIN_MENU_HEADER.format(checklist.name) + '\n\n'
    if len(checklist_items) == 0:
        text += NO_ITEMS
    else:
        text += ITEM_LISTING.format('\n'.join(map(lambda checklist_item: checklist_item.name, checklist_items)))
    text += '\n\n' + MAIN_MENU_INFO

    return text


def checklist_menu_markup(allow_advanced_options):
    keyboard = [
        [InlineKeyboardButton('🌟 Start a new purchase 🌟', callback_data='new_purchase')],
        [InlineKeyboardButton('📋 Show unresolved purchases 📋', callback_data='show_purchases')],
        [InlineKeyboardButton('🧮 Resolve purchases 🧮', callback_data='equalize')],
    ]
    if allow_advanced_options:
        keyboard.append([InlineKeyboardButton('⚙️ Advanced settings ⚙️', callback_data='checklist_settings')])
    keyboard.append([InlineKeyboardButton('🔙 Checklist overview 🔙', callback_data='checklist_overview')])
    return InlineKeyboardMarkup(keyboard)


def checklist_menu(session, from_user, context):
    checklist = context.user_data['checklist']
    allow_advanced_options = checklist.creator_id == from_user.id

    return checklist_menu_text(session, checklist), checklist_menu_markup(allow_advanced_options)


ADVANCED_CHECKLIST_MENU_TEXT = 'This is the advanced menu for the checklist called *{}*. Please choose an action below.'
