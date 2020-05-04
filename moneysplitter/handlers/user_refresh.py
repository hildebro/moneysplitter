from ..db import session_wrapper, user_queries


@session_wrapper
def callback(session, update, context):
    user_queries.refresh(session, update.message.from_user)
