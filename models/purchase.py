from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from db import base


class Purchase(base):
    __tablename__ = 'purchases'

    id = Column(Integer, primary_key=True)
    checklist_id = Column(Integer, ForeignKey('checklists.id'))
    checklist = relationship('Checklist', backref='purchases', cascade='all, delete-orphan', single_parent=True)
    buyer_id = Column(Integer, ForeignKey('users.id'))
    buyer = relationship('User', backref='purchases', cascade='all, delete-orphan', single_parent=True)
    active = Column(Boolean, default=True)
    equalized = Column(Boolean, default=False)
    price = Column(Integer)

    def __init__(self, checklist, buyer):
        self.checklist = checklist
        self.buyer = buyer
