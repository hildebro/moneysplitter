from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from ..db import base


class UserSettings(base):
    __tablename__ = 'user_settings'

    user_id = Column(Integer, ForeignKey('users.id', ondelete='cascade'), primary_key=True)
    checklist_id = Column(Integer, ForeignKey('checklists.id', ondelete='set null'), nullable=True)
    selected_checklist = relationship('Checklist')

    def __init__(self, user_id):
        self.user_id = user_id
