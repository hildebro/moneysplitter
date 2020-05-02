from sqlalchemy import func

from ..models import Checklist, Participant, Purchase
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


def find(session, checklist_id):
    return session.query(Checklist).filter(Checklist.id == checklist_id).one()


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


def find_participants(session, checklist_id):
    return session.query(Participant).filter(Participant.checklist_id == checklist_id).all()


def find_by_purchase(session, purchase_id):
    return session.query(Checklist).filter(Checklist.purchases.any(Purchase.id == purchase_id)).one()


def is_creator(session, checklist_id, user_id):
    checklist = session \
        .query(Checklist) \
        .filter(Checklist.id == checklist_id).one()
    return checklist.creator_id == user_id


def is_participant(session, checklist_id, user_id):
    checklist = session \
        .query(Participant) \
        .filter(Participant.checklist_id == checklist_id, Participant.user_id == user_id) \
        .scalar()
    return checklist is not None


def delete(session, checklist_id, user_id):
    if not is_creator(session, checklist_id, user_id):
        raise Exception

    session.query(Checklist).filter(Checklist.id == checklist_id).delete()
    session.commit()


def join(session, checklist_id, user_id):
    session.add(Participant(checklist_id, user_id))
    session.commit()


def count_checklists(session, user_id):
    count = session \
        .query(func.count(Participant.user_id)) \
        .filter(Participant.user_id == user_id) \
        .scalar()
    return count
