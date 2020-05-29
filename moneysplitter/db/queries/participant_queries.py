from sqlalchemy import or_

from ..models import Activity, Participant
from ..queries import user_queries
from ...i18n import trans


def create(session, checklist_id, user_id):
    session.add(Participant(checklist_id, user_id))
    user = user_queries.find(session, user_id)
    session.add(Activity(trans.t('activity.new_participant', name=user.display_name()), checklist_id))
    session.commit()


def leave(session, user_id):
    checklist = user_queries.get_selected_checklist(session, user_id)
    if checklist.creator_id == user_id:
        return False

    session.query(Participant).filter(Participant.user_id == user_id, Participant.checklist == checklist).delete()
    user_queries.select_checklist(session, None, user_id)
    user = user_queries.find(session, user_id)
    session.add(Activity(trans.t('activity.leave_participant', name=user.display_name()), checklist.id))
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
    checklist_id = user_queries.get_participant_delete_id(session, deleting_user_id)
    return session \
        .query(Participant) \
        .filter(Participant.checklist_id == checklist_id, Participant.user_id != deleting_user_id) \
        .filter(or_(Participant.deleting_user_id == None, Participant.deleting_user_id == deleting_user_id)) \
        .order_by(Participant.user_id) \
        .all()


def mark_for_removal(session, deleting_user_id, user_id):
    checklist_id = user_queries.get_participant_delete_id(session, deleting_user_id)
    participant = session \
        .query(Participant) \
        .filter(Participant.user_id == user_id, Participant.checklist_id == checklist_id) \
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
    checklist_id = user_queries.get_participant_delete_id(session, deleting_user_id)
    session \
        .query(Participant) \
        .filter(Participant.checklist_id == checklist_id, Participant.deleting_user_id == deleting_user_id) \
        .update({'deleting_user_id': None})
    user_queries.set_participant_delete(session, deleting_user_id, True)
    session.commit()


def commit_removal(session, user_id):
    checklist_id = user_queries.get_participant_delete_id(session, user_id)
    participants = session \
        .query(Participant) \
        .filter(Participant.checklist_id == checklist_id, Participant.deleting_user_id == user_id) \
        .all()

    if len(participants) == 0:
        return False

    for participant in participants:
        session.delete(participant)
        session.add(Activity(trans.t('activity.kick_participant', name=participant.user.display_name()), checklist_id))

    session.commit()
    return True
