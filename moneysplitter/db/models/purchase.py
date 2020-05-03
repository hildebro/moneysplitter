from sqlalchemy import Column, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from ..db import base
from ...i18n import trans


class Purchase(base):
    __tablename__ = 'purchases'

    id = Column(Integer, primary_key=True)
    checklist_id = Column(Integer, ForeignKey('checklists.id', ondelete='cascade'))
    checklist = relationship('Checklist', back_populates='purchases')
    buyer_id = Column(Integer, ForeignKey('users.id', ondelete='set null'))
    buyer = relationship('User', back_populates='purchases')
    items = relationship('Item', back_populates='purchase')
    written_off = Column(Boolean, default=False, nullable=False)
    in_progress = Column(Boolean, default=True, nullable=False)
    price = Column(Integer, nullable=True)

    def __init__(self, buyer_id, checklist_id):
        self.buyer_id = buyer_id
        self.checklist_id = checklist_id

    def get_price(self):
        return self.price / 100.0

    def set_price(self, price):
        self.price = price * 100.0

    def display_name(self):
        item_names = ', '.join(map(lambda item: item.name, self.items))
        return trans.t('purchase.log.list', name=self.buyer.username, price=self.get_price(), items=item_names)
