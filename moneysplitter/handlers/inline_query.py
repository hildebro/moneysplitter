from telegram import InlineKeyboardMarkup, InputTextMessageContent, InlineQueryResultArticle, InlineKeyboardButton

from . import main_menu
from ..db import session_wrapper
from ..db.queries import checklist_queries, user_queries, participant_queries
from ..helper import emojis
from ..helper.function_wrappers import button
from ..i18n import trans


def invite_button(checklist_name):
    return InlineKeyboardButton(emojis.PINCH + trans.t('inline.invite') + emojis.PINCH,
                                switch_inline_query=checklist_name)


@session_wrapper
def query_callback(session, update, context):
    query = update.inline_query.query

    inline_options = []
    for checklist in checklist_queries.find_by_creator(session, update.inline_query.from_user.id):
        if query and not checklist.name.lower().startswith(query.lower()):
            continue

        inline_options.append(
            InlineQueryResultArticle(id=checklist.id, title=checklist.name,
                                     input_message_content=InputTextMessageContent(
                                         trans.t('inline.text', name=checklist.name)),
                                     reply_markup=InlineKeyboardMarkup(
                                         [[button(f'join_checklist_{checklist.id}', trans.t('inline.join'))]])
                                     )
        )
    update.inline_query.answer(inline_options)


# noinspection PyUnusedLocal
@session_wrapper
def answer_callback(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    if not user_queries.exists(session, user_id):
        query.answer(trans.t('inline.accept.not_registered'))
        return

    checklist_id = query.data.split('_')[-1]
    if participant_queries.exists(session, checklist_id, user_id):
        query.answer(trans.t('inline.accept.already_joined'))
        return

    participant_queries.create(session, checklist_id, user_id)
    if participant_queries.count(session, user_id) == 1:
        user_queries.select_checklist(session, checklist_id, user_id)
        text = trans.t('inline.accept.new_user')
        markup = InlineKeyboardMarkup([[button('checklist-menu', trans.t('checklist.menu.link'), emojis.FORWARD)]])
    else:
        text = trans.t('inline.accept.old_user')
        markup = InlineKeyboardMarkup([[
            main_menu.link_button(),
            button('checklist-picker', trans.t('checklist.picker.link'), emojis.FORWARD)
        ]])

    query.bot.send_message(user_id, text, reply_markup=markup, parse_mode='Markdown')
