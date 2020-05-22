from telegram import InlineKeyboardMarkup, InputTextMessageContent, InlineQueryResultArticle

from ..db import session_wrapper
from ..db.queries import checklist_queries, user_queries, participant_queries
from ..helper import emojis
from ..helper.function_wrappers import button
from ..i18n import trans


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
                                     reply_markup=InlineKeyboardMarkup([
                                         [button(f'join_checklist_{checklist.id}',
                                                 trans.t('inline.join'),
                                                 emojis.RUNNER)
                                          ]
                                     ]))
        )
    update.inline_query.answer(inline_options)


# noinspection PyUnusedLocal
@session_wrapper
def answer_callback(session, update, context):
    user_id = update.callback_query.from_user.id
    if not user_queries.exists(session, user_id):
        update.callback_query.answer(trans.t('inline.accept.not_registered'))
        return

    checklist_id = update.callback_query.data.split('_')[-1]
    if participant_queries.exists(session, checklist_id, user_id):
        update.callback_query.answer(trans.t('inline.accept.already_joined'))
        return

    participant_queries.create(session, checklist_id, user_id)
    update.callback_query.answer(trans.t('inline.accept.success'))
