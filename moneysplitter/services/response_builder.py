from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..db.queries import checklist_queries, item_queries
from ..services import emojis

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


def checklist_menu_markup(checklist_id, allow_advanced_options):
    """
    :return: Generic menu options for any checklist
    """
    keyboard = [
        [button(f'new-purchase_{checklist_id}', 'New purchase', emojis.CART)],
        [button(f'show-purchases_{checklist_id}', 'Outstanding purchases', emojis.BILL)],
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

    return checklist_menu_text(session, checklist), checklist_menu_markup(checklist.id, allow_advanced_options)


def back_to_main_menu(checklist_id):
    return InlineKeyboardMarkup([[button(f'checklist_menu_{checklist_id}', 'Main menu', emojis.BACK)]])


ADVANCED_CHECKLIST_MENU_TEXT = 'This is the advanced menu for the checklist called *{}*. Please choose an action below.'


def entity_selector_markup(entities, is_marked_callback, contextual_id, contextual_suffix):
    """
    :param entities: For each of these a button will be created.
    :param is_marked_callback: Used to check, whether an entity is already selected.
    :param contextual_id: The ID of the defined context.
    :param contextual_suffix: Used to define the context in which the selection of entities occurs.
    :return: Buttons to be marked as selected, when clicked.
    """
    keyboard = []
    for entity in entities:
        button_prefix = '(O)' if is_marked_callback(entity) else '(  )'
        keyboard.append(
            [button(f'mark-{contextual_suffix}_{contextual_id}_{entity.id}', f'{button_prefix} {entity.name}')])
    keyboard.append([
        button(f'abort-{contextual_suffix}_{contextual_id}', 'Main menu', emojis.BACK),
        button(f'continue-{contextual_suffix}_{contextual_id}', 'Continue', emojis.FORWARD)
    ])

    return InlineKeyboardMarkup(keyboard)


def button(callback_data, label, emoji=''):
    """ Simple wrapper around InlineKeyboardButton to slim down frequent usage."""
    return InlineKeyboardButton(emoji + label + emoji, callback_data=callback_data)


CALLBACK_MAPPINGS = {
    'show-purchases': ['checklist_id'],
    'new-purchase': ['checklist_id'],
    'mark-for-purchase': ['purchase_id', 'item_id'],
    'abort-for-purchase': ['purchase_id'],
    'continue-for-purchase': ['purchase_id']
}


def interpret_data(callback_query):
    """
    Every callback data has the format of PURPOSE_ID_ID_ID_ID_ID...
    In order to properly interpret the data, the purpose is used as a key for CALLBACK_MAPPINGS.
    The callback IDs are then mapped to the defined names.
    """
    data = callback_query.data.split('_')
    mapping = CALLBACK_MAPPINGS[data.pop(0)]
    result_data = {}
    for i in range(len(mapping)):
        result_data[mapping[i]] = int(data[i])

    return result_data
