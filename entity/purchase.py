# coding=utf-8

from sqlalchemy import Column, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from entity.base import Base


class Purchase(Base):
    __tablename__ = 'purchases'

    id = Column(Integer, primary_key=True)
    checklist_id = Column(Integer, ForeignKey('checklists.id'))
    checklist = relationship('Checklist', backref='purchases', cascade='all, delete-orphan')
    buyer_id = Column(Integer, ForeignKey('users.id'))
    buyer = relationship('User', backref='purchases', cascade='all, delete-orphan')
    active = Column(Boolean, default=True)
    equalized = Column(Boolean, default=False)
    price = Column(Integer)

    __table_args__ = (
        UniqueConstraint('name', 'checklist_id'),
    )

    def __init__(self, checklist, buyer):
        self.checklist = checklist
        self.buyer = buyer
