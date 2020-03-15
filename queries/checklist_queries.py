from sqlalchemy import func

from db import get_session
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


def find_by_participant(user_id):
    session = get_session()
    checklists = session \
        .query(Checklist) \
        .filter(Checklist.participants.any(id=user_id)) \
        .all()
    session.close()
    return checklists


def find_by_creator(user_id):
    session = get_session()
    checklists = session \
        .query(Checklist) \
        .filter(Checklist.creator_id == user_id) \
        .all()
    session.close()
    return checklists


def find_participants(checklist_id):
    session = get_session()
    participants = session.query(User).filter(User.joined_checklists.any(Checklist.id == checklist_id)).all()
    session.close()
    return participants


def is_creator(checklist_id, user_id):
    session = get_session()
    checklist = session \
        .query(Checklist) \
        .filter(Checklist.id == checklist_id).one()
    session.close()
    return checklist.creator_id == user_id


def is_participant(session, checklist_id, user_id):
    checklist = session \
        .query(Checklist) \
        .filter(Checklist.id == checklist_id, Checklist.participants.any(User.id == user_id)).scalar()
    return checklist is not None


def delete(session, checklist_id, user_id):
    if not is_creator(checklist_id, user_id):
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
