# coding=utf-8

from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from entity.base import Base

class Checklist(Base):
    __tablename__ = 'checklists'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    creator_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    creator = relationship('User', backref='checklists')

    __table_args__ = (
        UniqueConstraint('name', 'creator_id'),
    )

    def __init__(self, name, creator):
        self.name = name
        self.creator = creator

