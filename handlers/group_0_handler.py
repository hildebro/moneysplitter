from queries import user_queries


def handle_start_command(update, context):
    user = update.message.from_user
    if user_queries.exists(user.id):
        update.message.reply_text('You already started the bot!')
        refresh_username(update, context)
        return

    user_queries.register(update.message.from_user)
    update.message.reply_text(
        'Thanks for using Purchase Splitter Bot! If you are here, because you were invited to someone else\'s '
        'checklist, you can now head back to their invite message and click the button. Otherwise, you can start '
        'using the bot by creating your own checklist.')


def refresh_username(update, context):
    user_queries.refresh(update.message.from_user)
