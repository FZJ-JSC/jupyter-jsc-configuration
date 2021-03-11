import requests
import os
from contextlib import closing
from jupyterhub.apihandlers.base import APIHandler
from jupyterhub.utils import url_path_join

import uuid
import requests
import json

from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from contextlib import closing

from jupyterhub.orm import Spawner
from jupyterhub.utils import url_path_join
from jupyterhub.apihandlers.base import APIHandler
from jupyterhub.handlers.base import BaseHandler
from jupyterhub.apihandlers.users import admin_or_self
from tornado import gen, web

import asyncio
import json
import os
import psycopg2
import requests
import subprocess
import time
import uuid

from contextlib import closing
from datetime import datetime, timedelta
from tornado import gen, web

from jupyterhub.apihandlers.base import APIHandler
from jupyterhub.handlers.base import BaseHandler
from jupyterhub.handlers.login import LogoutHandler
from jupyterhub.utils import maybe_future, admin_only, new_token
from jupyterhub import orm

from jupyterhub.metrics import RUNNING_SERVERS, SERVER_STOP_DURATION_SECONDS, ServerStopStatus
from jupyterhub.apihandlers.users import admin_or_self

from .twoFA_orm import TwoFAORM
from .twoFA_mail import send_user_mail, send_user_mail_delete
from .twoFA_unity import delete_user_2fa, add_user_2fa

class TwoFAHandler(BaseHandler):
    async def get(self):
        user = self.current_user
        html = await self.render_template(
                    '2FA.html',
                    user=user)
        self.finish(html)

class TwoFAAPIHandler(APIHandler):
    @web.authenticated
    async def post(self):
        user = self.current_user

        uuidcode = uuid.uuid4().hex
        self.log.info("uuidcode={} - action=request2fa - {} will receive an email with a generated code".format(uuidcode, user.name))
        send2fa_config_path = os.environ.get("SEND2FA_CONFIG_PATH", None)
        if not send2fa_config_path:
            self.log.error("Please define $SEND2FA_CONFIG_PATH environment variable.")
            send2fa_config = {}
        else:
            with open(send2fa_config_path, 'r') as f:
                send2fa_config = json.load(f)

        code = uuid.uuid4().hex
        generated = datetime.now()
        unit = ''
        value = ''
        if send2fa_config.get('timedelta', {}).get('unit', 'default') == 'default' or send2fa_config.get('timedelta', {}).get('unit', 'default') == 'hours':
            expired = generated + timedelta(hours=send2fa_config.get('timedelta', {}).get('value', 2))
            unit = 'hours'
            value = send2fa_config.get('timedelta', {}).get('value', 2)
        elif send2fa_config.get('timedelta', {}).get('unit', 'default') == 'days':
            expired = generated + timedelta(days=send2fa_config.get('timedelta', {}).get('value', 1))
            unit = 'days'
            value = send2fa_config.get('timedelta', {}).get('value', 1)
        elif send2fa_config.get('timedelta', {}).get('unit', 'default') == 'minutes':
            expired = generated + timedelta(minutes=send2fa_config.get('timedelta', {}).get('value', 30))
            unit = 'minutes'
            value = send2fa_config.get('timedelta', {}).get('value', 30)
        else:
            expired = generated + timedelta(hours=2)
            unit = 'hours'
            value = 2
        generated_s = generated.strftime('%Y-%m-%d-%H:%M:%S')
        expired_s = expired.strftime('%Y-%m-%d-%H:%M:%S')

        twofa_orm = TwoFAORM.find(self.db, user_id=user.id)
        if twofa_orm is None:
            twofa_orm = TwoFAORM(user_id=user.id, code=code, generated=generated_s, expired=expired_s)
            self.db.add(twofa_orm)
        else:
            twofa_orm.code = code
            twofa_orm.generated = generated_s
            twofa_orm.expired = expired_s
        self.db.commit()

        url = "https://" + url_path_join(self.request.host, self.hub.base_url, "/")
        send_user_mail(user.name, code, unit, str(value), url)
        self.set_header('Content-Type', 'text/plain')
        self.set_status(200)

    @web.authenticated
    async def delete(self):
        user = self.current_user
        if user:
            try:
                uuidcode = uuid.uuid4().hex
                self.log.info("uuidcode={} - action=delete2faopt - Remove User from 2FA optional group: {}".format(uuidcode, user.name))

                self.log.debug("uuidcode={} - Delete user from group via ssh to Unity VM".format(uuidcode))
                delete_user_2fa(user.name)

                self.log.debug("uuidcode={} - Send user a confirmation mail".format(uuidcode))
                send_user_mail_delete(user.name)

                self.set_header('Content-Type', 'text/plain')
                self.set_status(204)
            except:
                self.log.exception("Bugfix required")
                self.set_status(500)
                self.write("Something went wrong. Please contact support to deactivate two factor authentication.")
                self.flush()
        else:
            self.set_header('Content-Type', 'text/plain')
            self.set_status(404)
            raise web.HTTPError(404, 'User not found. Please logout, login and try again. If this does not help contact support.')


class TwoFACodeHandler(BaseHandler):
    @web.authenticated
    async def get(self, code):
        uuidcode = uuid.uuid4().hex
        user = self.current_user
        self.log.info("uuidcode={} - action=activate2facode - user={}".format(uuidcode, user.name))
        result = TwoFAORM.validate_token(TwoFAORM, self.db, user.id, code)
        if result:
            self.db.delete(result)
            self.db.commit()

            expired_s = result.expired
            expired = datetime.strptime(expired_s, '%Y-%m-%d-%H:%M:%S')
            if expired > datetime.now():
                try:
                    self.log.debug("uuidcode={} - Add user to 2FA group in unity".format(uuidcode))
                    add_user_2fa(user.name)
                    code_success=True
                    code_header="2FA activation successful"
                    code_text="You'll be able to add a second factor the next time you log in."
                except:
                    self.log.exception("uuidcode={} - Unknown Error in Code2FA".format(uuidcode))
                    code_success=False
                    code_header="2FA activation failed"
                    code_text="Please contact support to activate 2-Factor Authentication."
            else:
                self.log.error("uuidcode={} - Expired code. Now: {} - Expired: {}".format(uuidcode, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), expired.strftime('%Y-%m-%d %H:%M:%S')))
                code_success=False
                code_header="2FA activation failed"
                code_text="The link is expired since {}. Please request a new one.".format(expired.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            self.log.error("uuidcode={} - There is no such token {}".format(uuidcode, code))
            code_success=False
            code_header="2FA activation failed"
            code_text="Please contact support to activate 2-Factor Authentication."

        html = await self.render_template(
                '2FA.html',
                user=user,
                code=True,
                code_success=code_success,
                code_header=code_header,
                code_text=code_text)
        self.finish(html)
        return
