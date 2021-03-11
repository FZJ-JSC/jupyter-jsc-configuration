from jupyterhub.orm import Base, User

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

class ProjectsORM(Base):
    """Information about projects.
    """

    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    system = Column(Unicode(255), default='')
    name = Column(Unicode(255), default='')

    def __repr__(self):
        return "<Project {}: {} {} {}>".format(self.id, self.user_id, self.system, self.name)

    @classmethod
    def find_to_delete(cls, db, user_id, system, name):
        """Finds projects by id.
        Returns None if not found.
        """
        if system:
            if name:
                query = db.query(cls, ProjectSharesORM, User).filter(cls.user_id == user_id).filter(cls.system == system).filter(cls.name == name).filter(cls.id == ProjectSharesORM.project_id).filter(User.id == ProjectSharesORM.shared_with).all()
                query = [x[0] for x in query]
            else:
                query = db.query(cls).filter(cls.user_id == user_id).filter(cls.system == system).all()
        else:
            query = db.query(cls).filter(cls.user_id == user_id).all()
        return query

    @classmethod
    def find(cls, db, user_id, system, name):
        """Finds projects by id.
        Returns None if not found.
        """
        if system:
            if name:
                query = db.query(cls, ProjectSharesORM, User).filter(cls.user_id == user_id).filter(cls.system == system).filter(cls.name == name).filter(cls.id == ProjectSharesORM.project_id).filter(User.id == ProjectSharesORM.shared_with).all()
                return [x[0] for x in query]
            else:
                query = db.query(cls).filter(cls.user_id == user_id).filter(cls.system == system).all()
                return query
        else:
            query = db.query(cls).filter(cls.user_id == user_id).all()
            return query

    @classmethod
    def find_prettify(cls, db, user_id, system, name):
        """Finds projects by id.
        Returns None if not found.
        """
        if system:
            if name:
                query = db.query(cls, ProjectSharesORM, User).filter(cls.user_id == user_id).filter(cls.system == system).filter(cls.name == name).filter(cls.id == ProjectSharesORM.project_id).filter(User.id == ProjectSharesORM.shared_with).all()
                return [x[2].name for x in query]
            else:
                query = db.query(cls).filter(cls.user_id == user_id).filter(cls.system == system).all()
                return [x.name for x in query]
        else:
            query = db.query(cls).filter(cls.user_id == user_id).all()
            return [(x.system, x.name) for x in query]

class ProjectSharesORM(Base):
    __tablename__ = 'project_shares'

    id = Column(Integer, primary_key=True)

    project_id = Column(Integer, ForeignKey('projects.id', ondelete='CASCADE'), default='')
    shared_with = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), default='')

    def __repr__(self):
        return "<ProjectShare {}: {} - {}>".format(self.id, self.project_id, self.shared_with)

    @classmethod
    def find_to_delete_shares(cls, db, owner_id, system, pname, user_id):
        if user_id:
            query = db.query(cls, ProjectsORM).filter(ProjectsORM.user_id == owner_id).filter(ProjectsORM.system == system).filter(ProjectsORM.name == pname).filter(ProjectsORM.id == cls.project_id).filter(cls.shared_with == user_id).all()
        else:
            query = db.query(cls, ProjectsORM).filter(ProjectsORM.user_id == owner_id).filter(ProjectsORM.system == system).filter(ProjectsORM.name == pname).filter(ProjectsORM.id == cls.project_id).all()
        return [x[0] for x in query]

    @classmethod
    def find_to_delete_myself(cls, db, user_id, system, pname, owner_id):
        query = db.query(cls, ProjectsORM).filter(cls.shared_with == user_id).filter(cls.project_id == ProjectsORM.id).filter(ProjectsORM.system == system).filter(ProjectsORM.name == pname).filter(ProjectsORM.user_id == owner_id).all()
        return [x[0] for x in query]

    @classmethod
    def list_my_shares(cls, db, user_id, system):
        if system:
            query = db.query(cls, ProjectsORM).filter(cls.shared_with == user_id).filter(cls.project_id == ProjectsORM.id).filter(ProjectsORM.system == system).all()
            ret = [x[1].name for x in query]
        else:
            query = db.query(cls, ProjectsORM).filter(cls.shared_with == user_id).filter(cls.project_id == ProjectsORM.id).all()
            ret = [(x[1].system, x[1].name) for x in query]
        return ret

    @classmethod
    def find(cls, db, owner_id, system, name, user_id):
        query = db.query(cls, ProjectsORM).filter(ProjectsORM.user_id == owner_id).filter(ProjectsORM.system == system).filter(ProjectsORM.name == name).filter(ProjectsORM.id == cls.project_id).filter(cls.shared_with == user_id).all()
        return [x[0] for x in query]

