from telegram import InlineKeyboardButton


def button(callback_data, label, emoji=''):
    return InlineKeyboardButton(emoji + label + emoji, callback_data=callback_data)


def reply(message, text, markup=None):
    message.reply_text(text, reply_markup=markup, parse_mode='Markdown')


def edit(query, text, markup=None):
    query.edit_message_text(text, reply_markup=markup, parse_mode='Markdown')


def get_entity_id(callback_query):
    data = callback_query.data.split('_')
    return data[-1]
