from sqlalchemy import or_

from ..models import Checklist, User


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


def find_participants_for_removal(session, checklist_id, user_id):
    return session \
        .query(User) \
        .filter(User.joined_checklists.any(Checklist.id == checklist_id)) \
        .filter(or_(User.deleting_user_id == None, User.deleting_user_id == user_id)) \
        .filter(User.id != user_id) \
        .order_by(User.id) \
        .all()


def mark_for_removal(session, deleting_user_id, participant):
    participant = session.query(User).filter(User.id == participant).one()
    if participant.deleting_user_id is None:
        participant.deleting_user_id = deleting_user_id
    elif participant.deleting_user_id == deleting_user_id:
        participant.deleting_user_id = None
    else:
        return False

    session.commit()
    return True


def abort_removal(session, checklist_id, user_id):
    session \
        .query(User) \
        .filter(User.joined_checklists.any(Checklist.id == checklist_id), User.deleting_user_id == user_id) \
        .update({'deleting_user_id': None}, synchronize_session=False)
    session.commit()


def delete_pending(session, checklist_id, user_id):
    users = session \
        .query(User) \
        .filter(User.joined_checklists.any(Checklist.id == checklist_id), User.deleting_user_id == user_id) \
        .all()

    if len(users) == 0:
        return False

    checklist = session \
        .query(Checklist) \
        .filter(Checklist.id == checklist_id) \
        .one()

    for user in users:
        user.joined_checklists.remove(checklist)

    session.commit()
    return True
