"""Helper class to get a database engine and to get a session."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker

engine = create_engine('postgresql://hillburn@localhost:5432/moneysplitter')
base = declarative_base(bind=engine)


def get_session():
    """Get a new db session."""
    session = scoped_session(sessionmaker(bind=engine))
    return session()
