from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..i18n import trans
from ..services import emojis


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
            [button(f'mark-{contextual_suffix}_{contextual_id}_{entity.identifier()}',
                    f'{button_prefix} {entity.display_name()}')])
    keyboard.append([
        button(f'abort-{contextual_suffix}_{contextual_id}', trans.t('conversation.cancel'), emojis.BACK),
        button(f'continue-{contextual_suffix}_{contextual_id}', trans.t('conversation.continue'), emojis.FORWARD)
    ])

    return InlineKeyboardMarkup(keyboard)


def button(callback_data, label, emoji=''):
    """ Simple wrapper around InlineKeyboardButton to slim down frequent usage."""
    return InlineKeyboardButton(emoji + label + emoji, callback_data=callback_data)


CALLBACK_MAPPINGS = {
    # i don't want these remove-mark-abort-continue chains, but that's a whole can of worms...
    'remove-items': ['checklist_id'],
    'remove-users': ['checklist_id'],
    'mark-remove-items': ['checklist_id', 'item_id'],
    'mark-remove-users': ['checklist_id', 'user_id'],
    'abort-remove-items': ['checklist_id'],
    'abort-remove-users': ['checklist_id'],
    'continue-remove-items': ['checklist_id'],
    'continue-remove-users': ['checklist_id'],
    # these are actually required after overhaul
    'select-checklist': ['checklist_id'],
    'mark-purchase': ['purchase_id', 'item_id'],
    'abort-purchase': ['purchase_id'],
    'continue-purchase': ['purchase_id'],
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
