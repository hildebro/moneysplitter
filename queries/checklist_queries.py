from sqlalchemy import func

from models import User
from models.checklist import Checklist
from queries import user_queries


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
    checklist.participants = [creator]
    session.add(checklist)
    session.commit()


def find_by_participant(session, user_id):
    checklists = session \
        .query(Checklist) \
        .filter(Checklist.participants.any(id=user_id)) \
        .all()
    return checklists


def find_by_creator(session, user_id):
    checklists = session \
        .query(Checklist) \
        .filter(Checklist.creator_id == user_id) \
        .all()
    return checklists


def find_participants(session, checklist_id):
    participants = session.query(User).filter(User.joined_checklists.any(Checklist.id == checklist_id)).all()
    return participants


def is_creator(session, checklist_id, user_id):
    checklist = session \
        .query(Checklist) \
        .filter(Checklist.id == checklist_id).one()
    return checklist.creator_id == user_id


def is_participant(session, checklist_id, user_id):
    checklist = session \
        .query(Checklist) \
        .filter(Checklist.id == checklist_id, Checklist.participants.any(User.id == user_id)).scalar()
    return checklist is not None


def delete(session, checklist_id, user_id):
    if not is_creator(session, checklist_id, user_id):
        raise Exception

    session.query(Checklist).filter(Checklist.id == checklist_id).delete()
    session.commit()


def join(session, checklist_id, user_id):
    user = user_queries.find(session, user_id)
    checklist = session.query(Checklist).filter(Checklist.id == checklist_id).one()
    checklist.participants.append(user)
    session.commit()


def count_checklists(session, user_id):
    count = session.query(func.count(Checklist.id)).filter(Checklist.participants.any(User.id == user_id)).scalar()
    return count
