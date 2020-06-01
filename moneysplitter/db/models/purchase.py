import datetime

from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from ..db import base


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
    leftover_price = Column(Integer, nullable=True)
    distributions = relationship('PurchaseDistribution', back_populates='purchase')
    created_at = Column(DateTime, nullable=False)

    def __init__(self, buyer_id, checklist_id):
        self.buyer_id = buyer_id
        self.checklist_id = checklist_id
        self.created_at = datetime.datetime.now()

    def get_price(self):
        return "{:.2f}".format(self.price / 100.0)

    def set_price(self, price):
        self.price = price * 100.0
        self.leftover_price = price * 100.0

    def get_leftover_price(self):
        return "{:.2f}".format(self.leftover_price / 100.0)

    def set_leftover_price(self, leftover_price):
        self.leftover_price = leftover_price * 100.0

    def display_name(self):
        formatted_time = self.created_at.isoformat(' ', timespec='minutes')
        return f'[{formatted_time}] {self.buyer.username} - {self.get_price()}'
