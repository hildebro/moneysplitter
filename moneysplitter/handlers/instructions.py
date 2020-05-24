from telegram import InlineKeyboardMarkup

from . import main_menu
from ..helper import emojis
from ..helper.function_wrappers import edit, button
from ..i18n import trans


def callback(update, context):
    text = trans.t('instructions.overview')
    markup = InlineKeyboardMarkup([
        [button('instructions.basics', trans.t('instructions.basics.link'))],
        [button('instructions.checklist', trans.t('instructions.checklist.link'))],
        [button('instructions.item', trans.t('instructions.item.link'))],
        [button('instructions.purchase', trans.t('instructions.purchase.link'))],
        [button('instructions.write_off', trans.t('instructions.write_off.link'))],
        [button('instructions.balance', trans.t('instructions.balance.link'))],
        [main_menu.link_button()],
    ])
    edit(update.callback_query, text, markup)


def render_instructions(query, text, previous_instructions, next_instructions):
    markup = InlineKeyboardMarkup(
        [
            [main_menu.link_button(), button('instructions', trans.t('instructions.link'), emojis.BACK)],
            [
                button(previous_instructions, trans.t('instructions.back'), emojis.PREVIOUS),
                button(next_instructions, trans.t('instructions.forward'), emojis.FORWARD)
            ]
        ]
    )
    edit(query, trans.t(text), markup)


def basics(update, context):
    render_instructions(update.callback_query, 'instructions.basics.text', 'instructions', 'instructions.checklist')


def checklist(update, context):
    render_instructions(update.callback_query, 'instructions.checklist.text', 'instructions.basics',
                        'instructions.item')


def item(update, context):
    render_instructions(update.callback_query, 'instructions.item.text', 'instructions.checklist',
                        'instructions.purchase')


def purchase(update, context):
    render_instructions(update.callback_query, 'instructions.purchase.text', 'instructions.item',
                        'instructions.write_off')


def write_off(update, context):
    render_instructions(update.callback_query, 'instructions.write_off.text', 'instructions.purchase',
                        'instructions.balance')


def balance(update, context):
    render_instructions(update.callback_query, 'instructions.balance.text', 'instructions.write_off', 'instructions')
