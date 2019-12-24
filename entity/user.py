# coding=utf-8

from sqlalchemy import Column, String, Integer

from entity.base import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)

    def __init__(self, username, first_name, last_name):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    def getDisplayName():
        # todo first available thing: fullname, first name, username
        return self.username

