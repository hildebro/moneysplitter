from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, ConversationHandler, CommandHandler

from db import session_wrapper
from main import conv_cancel
from queries import checklist_queries, user_queries
from services import response_builder

USER_REMOVAL_MESSAGE = \
    'You are now removing users from checklist *{}*.\n\nClick on a username to *(de)select* them for ' \
    'removal.\nWhen you are done, click *Commit* to remove all selected users.\nClick *Abort* to exit ' \
    'without removals. '

BASE_STATE = 0


def get_removal_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(initialize, pattern='^remove_users$')],
        states={
            BASE_STATE: [
                CallbackQueryHandler(mark_user, pattern='^mark_[0-9]+$'),
                CallbackQueryHandler(abort, pattern='^abort_[0-9]+$'),
                CallbackQueryHandler(commit, pattern='^commit_[0-9]+$')
            ]
        },
        fallbacks=[CommandHandler('cancel', conv_cancel)]
    )


@session_wrapper
def initialize(session, update, context):
    context.user_data['removal_dict'] = {}
    users = checklist_queries.find_participants(session, context.user_data['checklist'].id)
    for user in users:
        context.user_data['removal_dict'][user.id] = user.username

    render_removal_buttons(update, context)

    return BASE_STATE


def mark_user(update, context):
    query = update.callback_query
    user_id = int(query.data.split('_')[-1])
    user_name = context.user_data['removal_dict'][user_id]
    if '🚫' in user_name:
        user_name = user_name.replace('🚫', '')
    else:
        user_name = '🚫' + user_name + '🚫'

    context.user_data['removal_dict'][user_id] = user_name
    render_removal_buttons(update, context)

    return BASE_STATE


@session_wrapper
def abort(session, update, context):
    context.user_data['removal_dict'] = None
    text, markup = response_builder.checklist_menu(session, update.callback_query.from_user, context)
    update.callback_query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return ConversationHandler.END


@session_wrapper
def commit(session, update, context):
    ids_to_remove = []
    removal_dict = context.user_data['removal_dict']
    for user_id in removal_dict:
        if '🚫' in removal_dict[user_id]:
            ids_to_remove.append(user_id)

    if update.callback_query.from_user.id in ids_to_remove:
        update.callback_query.answer('You cannot remove yourself!')
        return BASE_STATE

    user_queries.remove_all(session, ids_to_remove)
    context.user_data['removal_dict'] = None
    text, markup = response_builder.checklist_menu(session, update.callback_query.from_user, context)
    update.callback_query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')

    return ConversationHandler.END


def render_removal_buttons(update, context):
    checklist = context.user_data['checklist']
    removal_dict = context.user_data['removal_dict']

    keyboard = []
    for user_id in removal_dict:
        keyboard.append([InlineKeyboardButton(removal_dict[user_id], callback_data='mark_{}'.format(user_id))])
    keyboard.append([
        InlineKeyboardButton('Abort', callback_data='abort_{}'.format(checklist.id)),
        InlineKeyboardButton('Commit', callback_data='commit_{}'.format(checklist.id))
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(text=USER_REMOVAL_MESSAGE.format(checklist.name),
                                            reply_markup=reply_markup, parse_mode='Markdown')
