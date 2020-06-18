import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from ..db import base


class Activity(base):
    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False)
    checklist_id = Column(Integer, ForeignKey('checklists.id', ondelete='cascade'))
    checklist = relationship('Checklist')
    message = Column(String)

    def __init__(self, message, checklist_id):
        self.created_at = datetime.datetime.now()
        self.message = message
        self.checklist_id = checklist_id

    def display_name(self):
        formatted_time = self.created_at.isoformat(' ', timespec='minutes')
        return f'*[{formatted_time}]*\n{self.message}'
