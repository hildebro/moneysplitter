from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint, Table
from sqlalchemy.orm import relationship

from entity.base import Base

checklist_participants = Table('checklist_participants', Base.metadata,
                               Column('checklist_id', Integer, ForeignKey('checklists.id')),
                               Column('user_id', Integer, ForeignKey('users.id'))
                               )


class Checklist(Base):
    __tablename__ = 'checklists'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    creator_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    creator = relationship('User', backref='created_checklists')
    participants = relationship('User', secondary='checklist_participants', backref='joined_checklists')

    __table_args__ = (
        UniqueConstraint('name', 'creator_id'),
    )

    def __init__(self, name, creator):
        self.name = name
        self.creator = creator
