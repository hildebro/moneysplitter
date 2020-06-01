from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ConversationHandler, MessageHandler, Filters

from . import main_menu, purchase_list
from ..db import session_wrapper
from ..db.models.purchase_distribution import PurchaseDistribution
from ..db.queries import purchase_queries, distribution_queries, user_queries
from ..helper import write_off_calculator, emojis
from ..helper.calculator import Calculator
from ..helper.function_wrappers import reply, edit, button, get_entity_id
from ..i18n import trans

ACTION_SELECT_STATE, DISTRIBUTION_SELECT_STATE, DISTRIBUTION_SET_STATE = range(3)

ACTION_IDENTIFIER = 'purchase.edit'


def conversation_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(entry_callback, pattern=f'^{ACTION_IDENTIFIER}_[0-9]+$')],
        states={
            ACTION_SELECT_STATE: [
                CallbackQueryHandler(distribution_menu, pattern=f'^{ACTION_IDENTIFIER}.distribution.menu$'),
                CallbackQueryHandler(write_off, pattern=f'^{ACTION_IDENTIFIER}.write_off$'),
            ],
            DISTRIBUTION_SELECT_STATE: [
                CallbackQueryHandler(ask_distribution,
                                     pattern=f'^{ACTION_IDENTIFIER}.distribution.edit_[0-9]+$'),
                CallbackQueryHandler(entry_callback, pattern=f'^{ACTION_IDENTIFIER}.main_[0-9]+$'),
            ],
            DISTRIBUTION_SET_STATE: [
                CallbackQueryHandler(distribution_menu, pattern=f'^{ACTION_IDENTIFIER}.distribution.menu$'),
                MessageHandler(Filters.text, check_distribution),
            ]
        },
        fallbacks=[CallbackQueryHandler(exit_conversation, pattern=f'^{ACTION_IDENTIFIER}.exit$')]
    )


@session_wrapper
def entry_callback(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    purchase_id = get_entity_id(query)
    purchase = purchase_queries.find(session, purchase_id)

    if purchase.buyer_id != user_id:
        query.answer(trans.t(f'{ACTION_IDENTIFIER}.access_denied'))
        return ConversationHandler.END

    user_queries.set_purchase_edit(session, user_id, purchase_id)
    checklist = user_queries.get_selected_checklist(session, query.from_user.id)

    text = trans.t(f'{ACTION_IDENTIFIER}.text', name=checklist.name)
    markup = InlineKeyboardMarkup([
        [
            button(f'{ACTION_IDENTIFIER}.distribution.menu',
                   trans.t(f'{ACTION_IDENTIFIER}.distribution.link'),
                   emojis.MONEY_WINGS),
        ],
        [
            button(f'{ACTION_IDENTIFIER}.exit', trans.t('purchase.log.link'), emojis.BACK),
            button(f'{ACTION_IDENTIFIER}.write_off', trans.t(f'{ACTION_IDENTIFIER}.write_off'), emojis.MONEY)
        ]
    ])

    edit(query, text, markup)
    return ACTION_SELECT_STATE


@session_wrapper
def distribution_menu(session, update, context):
    query = update.callback_query
    purchase_id = user_queries.get_purchase_edit_id(session, query.from_user.id)
    purchase = purchase_queries.find(session, purchase_id)

    if len(purchase.checklist.participants) == 1:
        query.answer(trans.t(f'{ACTION_IDENTIFIER}.no_participants'))
        return ACTION_SELECT_STATE

    if len(purchase.checklist.participants) != len(purchase.distributions):
        distribution_dict = {distribution.user_id: distribution for distribution in purchase.distributions}
        for participant in purchase.checklist.participants:
            if participant.user_id not in distribution_dict:
                purchase.distributions.append(PurchaseDistribution(purchase.id, participant.user_id, 0))

    session.commit()

    text, markup = build_distribution_data(purchase)
    edit(query, text, markup)
    return DISTRIBUTION_SELECT_STATE


def build_distribution_data(purchase):
    keyboard = []
    for distribution in purchase.distributions:
        keyboard.append([
            button(f'{ACTION_IDENTIFIER}.distribution.edit_{distribution.id}', f'{distribution.display_name()}')])

    keyboard.append([
        button(f'{ACTION_IDENTIFIER}.exit', trans.t('purchase.log.link'), emojis.BACK),
        button(f'{ACTION_IDENTIFIER}.main_{purchase.id}', trans.t(f'{ACTION_IDENTIFIER}.link'),
               emojis.BACK)
    ])

    text = trans.t(f'{ACTION_IDENTIFIER}.distribution.text', name=purchase.checklist.name, price=purchase.get_price(),
                   leftover_price=purchase.get_leftover_price())
    markup = InlineKeyboardMarkup(keyboard)
    return text, markup


@session_wrapper
def ask_distribution(session, update, context):
    query = update.callback_query
    operator_id = query.from_user.id
    distribution_id = get_entity_id(query)
    distribution = distribution_queries.find(session, distribution_id)

    user_queries.set_purchase_distribution(session, operator_id, distribution.id)

    text = trans.t(f'{ACTION_IDENTIFIER}.distribution.ask', name=distribution.user.display_name())
    markup = InlineKeyboardMarkup([[
        button(f'{ACTION_IDENTIFIER}.exit', trans.t('purchase.log.link'), emojis.BACK),
        button(f'{ACTION_IDENTIFIER}.distribution_menu', trans.t(f'{ACTION_IDENTIFIER}.distribution.link'), emojis.BACK)
    ]])
    edit(query, text, markup)
    return DISTRIBUTION_SET_STATE


@session_wrapper
def check_distribution(session, update, context):
    message = update.message
    user_id = message.from_user.id

    retry_markup = InlineKeyboardMarkup([[
        button(f'{ACTION_IDENTIFIER}.exit', trans.t('purchase.log.link'), emojis.BACK),
        button(f'{ACTION_IDENTIFIER}.distribution_menu', trans.t(f'{ACTION_IDENTIFIER}.distribution.link'), emojis.BACK)
    ]])
    try:
        # replacing commas with dots to turn all numbers from the user into valid floats
        new_amount_text = message.text.replace(',', '.')
        new_amount = Calculator.evaluate(new_amount_text) * 100.0
    except SyntaxError:
        reply(message, trans.t(f'{ACTION_IDENTIFIER}.distribution.invalid'), retry_markup)
        return DISTRIBUTION_SET_STATE

    purchase_id = user_queries.get_purchase_edit_id(session, user_id)
    purchase = purchase_queries.find(session, purchase_id)
    distribution_id = user_queries.get_purchase_distribution_id(session, user_id)
    distribution = distribution_queries.find(session, distribution_id)

    max_new_amount = purchase.leftover_price + distribution.amount
    if new_amount > max_new_amount:
        text = trans.t(f'{ACTION_IDENTIFIER}.distribution.insufficient',
                       max_amount="{:.2f}".format(max_new_amount / 100.0))
        reply(message, text, retry_markup)
        return DISTRIBUTION_SET_STATE

    distribution.amount = new_amount
    purchase.leftover_price = max_new_amount - new_amount
    session.commit()

    text, markup = build_distribution_data(purchase)
    reply(message, text, markup)
    return DISTRIBUTION_SELECT_STATE


@session_wrapper
def write_off(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id
    purchase_id = user_queries.get_purchase_edit_id(session, user_id)
    purchase = purchase_queries.find(session, purchase_id)
    checklist = purchase.checklist

    write_off_calculator.write_off(session, checklist, [purchase])

    edit(query, trans.t(f'{ACTION_IDENTIFIER}.write_off_success'), InlineKeyboardMarkup([[main_menu.link_button()]]))
    return ConversationHandler.END


@session_wrapper
def exit_conversation(session, update, context):
    query = update.callback_query
    user_id = query.from_user.id

    text, markup = purchase_list.purchase_log_data(session, user_id)
    edit(query, text, markup)
    return ConversationHandler.END
