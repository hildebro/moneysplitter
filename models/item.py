from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from db import base


class Item(base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    checklist_id = Column(Integer, ForeignKey('checklists.id'))
    checklist = relationship('Checklist', backref='items', cascade='all, delete-orphan', single_parent=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id', ondelete='SET NULL'))
    purchase = relationship('Purchase', backref='items')

    __table_args__ = (
        UniqueConstraint('name', 'checklist_id'),
    )

    def __init__(self, name, checklist_id):
        self.name = name
        self.checklist_id = checklist_id
