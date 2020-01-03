from db import get_session
from models import User
from models.checklist import Checklist
from queries import user_queries


def exists(creator_id, checklist_name):
    session = get_session()
    checklist_query = session \
        .query(Checklist) \
        .filter(Checklist.creator_id == creator_id,
                Checklist.name == checklist_name)
    checklist_count = checklist_query.count() > 0
    session.close()
    return checklist_count


def create(creator_id, checklist_name):
    creator = user_queries.find(creator_id)
    checklist = Checklist(checklist_name, creator)
    checklist.participants = [creator]
    session = get_session()
    session.add(checklist)
    session.commit()
    session.close()


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


def is_participant(checklist_id, user_id):
    session = get_session()
    checklist = session \
        .query(Checklist) \
        .filter(Checklist.id == checklist_id, Checklist.participants.any(User.id == user_id)).scalar()
    session.close()
    return checklist is not None


def delete(checklist_id, user_id):
    if not is_creator(checklist_id, user_id):
        raise Exception

    session = get_session()
    session.query(Checklist).filter(Checklist.id == checklist_id).delete()
    session.commit()
    session.close()


def join(checklist_id, user_id):
    user = user_queries.find(user_id)
    session = get_session()
    checklist = session.query(Checklist).filter(Checklist.id == checklist_id).one()
    checklist.participants.append(user)
    session.commit()
    session.close()
