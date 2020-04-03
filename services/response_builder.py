from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from queries import checklist_queries, item_queries
from services import emojis

CHECKLIST_OVERVIEW_TEXT = \
    'This is your personal *checklist overview*.\n\nAll checklists that you create or join will be listed here. ' \
    'Click on a checklist button to enter its main menu.\nYou may also create a *new checklist* or *refresh* this ' \
    'overview in order for checklists that you have recently joined to appear.'


def checklist_overview_markup(session, context, user_id):
    """
    :return: Markup containing a button for every checklist available to the given user
    """
    context.user_data.pop('checklist', None)
    context.user_data['all_checklists'] = {}

    keyboard = []
    checklists = checklist_queries.find_by_participant(session, user_id)
    for checklist in checklists:
        context.user_data['all_checklists'][checklist.id] = checklist
        keyboard.append([button('checklist_menu_{}'.format(checklist.id), checklist.name)])
    keyboard.append([button('refresh_checklists', 'Refresh overview', emojis.REFRESH)])
    keyboard.append([button('new_checklist', 'New checklist', emojis.NEW)])

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
    """
    :return: Info text for the given checklist
    """
    checklist_items = item_queries.find_by_checklist(session, checklist.id)
    text = MAIN_MENU_HEADER.format(checklist.name) + '\n\n'
    if len(checklist_items) == 0:
        text += NO_ITEMS
    else:
        text += ITEM_LISTING.format('\n'.join(map(lambda checklist_item: checklist_item.name, checklist_items)))
    text += '\n\n' + MAIN_MENU_INFO

    return text


def checklist_menu_markup(allow_advanced_options):
    """
    :return: Generic menu options for any checklist
    """
    keyboard = [
        [button('new_purchase', 'New purchase', emojis.CART)],
        [button('show_purchases', 'Outstanding purchases', emojis.BILL)],
        [button('equalize', 'Get even', emojis.MONEY)],
    ]
    if allow_advanced_options:
        keyboard.append([button('checklist_settings', 'Danger zone', emojis.WARNING)])
    keyboard.append([button('checklist_overview', 'Back to all checklists', emojis.BACK)])
    return InlineKeyboardMarkup(keyboard)


def checklist_menu(session, from_user, context):
    """
    :return: Tuple of menu text and markup defined above
    """
    checklist = context.user_data['checklist']
    allow_advanced_options = checklist.creator_id == from_user.id

    return checklist_menu_text(session, checklist), checklist_menu_markup(allow_advanced_options)


ADVANCED_CHECKLIST_MENU_TEXT = 'This is the advanced menu for the checklist called *{}*. Please choose an action below.'


def entity_selector_markup(entities):
    """
    :return: Buttons for the given entities with a callback to mark them. Marked entities will be represented as such.
    """
    return


def button(callback_data, label, emoji=''):
    """ Simple wrapper around InlineKeyboardButton to slim down frequent usage."""
    return InlineKeyboardButton(emoji + label + emoji, callback_data=callback_data)
