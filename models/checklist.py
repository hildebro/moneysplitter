from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint, Table
from sqlalchemy.orm import relationship

from db import base

checklist_participants = Table('checklist_participants', base.metadata,
                               Column('checklist_id', Integer, ForeignKey('checklists.id', ondelete='cascade')),
                               Column('user_id', Integer, ForeignKey('users.id', ondelete='cascade'))
                               )


class Checklist(base):
    __tablename__ = 'checklists'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    creator_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    creator = relationship('User', back_populates='created_checklists')
    participants = relationship('User', secondary='checklist_participants', back_populates='joined_checklists')
    items = relationship('Item', back_populates='checklist')
    purchases = relationship('Purchase', back_populates='checklist')

    __table_args__ = (
        UniqueConstraint('name', 'creator_id'),
    )

    def __init__(self, name, creator):
        self.name = name
        self.creator = creator
