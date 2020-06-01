import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from ..db import base


class PurchaseDistribution(base):
    __tablename__ = 'purchase_distributions'

    id = Column(Integer, primary_key=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id', ondelete='cascade'))
    purchase = relationship('Purchase', foreign_keys=purchase_id, back_populates='distributions')
    user_id = Column(Integer, ForeignKey('users.id', ondelete='set null'))
    user = relationship('User', foreign_keys=user_id)
    amount = Column(Integer)
    created_at = Column(DateTime, nullable=False)

    def __init__(self, purchase_id, user_id, amount):
        self.purchase_id = purchase_id
        self.user_id = user_id
        self.amount = amount
        self.created_at = datetime.datetime.now()

    def display_name(self):
        return f'{self.user.display_name()} - {self.get_amount()}'

    def get_amount(self):
        return "{:.2f}".format(self.amount / 100.0)
