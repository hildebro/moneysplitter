from db import get_session
from models.user import User


def exists(session, user_id):
    user_query = session.query(User).filter(User.id == user_id)
    user_count = user_query.count() > 0
    return user_count


def register(session, telegram_user):
    user = User(telegram_user.id, telegram_user.username, telegram_user.first_name, telegram_user.last_name)
    session.add(user)
    session.commit()


def find(user_id):
    session = get_session()
    user = session.query(User).filter(User.id == user_id).one()
    session.close()
    return user


def refresh(session, telegram_user):
    user = session.query(User).filter(User.id == telegram_user.id).one()
    user.username = telegram_user.username
    session.commit()


def find_username(user_id):
    session = get_session()
    username = session.query(User.username).filter(User.id == user_id).one()[0]
    session.close()
    return username


def remove_all(ids_to_remove):
    session = get_session()
    session.query(User).filter(User.id.in_(ids_to_remove)).delete(synchronize_session=False)
    session.commit()
    session.close()
