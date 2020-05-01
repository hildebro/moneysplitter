from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from ..db import session_wrapper
from ..db.queries import checklist_queries
from ..i18n import trans
from ..services import response_builder, emojis
from ..services.response_builder import button, interpret_data


@session_wrapper
def checklist_overview_command(session, update, context):
    reply_markup = response_builder.checklist_overview_markup(session, context, update.message.from_user.id)
    update.message.reply_text(trans.t('checklist.overview.text'), reply_markup=reply_markup, parse_mode='Markdown')


@session_wrapper
def checklist_overview_callback(session, update, context):
    query = update.callback_query
    markup = response_builder.checklist_overview_markup(session, context, query.from_user.id)
    query.edit_message_text(text=trans.t('checklist.overview.text'), reply_markup=markup, parse_mode='Markdown')


def settings_callback(update, context):
    checklist = context.user_data['checklist']
    reply_markup = InlineKeyboardMarkup([
        [button(f'remove-items_{checklist.id}', trans.t('checklist.settings.delete_items'), emojis.BIN)],
        [button('remove_users', trans.t('checklist.settings.remove_users.link'), emojis.RUNNER)],
        [button('delete_checklist', trans.t('checklist.settings.delete_checklist'), emojis.HAZARD)],
        [button(f'checklist-menu_{checklist.id}', trans.t('checklist.menu.link'), emojis.BACK)]
    ])
    update.callback_query.edit_message_text(
        text=trans.t('checklist.settings.text', name=context.user_data['checklist'].name),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


@session_wrapper
def checklist_menu_callback(session, update, context):
    callback_data = interpret_data(update.callback_query)
    checklist_id = callback_data['checklist_id']
    checklist = context.user_data['all_checklists'][checklist_id]
    context.user_data['checklist'] = checklist

    text, markup = response_builder.checklist_menu(session, update.callback_query.from_user, context)
    update.callback_query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')


@session_wrapper
def refresh_checklists(session, update, context):
    user_id = update.callback_query.from_user.id
    current_checklist = context.user_data['all_checklists']
    db_checklist_count = checklist_queries.count_checklists(session, user_id)

    if len(current_checklist) == db_checklist_count:
        update.callback_query.answer('Nothing new to show!')
        return

    reply_markup = response_builder.checklist_overview_markup(session, context, user_id)
    update.message.reply_text(trans.t('checklist.overview.text'), reply_markup=reply_markup, parse_mode='Markdown')
    update.callback_query.answer('Checklist overview refreshed!')


@session_wrapper
def conv_cancel(session, update, context):
    update.message.reply_text(trans.t('conversation.cancel'))
    markup = response_builder.checklist_overview_markup(session, context, update.message.from_user.id)
    update.message.reply_text(trans.t('checklist.overview.text'), reply_markup=markup, parse_mode='Markdown')

    return ConversationHandler.END


@session_wrapper
def cancel_conversation(session, update, context):
    markup = response_builder.checklist_overview_markup(session, context, update.callback_query.from_user.id)
    update.callback_query.edit_message_text(text=trans.t('checklist.overview.text'), reply_markup=markup,
                                            parse_mode='Markdown')

    return ConversationHandler.END
