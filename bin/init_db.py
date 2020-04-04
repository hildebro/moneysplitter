"""Drop and create a new database with schema."""
from moneysplitter.db.db import engine, base
# noinspection PyUnresolvedReferences
from moneysplitter.db.models import *

base.metadata.create_all(engine)
