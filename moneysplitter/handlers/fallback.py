from telegram import InlineKeyboardMarkup

from . import main_menu
from ..helper.function_wrappers import edit, reply
from ..i18n import trans


def button_callback(update, context):
    edit(update.callback_query, trans.t('fallback.callback_query'), InlineKeyboardMarkup([[main_menu.link_button()]]))


def command_callback(update, context):
    reply(update.message, trans.t('fallback.command'), InlineKeyboardMarkup([[main_menu.link_button()]]))
