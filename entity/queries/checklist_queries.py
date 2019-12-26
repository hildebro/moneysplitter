from entity.base import Session
from entity.checklist import Checklist


def find_by_participant(user_id):
    session = Session()
    checklists = session \
        .query(Checklist) \
        .filter(Checklist.participants.any(id=user_id)) \
        .all()
    session.close()
    return checklists
