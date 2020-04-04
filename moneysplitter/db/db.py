"""Helper class to get a database engine and to get a session."""
from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker

engine = create_engine('postgresql://postgres@localhost:5432/moneysplitter')
base = declarative_base(bind=engine)


def get_session():
    """Get a new db session."""
    session = scoped_session(sessionmaker(bind=engine))
    return session


def session_wrapper(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = get_session()
        try:
            value = func(session, *args, **kwargs)
            return value
        except Exception:
            raise
        finally:
            session.close()

    return wrapper
