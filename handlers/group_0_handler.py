from db import session_wrapper
from queries import user_queries


@session_wrapper
def handle_start_command(session, update, context):
    user = update.message.from_user
    if user_queries.exists(session, user.id):
        update.message.reply_text('You already started the bot!')
        user_queries.refresh(session, user)
        return

    user_queries.register(session, update.message.from_user)
    update.message.reply_text(
        'Thanks for using Purchase Splitter Bot! If you are here, because you were invited to someone else\'s '
        'checklist, you can now head back to their invite message and click the button. Otherwise, you can start '
        'using the bot by creating your own checklist.\n\n*NOTE*: This bot was made under the assumption that you '
        'will interact with it directly in this chat. I cannot guarantee that it works as intended, if you invite it '
        'into a telegram group with other users.')


# noinspection PyUnusedLocal
@session_wrapper
def refresh_username(session, update, context):
    user_queries.refresh(session, update.message.from_user)
