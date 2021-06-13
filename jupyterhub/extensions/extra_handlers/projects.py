import asyncio
import json
import os
import subprocess
import time
import uuid
from contextlib import closing
from datetime import datetime
from datetime import timedelta

import psycopg2
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from tornado import gen
from tornado import web

from .projects_orm import ProjectSharesORM
from .projects_orm import ProjectsORM
from jupyterhub import orm
from jupyterhub.apihandlers.base import APIHandler
from jupyterhub.apihandlers.users import admin_or_self
from jupyterhub.handlers.base import BaseHandler
from jupyterhub.handlers.login import LogoutHandler
from jupyterhub.metrics import RUNNING_SERVERS
from jupyterhub.metrics import SERVER_STOP_DURATION_SECONDS
from jupyterhub.metrics import ServerStopStatus
from jupyterhub.orm import Spawner
from jupyterhub.orm import User
from jupyterhub.utils import admin_only
from jupyterhub.utils import maybe_future
from jupyterhub.utils import new_token
from jupyterhub.utils import token_authenticated
from jupyterhub.utils import url_path_join


class ProjectsAPIHandler(APIHandler):
    @token_authenticated
    async def get(self, system="", name=""):
        # List all my projects
        uuidcode = self.request.headers.get("uuidcode", "<no_uuidcode>")
        user = self.get_current_user_token()
        self.log.debug(
            "uuidcode={uuidcode} - List Projects for {owner} - {system} - {name}".format(
                uuidcode=uuidcode, owner=user.name, system=system, name=name
            )
        )
        projects = ProjectsORM.find_prettify(self.db, user.orm_user.id, system, name)
        self.write(json.dumps(projects))

    @token_authenticated
    async def post(self, system, name):
        # Create Project in database
        uuidcode = self.request.headers.get("uuidcode", "<no_uuidcode>")
        user = self.get_current_user_token()
        self.log.debug(
            "uuidcode={uuidcode} - Create Projects for {owner} - {system} - {name}".format(
                uuidcode=uuidcode, owner=user.name, system=system, name=name
            )
        )
        projects = ProjectsORM.find(self.db, user.orm_user.id, system, name)
        if projects:
            self.set_header("Content-Type", "text/plain")
            username = user.name
            self.log.info(
                f"uuidcode={uuidcode} - Project {name} on {system} from {username} already exists"
            )
            self.write(f"Project {name} on {system} already exists for {username}")
            self.set_status(409)
            return
        project_orm = ProjectsORM(user_id=user.orm_user.id, system=system, name=name)
        self.db.add(project_orm)
        self.db.commit()
        self.set_header("Content-Type", "text/plain")
        self.set_status(200)

    @token_authenticated
    async def delete(self, system, name, owner=""):
        # Delete Project in database
        uuidcode = self.request.headers.get("uuidcode", "<no_uuidcode>")
        user = self.get_current_user_token()
        if len(owner) > 0 and owner != user.name:
            # Delete myself from another project
            self.log.debug(
                "uuidcode={uuidcode} - Delete myself ({myself}) from project {owner} - {system} - {name}".format(
                    uuidcode=uuidcode,
                    myself=user.name,
                    owner=owner,
                    system=system,
                    name=name,
                )
            )
            owner_orm = self.find_user(owner)
            projects = ProjectSharesORM.find_to_delete_myself(
                self.db, user.orm_user.id, system, name, owner_orm.id
            )
            if not projects:
                self.set_status(404)
                return
            self.db.delete(projects)
            self.db.commit()
        else:
            self.log.debug(
                "uuidcode={uuidcode} - Delete Project {owner} - {system} - {name}".format(
                    uuidcode=uuidcode, owner=user.name, system=system, name=name
                )
            )
            projects = ProjectsORM.find_to_delete(
                self.db, user.orm_user.id, system, name
            )
            if not projects:
                self.set_status(404)
                return
            for project in projects:
                self.db.delete(project)
            self.db.commit()
        self.set_status(200)


class ProjectSharesAPIHandler(APIHandler):
    @token_authenticated
    async def get(self, system=""):
        # List all projects shared with me
        uuidcode = self.request.headers.get("uuidcode", "<no_uuidcode>")
        user = self.get_current_user_token()
        self.log.debug(
            "uuidcode={uuidcode} - List projects shared with {username}".format(
                uuidcode=uuidcode, username=user.name
            )
        )
        projects = ProjectSharesORM.list_my_shares(self.db, user.orm_user.id, system)
        self.set_header("Content-Type", "text/plain")
        self.write(json.dumps(projects))

    @token_authenticated
    async def post(self, system, project_name, username):
        # Add user to my project
        user = self.get_current_user_token()
        user_to_add = self.find_user(username)
        if not user_to_add:
            self.set_header("Content-Type", "text/plain")
            self.write(f"User not found {username}")
            self.set_status(404)
            return

        projects = ProjectsORM.find(self.db, user.orm_user.id, system, project_name)
        if not projects:
            self.set_header("Content-Type", "text/plain")
            username = user.name
            self.write(f"Project {project_name} on {system} not found")
            self.set_status(404)
            return
        pre_existing_share = ProjectSharesORM.find(
            self.db, user.orm_user.id, system, project_name, user_to_add.orm_user.id
        )
        if not pre_existing_share:
            share_orm = ProjectSharesORM(
                project_id=projects[0].id, shared_with=user_to_add.orm_user.id
            )
            self.db.add(share_orm)
            self.db.commit()
        self.set_header("Content-Type", "text/plain")
        self.set_status(200)

    @token_authenticated
    async def delete(self, system, project_name, username=""):
        # Delete share of project in database
        uuidcode = self.request.headers.get("uuidcode", "<no_uuidcode>")
        user = self.get_current_user_token()
        self.log.debug(
            "uuidcode={uuidcode} - Delete sharing {owner} - {system} - {project_name} - {username}".format(
                uuidcode=uuidcode,
                owner=user.name,
                system=system,
                project_name=project_name,
                username=username,
            )
        )
        if username:
            user_to_delete = self.find_user(username)
            if not user_to_delete:
                self.log.debug("uuidcode={uuidcode} - User not found")
                self.set_header("Content-Type", "text/plain")
                self.write(f"User not found {username}")
                self.set_status(404)
                return
            user_id = user_to_delete.orm_user.id
        else:
            user_id = ""
        to_delete_all = ProjectSharesORM.find_to_delete_shares(
            self.db, user.orm_user.id, system, project_name, user_id
        )
        self.log.debug(f"uuidcode={uuidcode} - To delete: {to_delete_all}")
        for to_delete in to_delete_all:
            self.db.delete(to_delete)
        self.db.commit()
        self.set_status(200)
