from entity.base import Session
from entity.user import User


def exists(user_id):
    session = Session()
    user_query = session.query(User).filter(User.id == user_id)
    user_count = user_query.count() > 0
    session.close()
    return user_count


def register(telegram_user):
    session = Session()
    user = User(telegram_user.id, telegram_user.username, telegram_user.first_name, telegram_user.last_name)
    session.add(user)
    session.commit()
    session.close()


def find(user_id):
    session = Session()
    user = session.query(User).filter(User.id == user_id).one()
    session.close()
    return user


def refresh(telegram_user):
    session = Session()
    user = session.query(User).filter(User.id == telegram_user.id).one()
    user.username = telegram_user.username
    session.commit()
    session.close()
