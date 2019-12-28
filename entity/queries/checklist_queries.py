from entity.base import Session
from entity.checklist import Checklist
from entity.queries import user_queries


def exists(creator_id, checklist_name):
    session = Session()
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
    session = Session()
    session.add(checklist)
    session.commit()
    session.close()


def find_by_participant(user_id):
    session = Session()
    checklists = session \
        .query(Checklist) \
        .filter(Checklist.participants.any(id=user_id)) \
        .all()
    session.close()
    return checklists


def is_creator(checklist_id, user_id):
    session = Session()
    checklist = session \
        .query(Checklist) \
        .filter(Checklist.id == checklist_id).one()
    session.close()
    return checklist.creator_id == user_id


def delete(checklist_id, user_id):
    if not is_creator(checklist_id, user_id):
        raise Exception

    session = Session()
    session.query(Checklist).filter(Checklist.id == checklist_id).delete()
    session.commit()
    session.close()
