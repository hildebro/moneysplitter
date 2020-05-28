import datetime

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship

from ..db import base


class User(base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    created_checklists = relationship('Checklist', back_populates='creator')
    participants = relationship('Participant', back_populates='user', foreign_keys='Participant.user_id')
    deleting_participants = relationship('Participant', back_populates='deleting_user',
                                         foreign_keys='Participant.deleting_user_id')
    purchases = relationship('Purchase', back_populates='buyer')
    created_at = Column(DateTime, nullable=False)

    def __init__(self, external_id, username, first_name, last_name):
        self.id = external_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.created_at = datetime.datetime.now()

    def display_name(self):
        # todo first available thing: fullname, first name, username
        return self.username
