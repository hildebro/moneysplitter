from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from db import base


class Purchase(base):
    __tablename__ = 'purchases'

    id = Column(Integer, primary_key=True)
    checklist_id = Column(Integer, ForeignKey('checklists.id', ondelete='cascade'))
    checklist = relationship('Checklist', back_populates='purchases')
    buyer_id = Column(Integer, ForeignKey('users.id', ondelete='set null'))
    buyer = relationship('User', back_populates='purchases')
    items = relationship('Item', back_populates='purchase')
    active = Column(Boolean, default=True)
    equalized = Column(Boolean, default=False)
    price = Column(Integer)

    def __init__(self, buyer_id, checklist_id):
        self.buyer_id = buyer_id
        self.checklist_id = checklist_id
