from queries import user_queries


def handle_start_command(update, context):
    user = update.message.from_user
    if user_queries.exists(user.id):
        update.message.reply_text('You already started the bot!')
        refresh_username(update, context)
        return

    user_queries.register(update.message.from_user)
    update.message.reply_text('Hello! This bot serves two functions:\n1) Allow a group of people to create a common '
                              'checklist for items which they want to buy together. Individual users can mark items '
                              'as purchased and define how much money they spend on them.\n2) Calculate the amounts '
                              'of money that have to be transferred between group members in order for everyone to be '
                              'even.')


def refresh_username(update, context):
    user_queries.refresh(update.message.from_user)
