"""Drop and create a new database with schema."""
from db import engine, base
# noinspection PyUnresolvedReferences
from models import *

base.metadata.create_all(engine)
