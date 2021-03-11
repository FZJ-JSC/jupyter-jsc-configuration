from jupyterhub.orm import Base

from tornado.log import app_log
from alembic.script import ScriptDirectory
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import event
from sqlalchemy import exc
from sqlalchemy import ForeignKey
from sqlalchemy import inspect
from sqlalchemy import Integer
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy import Table
from sqlalchemy import Unicode
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref
from sqlalchemy.orm import interfaces
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.expression import bindparam
from sqlalchemy.types import LargeBinary
from sqlalchemy.types import Text
from sqlalchemy.types import TypeDecorator

class TwoFAORM(Base):
    """Information for TwoFA code.
    """

    __tablename__ = 'TwoFA'
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    code = Column(Unicode(255), default='')
    generated = Column(Unicode(255), default='')
    expired = Column(Unicode(255), default='')

    def __repr__(self):
        return "<TwoFA for {}>".format(self.user_id)

    @classmethod
    def find(cls, db, user_id):
        """Find a group by user_id.
        Returns None if not found.
        """
        return db.query(cls).filter(cls.user_id == user_id).first()

    def validate_token(cls, db, user_id, code):
        """If token is valide return True, otherwise False
        """
        obj = db.query(cls).filter(cls.user_id == user_id).filter(cls.code == code).all()
        app_log.debug("Query result: {}".format(obj))
        if len(obj) > 1 or len(obj) == 0:
            return False
        return obj[0]