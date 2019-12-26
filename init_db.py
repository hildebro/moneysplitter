# noinspection PyUnresolvedReferences
import entity.checklist
# noinspection PyUnresolvedReferences
import entity.item
# noinspection PyUnresolvedReferences
import entity.purchase
# noinspection PyUnresolvedReferences
import entity.user

from entity.base import engine, Base

Base.metadata.create_all(engine)
