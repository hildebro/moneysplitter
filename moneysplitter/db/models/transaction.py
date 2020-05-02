from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from ..db import base


class Transaction(base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    checklist_id = Column(Integer, ForeignKey('checklists.id', ondelete='cascade'))
    checklist = relationship('Checklist', foreign_keys=checklist_id)
    giver_id = Column(Integer, ForeignKey('users.id', ondelete='set null'))
    giver = relationship('User', foreign_keys=giver_id)
    receiver_id = Column(Integer, ForeignKey('users.id', ondelete='set null'))
    receiver = relationship('User', foreign_keys=receiver_id)
    amount = Column(Integer)

    def __init__(self, checklist_id, giver_id, receiver_id, amount):
        self.checklist_id = checklist_id
        self.giver_id = giver_id
        self.receiver_id = receiver_id
        self.amount = amount

    def display_name(self):
        return f'{self.giver.display_name()} owes {self.receiver.display_name()} {self.get_amount()}'

    def get_amount(self):
        return self.amount / 100.0
