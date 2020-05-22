from ..models import Checklist, Participant
from ..queries import user_queries


def exists(session, creator_id, checklist_name):
    checklist_query = session \
        .query(Checklist) \
        .filter(Checklist.creator_id == creator_id,
                Checklist.name == checklist_name)
    checklist_count = checklist_query.count() > 0
    return checklist_count


def create(session, creator_id, checklist_name):
    creator = user_queries.find(session, creator_id)
    checklist = Checklist(checklist_name, creator)
    session.add(checklist)
    session.flush()
    session.add(Participant(checklist.id, creator_id))
    session.commit()

    return checklist


def find_by_participant(session, user_id):
    checklists = session \
        .query(Checklist) \
        .filter(Checklist.participants.any(Participant.user_id == user_id)) \
        .all()
    return checklists


def find_by_creator(session, user_id):
    checklists = session \
        .query(Checklist) \
        .filter(Checklist.creator_id == user_id) \
        .all()
    return checklists


def delete(session, checklist_id):
    session.query(Checklist).filter(Checklist.id == checklist_id).delete()
    session.commit()
