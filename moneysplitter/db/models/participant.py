from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from ..db import base


class Participant(base):
    __tablename__ = 'checklist_participants'

    checklist_id = Column(Integer, ForeignKey('checklists.id', ondelete='cascade'), primary_key=True)
    checklist = relationship('Checklist', foreign_keys=checklist_id)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='cascade'), primary_key=True)
    user = relationship('User', foreign_keys=user_id)
    deleting_user_id = Column(Integer, ForeignKey('users.id', ondelete='set null'))
    deleting_user = relationship('User', foreign_keys=deleting_user_id)

    def __init__(self, checklist_id, user_id):
        self.checklist_id = checklist_id
        self.user_id = user_id

    def identifier(self):
        # participants should only ever be used in a context where the checklist is known. so user_id on its own is fine
        return self.user_id

    def display_name(self):
        return self.user.display_name()