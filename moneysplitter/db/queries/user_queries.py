from ..models import User, UserSettings


def exists(session, user_id):
    user_query = session.query(User).filter(User.id == user_id)
    user_count = user_query.count() > 0
    return user_count


def register(session, telegram_user):
    user = User(telegram_user.id, telegram_user.username, telegram_user.first_name, telegram_user.last_name)
    session.add(user)
    session.flush()
    session.add(UserSettings(telegram_user.id))
    session.commit()


def find(session, user_id):
    user = session.query(User).filter(User.id == user_id).one()
    return user


def refresh(session, telegram_user):
    user = session.query(User).filter(User.id == telegram_user.id).scalar()
    if user is None:
        return

    if user.username == telegram_user.username:
        return

    user.username = telegram_user.username
    session.commit()


def get_selected_checklist(session, user_id):
    user_settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).one()
    return user_settings.selected_checklist


def select_checklist(session, checklist_id, user_id):
    session \
        .query(UserSettings) \
        .filter(UserSettings.user_id == user_id) \
        .update({'checklist_id': checklist_id})
    session.commit()
