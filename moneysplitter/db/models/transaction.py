from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from ..db import base
from ...i18n import trans


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
    payoff_user_id = Column(Integer, ForeignKey('users.id', ondelete='set null'))

    def __init__(self, checklist_id, giver_id, receiver_id, amount):
        self.checklist_id = checklist_id
        self.giver_id = giver_id
        self.receiver_id = receiver_id
        self.amount = amount

    def identifier(self):
        return self.id

    def display_name(self, user_id=None):
        if user_id is None:
            trans_key = 'transaction.display.default'
        elif self.giver_id == user_id:
            trans_key = 'transaction.display.giver'
        elif self.receiver_id == user_id:
            trans_key = 'transaction.display.receiver'
        else:
            raise ValueError('user_id must be None or involved in the transaction')

        return trans.t(trans_key, giver=self.giver.display_name(), receiver=self.receiver.display_name(),
                       amount=self.get_amount())

    def get_amount(self):
        return self.amount / 100.0
