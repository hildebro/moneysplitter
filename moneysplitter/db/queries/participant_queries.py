from sqlalchemy import or_

from ..models import Participant
from ..queries import user_queries


def create(session, checklist_id, user_id):
    session.add(Participant(checklist_id, user_id))
    session.commit()


def leave(session, user_id):
    checklist = user_queries.get_selected_checklist(session, user_id)
    if checklist.creator_id == user_id:
        return False

    session.query(Participant).filter(Participant.user_id == user_id, Participant.checklist == checklist).delete()
    user_queries.select_checklist(session, None, user_id)
    session.commit()

    return True


def find(session, checklist_id):
    return session.query(Participant).filter(Participant.checklist_id == checklist_id).all()


def count(session, user_id):
    return session \
        .query(Participant) \
        .filter(Participant.user_id == user_id) \
        .count()


def exists(session, checklist_id, user_id):
    checklist = session \
        .query(Participant) \
        .filter(Participant.checklist_id == checklist_id, Participant.user_id == user_id) \
        .scalar()
    return checklist is not None


def find_for_removal(session, deleting_user_id):
    checklist = user_queries.get_selected_checklist(session, deleting_user_id)
    return session \
        .query(Participant) \
        .filter(Participant.checklist_id == checklist.id, Participant.user_id != deleting_user_id) \
        .filter(or_(Participant.deleting_user_id == None, Participant.deleting_user_id == deleting_user_id)) \
        .order_by(Participant.user_id) \
        .all()


def mark_for_removal(session, deleting_user_id, user_id):
    checklist = user_queries.get_selected_checklist(session, deleting_user_id)
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
    checklist = user_queries.get_selected_checklist(session, deleting_user_id)
    session \
        .query(Participant) \
        .filter(Participant.checklist_id == checklist.id, Participant.deleting_user_id == deleting_user_id) \
        .update({'deleting_user_id': None})
    session.commit()


def commit_removal(session, checklist_id, user_id):
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
