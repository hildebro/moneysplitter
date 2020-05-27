from enum import Enum
from typing import Callable, List, Any

from sqlalchemy.orm import Session
from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler, CallbackQueryHandler, Handler, MessageHandler, Filters

from .function_wrappers import button, edit, get_entity_id, reply
from ..db import session_wrapper, user_queries
from ..handlers import main_menu, settings
from ..helper import emojis
from ..i18n import trans


class AbortTarget(Enum):
    MAIN_MENU = 0
    SETTINGS = 1


class EntitySelectConversationBuilder:
    def __init__(self,
                 action_identifier: str,
                 get_entities_func: Callable[[Session, int], List],
                 is_selected_func: Callable[[Any], bool],
                 select_entity_func: Callable[[Session, int, int], bool],
                 abort_func: Callable[[Session, int], None],
                 abort_target: AbortTarget,
                 continue_handler_callback: Callable[[Session, int], None],
                 entry_func: Callable[[Session, int], None] = None,
                 post_continue_state: List[Handler] = None,
                 message_callback: Callable[[Session, int, str], None] = None,
                 allow_zero_entities: bool = False):
        self.action_identifier = action_identifier
        self.get_entities_func = get_entities_func
        self.is_selected_func = is_selected_func
        self.select_entity_func = select_entity_func
        self.abort_func = abort_func
        self.abort_target = abort_target
        self.continue_handler_callback = continue_handler_callback
        self.entry_func = entry_func
        self.post_continue_state = post_continue_state
        self.message_callback = message_callback
        self.allow_zero_entities = allow_zero_entities

    def conversation_handler(self):
        states = {
            0: [self._select_handler(), self._continue_handler(), self._message_handler()],
        }
        if self.post_continue_state is not None:
            states[1] = self.post_continue_state

        return ConversationHandler(
            entry_points=[self._entry_handler()],
            states=states,
            fallbacks=[self._abort_handler()])

    def _entry_handler(self):
        @session_wrapper
        def entry_callback(session, update, context):
            query = update.callback_query
            user_id = query.from_user.id

            if self.entry_func is not None:
                self.entry_func(session, user_id)

            if len(self.get_entities_func(session, user_id)) == 0 and not self.allow_zero_entities:
                self.abort_func(session, user_id)
                query.answer(trans.t(f'{self.action_identifier}.no_entities'))
                return ConversationHandler.END

            text = self._message_text(session, user_id)
            markup = self._entity_select_markup(session, user_id)
            edit(query, text, markup)
            return 0

        return CallbackQueryHandler(entry_callback, pattern=self.entry_pattern())

    def _message_handler(self):
        @session_wrapper
        def callback(session, update, context):
            message = update.message
            user_id = message.from_user.id
            if self.message_callback is not None:
                self.message_callback(session, user_id, message.text)
            else:
                reply(message, trans.t('conversation.message_not_allowed'))

            text = self._message_text(session, user_id)
            markup = self._entity_select_markup(session, user_id)
            reply(message, text, markup)

        return MessageHandler(Filters.text, callback)

    def _select_handler(self):
        @session_wrapper
        def select_callback(session, update, context):
            query = update.callback_query
            user_id = query.from_user.id

            success = self.select_entity_func(session, user_id, get_entity_id(query))
            if not success:
                query.answer(trans.t('conversation.already_selected'))
                return 0

            text = self._message_text(session, user_id)
            markup = self._entity_select_markup(session, user_id)
            edit(query, text, markup)
            return 0

        return CallbackQueryHandler(select_callback, pattern=self.select_pattern())

    def _continue_handler(self):
        return CallbackQueryHandler(self.continue_handler_callback, pattern=self.continue_pattern())

    def _abort_handler(self):
        @session_wrapper
        def abort_callback(session, update, context):
            query = update.callback_query
            user_id = query.from_user.id

            self.abort_func(session, user_id)

            if self.abort_target == AbortTarget.MAIN_MENU:
                text, markup = main_menu.checklist_menu_data(session, user_id)
            elif self.abort_target == AbortTarget.SETTINGS:
                text, markup = settings.menu_data(session, user_id)
            else:
                raise Exception(f'Unhandled abort target: {self.abort_target}')

            edit(query, text, markup)
            return ConversationHandler.END

        return CallbackQueryHandler(abort_callback, pattern=self.abort_pattern())

    def _entity_select_markup(self, session, user_id):
        keyboard = []
        for entity in self.get_entities_func(session, user_id):
            button_prefix = '(O)' if self.is_selected_func(entity) else '(  )'
            keyboard.append([button(
                f'{self.action_identifier}-select_{entity.identifier()}',
                f'{button_prefix} {entity.display_name()}'
            )])

        keyboard.append([
            abort_button(self.action_identifier, self.abort_target),
            button(f'{self.action_identifier}-continue', trans.t('conversation.continue'), emojis.FORWARD)
        ])

        return InlineKeyboardMarkup(keyboard)

    def _message_text(self, session, user_id):
        checklist = user_queries.get_selected_checklist(session, user_id)
        return trans.t(f'{self.action_identifier}.text', name=checklist.name)

    def entry_pattern(self):
        return f'^{self.action_identifier}$'

    def select_pattern(self):
        return f'^{self.action_identifier}-select_[0-9]+$'

    def continue_pattern(self):
        return f'^{self.action_identifier}-continue$'

    def abort_pattern(self):
        return f'^{self.action_identifier}-abort$'


def abort_button(action_identifier, abort_target):
    if abort_target == AbortTarget.MAIN_MENU:
        label = 'checklist.menu.link'
    elif abort_target == AbortTarget.SETTINGS:
        label = 'checklist.settings.link'
    else:
        raise Exception(f'Unhandled abort target: {abort_target}')

    return button(f'{action_identifier}-abort', trans.t(label), emojis.BACK)
