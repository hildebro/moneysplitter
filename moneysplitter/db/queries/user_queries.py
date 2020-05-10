from sqlalchemy import or_

from ..models import Participant, User, UserSettings


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


def find_participants_for_removal(session, deleting_user_id):
    checklist = get_selected_checklist(session, deleting_user_id)
    return session \
        .query(Participant) \
        .filter(Participant.checklist_id == checklist.id, Participant.user_id != deleting_user_id) \
        .filter(or_(Participant.deleting_user_id == None, Participant.deleting_user_id == deleting_user_id)) \
        .order_by(Participant.user_id) \
        .all()


def mark_for_removal(session, deleting_user_id, user_id):
    checklist = get_selected_checklist(session, deleting_user_id)
    participant = session \
        .query(Participant) \
        .filter(Participant.user_id == user_id, Participant.checklist_id == checklist.id) \
        .one()
    if participant.deleting_user_id is None:
        participant.deleting_user_id = deleting_user_id
    elif participant.deleting_user_id == deleting_user_id:
        participant.deleting_user_id = None
    else:
        return False

    session.commit()
    return True


def abort_removal(session, deleting_user_id):
    checklist = get_selected_checklist(session, deleting_user_id)
    session \
        .query(Participant) \
        .filter(Participant.checklist_id == checklist.id, Participant.deleting_user_id == deleting_user_id) \
        .update({'deleting_user_id': None})
    session.commit()


def delete_pending(session, checklist_id, user_id):
    participants = session \
        .query(Participant) \
        .filter(Participant.checklist_id == checklist_id, Participant.deleting_user_id == user_id) \
        .all()

    if len(participants) == 0:
        return False

    for participant in participants:
        session.delete(participant)

    session.commit()
    return True


def get_selected_checklist(session, user_id):
    user_settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).one()
    return user_settings.selected_checklist


def select_checklist(session, checklist_id, user_id):
    session \
        .query(UserSettings) \
        .filter(UserSettings.user_id == user_id) \
        .update({'checklist_id': checklist_id})
    session.commit()
