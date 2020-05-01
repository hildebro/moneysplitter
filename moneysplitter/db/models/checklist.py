from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from ..db import base


class Checklist(base):
    __tablename__ = 'checklists'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    creator_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    creator = relationship('User', back_populates='created_checklists')
    participants = relationship('Participant', back_populates='checklist')
    items = relationship('Item', back_populates='checklist')
    purchases = relationship('Purchase', back_populates='checklist')

    __table_args__ = (
        UniqueConstraint('name', 'creator_id'),
    )

    def __init__(self, name, creator):
        self.name = name
        self.creator = creator
