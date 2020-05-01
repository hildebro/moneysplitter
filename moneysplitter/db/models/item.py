from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from ..db import base


class Item(base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    checklist_id = Column(Integer, ForeignKey('checklists.id', ondelete='cascade'))
    checklist = relationship('Checklist', back_populates='items')
    purchase_id = Column(Integer, ForeignKey('purchases.id', ondelete='set null'))
    purchase = relationship('Purchase', back_populates='items')
    deleting_user_id = Column(Integer, ForeignKey('users.id', ondelete='set null'))

    def __init__(self, name, checklist_id):
        self.name = name
        self.checklist_id = checklist_id

    def display_name(self):
        return self.name
