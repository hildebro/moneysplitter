from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from queries import checklist_queries, item_queries

CHECKLIST_OVERVIEW_TEXT = \
    'This is your personal *checklist overview*.\n\nAll checklists that you create or join will be listed here. ' \
    'Click on a checklist button to enter its main menu.\nYou may also create a *new checklist* or *refresh* this ' \
    'overview in order for checklists that you have recently joined to appear.'

ADVANCED_CHECKLIST_MENU_TEXT = 'This is the advanced menu for the checklist called *{}*. Please choose an action below.'


def render_checklist_overview(update, context):
    reply_markup = build_checklist_overview_markup(context, update.message.chat_id)
    update.message.reply_text(CHECKLIST_OVERVIEW_TEXT, reply_markup=reply_markup, parse_mode='Markdown')


def render_checklist_overview_from_callback(update, context, as_new=False):
    reply_markup = build_checklist_overview_markup(context, update.callback_query.message.chat_id)
    if as_new:
        update.callback_query.message.reply_text(CHECKLIST_OVERVIEW_TEXT, reply_markup=reply_markup,
                                                 parse_mode='Markdown')
        return

    update.callback_query.edit_message_text(text=CHECKLIST_OVERVIEW_TEXT, reply_markup=reply_markup,
                                            parse_mode='Markdown')


def build_checklist_overview_markup(context, user_id):
    context.user_data.pop('checklist', None)
    context.user_data['all_checklists'] = {}

    keyboard = []
    checklists = checklist_queries.find_by_participant(user_id)
    for checklist in checklists:
        context.user_data['all_checklists'][checklist.id] = checklist
        keyboard.append([InlineKeyboardButton(checklist.name, callback_data='checklist_menu_{}'.format(checklist.id))])
    keyboard.append([InlineKeyboardButton('🌟 New checklist 🌟', callback_data='new_checklist')])
    keyboard.append([InlineKeyboardButton('🔄 Refresh 🔄', callback_data='refresh_checklists')])

    return InlineKeyboardMarkup(keyboard)


MAIN_MENU_HEADER = \
    'This is the *main menu* for the checklist called *{}*.'

ITEM_LISTING = \
    'It contains the following items:\n{}'

NO_ITEMS = \
    'It contains no items.'

MAIN_MENU_INFO = \
    'If you want to add new items, simply send me a message containing the item name.'


def render_checklist_menu(update, context):
    checklist_id = int(update.callback_query.data.split('_')[-1])
    checklist = context.user_data['all_checklists'][checklist_id]
    context.user_data['checklist'] = checklist

    update.callback_query.edit_message_text(text=build_checklist_menu_text(checklist),
                                            reply_markup=build_checklist_menu_markup(
                                                update.callback_query.from_user.id == checklist.creator_id
                                            ),
                                            parse_mode='Markdown')


def render_checklist_menu_as_new(update, context):
    checklist = context.user_data['checklist']
    update.message.reply_text(build_checklist_menu_text(checklist),
                              reply_markup=build_checklist_menu_markup(
                                  update.message.from_user.id == checklist.creator_id
                              ),
                              parse_mode='Markdown')


def build_checklist_menu_text(checklist):
    checklist_items = item_queries.find_by_checklist(checklist.id)
    text = MAIN_MENU_HEADER.format(checklist.name) + '\n\n'
    if len(checklist_items) == 0:
        text += NO_ITEMS
    else:
        text += ITEM_LISTING.format('\n'.join(map(lambda checklist_item: checklist_item.name, checklist_items)))
    text += '\n\n' + MAIN_MENU_INFO

    return text


def build_checklist_menu_markup(is_admin_menu_allowed):
    keyboard = [
        [InlineKeyboardButton('Start new purchase', callback_data='new_purchase')],
        [InlineKeyboardButton('Show unresolved purchases', callback_data='show_purchases')],
        [InlineKeyboardButton('Resolve purchases', callback_data='equalize')],
        [InlineKeyboardButton('Remove items', callback_data='remove_items')]
    ]
    if is_admin_menu_allowed:
        keyboard.append([InlineKeyboardButton('Admin Menu', callback_data='admin_menu')])
    keyboard.append([InlineKeyboardButton('Back to checklist overview', callback_data='checklist_overview')])
    return InlineKeyboardMarkup(keyboard)


def render_admin_menu(update, context):
    checklist_id = context.user_data['checklist'].id
    keyboard = [
    ]
    if checklist_queries.is_creator(checklist_id, update.callback_query.from_user.id):
        keyboard.append([InlineKeyboardButton('Delete checklist', callback_data='delete_checklist')])

    keyboard.append(
        [InlineKeyboardButton('Back to default options', callback_data='checklist_menu_{}'.format(checklist_id))]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.edit_message_text(
        text=ADVANCED_CHECKLIST_MENU_TEXT.format(context.user_data['checklist'].name),
        reply_markup=reply_markup, parse_mode='Markdown')
