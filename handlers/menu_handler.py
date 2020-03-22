from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from db import session_wrapper
from queries import checklist_queries
from services import response_builder


@session_wrapper
def checklist_overview_command(session, update, context):
    reply_markup = response_builder.checklist_overview_markup(session, context, update.message.from_user.id)
    update.message.reply_text(response_builder.CHECKLIST_OVERVIEW_TEXT,
                              reply_markup=reply_markup,
                              parse_mode='Markdown')


@session_wrapper
def checklist_overview_callback(session, update, context):
    markup = response_builder.checklist_overview_markup(session, context, update.callback_query.from_user.id)
    update.callback_query.edit_message_text(text=response_builder.CHECKLIST_OVERVIEW_TEXT, reply_markup=markup,
                                            parse_mode='Markdown')


def advanced_settings_callback(update, context):
    checklist = context.user_data['checklist']
    keyboard = [
        [InlineKeyboardButton('🗑️ Remove items 🗑️', callback_data='remove_items')],
        [InlineKeyboardButton('️🏃‍♂️ Remove users ️🏃‍♂️', callback_data='remove_users')],
        [InlineKeyboardButton('☣️ Delete checklist ☣️', callback_data='delete_checklist')],
        [InlineKeyboardButton('🔙 Main menu 🔙', callback_data='checklist_menu_{}'.format(checklist.id))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(
        text=response_builder.ADVANCED_CHECKLIST_MENU_TEXT.format(context.user_data['checklist'].name),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


@session_wrapper
def checklist_menu_callback(session, update, context):
    checklist_id = int(update.callback_query.data.split('_')[-1])
    checklist = context.user_data['all_checklists'][checklist_id]
    context.user_data['checklist'] = checklist

    text, markup = response_builder.checklist_menu(session, update.callback_query.from_user, context)
    update.callback_query.edit_message_text(text=text, reply_markup=markup, parse_mode='Markdown')


@session_wrapper
def refresh_checklists(session, update, context):
    user_id = update.callback_query.from_user.id
    currently_displayed_checklists = context.user_data['all_checklists']
    db_checklist_count = checklist_queries.count_checklists(session, user_id)

    if len(currently_displayed_checklists) == db_checklist_count:
        update.callback_query.answer('Nothing new to show!')
        return

    reply_markup = response_builder.checklist_overview_markup(session, context, user_id)
    update.message.reply_text(response_builder.CHECKLIST_OVERVIEW_TEXT, reply_markup=reply_markup,
                              parse_mode='Markdown')

    update.callback_query.answer('Checklist overview refreshed!')
