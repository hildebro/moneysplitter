from . import user_queries
from .. import Activity


def find_by_checklist(session, user_id):
    checklist = user_queries.get_selected_checklist(session, user_id)
    return session.query(Activity) \
        .filter(Activity.checklist_id == checklist.id) \
        .order_by(Activity.created_at.desc()) \
        .limit(20) \
        .all()
