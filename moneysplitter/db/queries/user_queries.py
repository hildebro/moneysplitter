from ..models import User


def exists(session, user_id):
    user_query = session.query(User).filter(User.id == user_id)
    user_count = user_query.count() > 0
    return user_count


def register(session, telegram_user):
    user = User(telegram_user.id, telegram_user.username, telegram_user.first_name, telegram_user.last_name)
    session.add(user)
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


def find_username(session, user_id):
    username = session.query(User.username).filter(User.id == user_id).one()[0]
    return username


def remove_all(session, ids_to_remove):
    session.query(User).filter(User.id.in_(ids_to_remove)).delete(synchronize_session=False)
    session.commit()
