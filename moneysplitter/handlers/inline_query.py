from telegram import InlineKeyboardMarkup, InputTextMessageContent, InlineQueryResultArticle

from ..db import session_wrapper
from ..db.queries import checklist_queries, user_queries
from ..i18n import trans
from ..services import emojis
from ..services.response_builder import button


@session_wrapper
def get_send_handler(session, update, context):
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
    context.bot.answer_inline_query(update.inline_query.id, inline_options)


# noinspection PyUnusedLocal
@session_wrapper
def get_join_handler(session, update, context):
    user_id = update.callback_query.from_user.id
    if not user_queries.exists(session, user_id):
        update.callback_query.answer(trans.t('inline.accept.not_registered'))
        return

    checklist_id = update.callback_query.data.split('_')[-1]
    if checklist_queries.is_participant(session, checklist_id, user_id):
        update.callback_query.answer(trans.t('inline.accept.already_joined'))
        return

    checklist_queries.join(session, checklist_id, user_id)
    update.callback_query.answer(trans.t('inline.accept.success'))
