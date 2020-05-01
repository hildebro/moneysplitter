from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from ..db.queries import checklist_queries, item_queries
from ..i18n import trans
from ..services import emojis


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
        keyboard.append([button(f'checklist-menu_{checklist.id}', checklist.name)])
    keyboard.append([button('refresh_checklists', trans.t('checklist.overview.refresh'), emojis.REFRESH)])
    keyboard.append([button('new_checklist', trans.t('checklist.create.link'), emojis.NEW)])

    return InlineKeyboardMarkup(keyboard)


def checklist_menu_text(session, checklist):
    """
    :return: Info text for the given checklist
    """
    checklist_items = item_queries.find_by_checklist(session, checklist.id)
    text = trans.t('checklist.menu.title', name=checklist.name) + '\n\n'
    if len(checklist_items) == 0:
        text += trans.t('checklist.menu.items.none')
    else:
        items = '\n'.join(map(lambda checklist_item: checklist_item.name, checklist_items))
        text += trans.t('checklist.menu.items.some', items=items)
    text += '\n\n' + trans.t('checklist.menu.info')

    return text


def checklist_menu_markup(checklist_id, allow_advanced_options):
    """
    :return: Generic menu options for any checklist
    """
    keyboard = [
        [button(f'new-purchase_{checklist_id}', trans.t('purchase.create.link'), emojis.CART)],
        [button(f'show-purchases_{checklist_id}', trans.t('purchase.log.link'), emojis.BILL)],
        [button('equalize', trans.t('purchase.equalize'), emojis.MONEY)],
    ]
    if allow_advanced_options:
        keyboard.append([button('checklist_settings', trans.t('checklist.settings.link'), emojis.GEAR)])
    keyboard.append([button('checklist_overview', trans.t('checklist.overview.link'), emojis.BACK)])
    return InlineKeyboardMarkup(keyboard)


def checklist_menu(session, from_user, context):
    """
    :return: Tuple of menu text and markup defined above
    """
    checklist = context.user_data['checklist']
    allow_advanced_options = checklist.creator_id == from_user.id

    return checklist_menu_text(session, checklist), checklist_menu_markup(checklist.id, allow_advanced_options)


def back_to_main_menu(checklist_id):
    return InlineKeyboardMarkup(
        [[button(f'checklist-menu_{checklist_id}', trans.t('checklist.menu.link'), emojis.BACK)]]
    )


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
        button(f'abort-{contextual_suffix}_{contextual_id}', trans.t('checklist.menu.link'), emojis.BACK),
        button(f'continue-{contextual_suffix}_{contextual_id}', trans.t('conversation.continue'), emojis.FORWARD)
    ])

    return InlineKeyboardMarkup(keyboard)


def button(callback_data, label, emoji=''):
    """ Simple wrapper around InlineKeyboardButton to slim down frequent usage."""
    return InlineKeyboardButton(emoji + label + emoji, callback_data=callback_data)


CALLBACK_MAPPINGS = {
    'show-purchases': ['checklist_id'],
    'new-purchase': ['checklist_id'],
    'remove-items': ['checklist_id'],
    'remove-users': ['checklist_id'],
    'mark-purchase': ['purchase_id', 'item_id'],
    'mark-remove-items': ['checklist_id', 'item_id'],
    'mark-remove-users': ['checklist_id', 'user_id'],
    'abort-purchase': ['purchase_id'],
    'abort-remove-items': ['checklist_id'],
    'abort-remove-users': ['checklist_id'],
    'continue-purchase': ['purchase_id'],
    'continue-remove-items': ['checklist_id'],
    'continue-remove-users': ['checklist_id'],
    'checklist-menu': ['checklist_id']
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
