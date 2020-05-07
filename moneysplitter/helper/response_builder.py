from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler

from .function_wrappers import button, edit
from ..db import session_wrapper
from ..handlers import main_menu
from ..helper import emojis
from ..i18n import trans


def entry_pattern(action_identifier):
    return f'^{action_identifier}$'


def select_pattern(action_identifier):
    return f'^{action_identifier}-select_[0-9]+$'


def continue_pattern(action_identifier):
    return f'^{action_identifier}-continue$'


def abort_pattern(action_identifier):
    return f'^{action_identifier}-abort$'


def entry_handler(action_identifier, get_text_func, get_entities_func, is_selected_func, initial_func=None):
    @session_wrapper
    def entry_callback(session, update, context):
        query = update.callback_query
        user_id = query.from_user.id

        if initial_func is not None:
            initial_func(session, user_id)

        text = get_text_func(session, user_id)
        markup = entity_select_markup(action_identifier, get_entities_func(session, user_id), is_selected_func)
        edit(query, text, markup)
        return 0

    return CallbackQueryHandler(entry_callback, pattern=entry_pattern(action_identifier))


def select_handler(action_identifier, get_text_func, get_entities_func, is_selected_func, select_entity_func):
    @session_wrapper
    def select_callback(session, update, context):
        query = update.callback_query
        user_id = query.from_user.id

        select_entity_func(session, user_id, get_item_id(query))

        text = get_text_func(session, user_id)
        markup = entity_select_markup(action_identifier, get_entities_func(session, user_id), is_selected_func)
        edit(query, text, markup)
        return 0

    return CallbackQueryHandler(select_callback, pattern=select_pattern(action_identifier))


def abort_handler(action_identifier, abort_func):
    @session_wrapper
    def abort_callback(session, update, context):
        query = update.callback_query

        abort_func(session, query.from_user.id)

        text = trans.t('conversation.canceled')
        markup = InlineKeyboardMarkup([[main_menu.link_button()]])
        edit(query, text, markup)
        return ConversationHandler.END

    return CallbackQueryHandler(abort_callback, pattern=abort_pattern(action_identifier))


def entity_select_markup(action_identifier, entities, entity_select_callback):
    keyboard = []
    for entity in entities:
        button_prefix = '(O)' if entity_select_callback(entity) else '(  )'
        keyboard.append([button(
            f'{action_identifier}-select_{entity.identifier()}',
            f'{button_prefix} {entity.display_name()}'
        )])

    keyboard.append([
        abort_button(action_identifier),
        button(f'{action_identifier}-continue', trans.t('conversation.continue'), emojis.FORWARD)
    ])

    return InlineKeyboardMarkup(keyboard)


def abort_button(action_identifier):
    return button(f'{action_identifier}-abort', trans.t('conversation.cancel'), emojis.BACK)


def get_item_id(callback_query):
    data = callback_query.data.split('_')
    return data[-1]


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
