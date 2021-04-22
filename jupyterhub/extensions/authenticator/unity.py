import copy
import json
import os
import re
import time
import uuid
from contextlib import closing
from datetime import datetime
from subprocess import PIPE
from subprocess import Popen

import requests
from oauthenticator.generic import GenericOAuthenticator
from tornado.httpclient import HTTPClientError
from tornado.httpclient import HTTPRequest
from traitlets import Unicode

from jupyterhub import orm
from jupyterhub.handlers.login import LogoutHandler
from jupyterhub.jupyterjsc.utils.partitions import get_default_partitions
from jupyterhub.jupyterjsc.utils.vo import get_vos


def get_hpc_accounts_via_ssh(username, log=None):
    ssh_key = os.environ.get("GET_HPC_ACCOUNTS_SSH_KEY")
    ssh_user = os.environ.get("GET_HPC_ACCOUNTS_SSH_USER")
    ssh_host = os.environ.get("GET_HPC_ACCOUNTS_SSH_HOST")
    if username.endswith("@fz-juelich.de"):
        username = username[: -len("@fz-juelich.de")]
    cmd = [
        "/usr/bin/ssh",
        "-oLogLevel=ERROR",
        "-oStrictHostKeyChecking=no",
        "-oUserKnownHostsFile=/dev/null",
        "-i",
        f"{ssh_key}",
        f"{ssh_user}@{ssh_host}",
        f",{username}",
    ]
    p = Popen(cmd, stderr=PIPE, stdout=PIPE)
    outb, errb = p.communicate(
        timeout=int(os.environ.get("GET_HPC_ACCOUNTS_SSH_TIMEOUT", "3"))
    )
    out = outb.decode("utf-8")
    # err = errb.decode("utf-8")
    return_code = p.returncode
    list_out = []
    try:
        if return_code == 0 and out:
            list_out = out.split()
    except:
        if log:
            log.exception("Could not check for hpc_accounts")
        list_out = []
    return list_out


class UnityOAuthenticator(GenericOAuthenticator):
    tokeninfo_url = Unicode(
        config=True,
        help="""The url retrieving information about the access token""",
    )

    def spawnable(self, system):
        maintenance_path = os.environ.get("MAINTENANCE_PATH")
        with open(maintenance_path, "r") as f:
            maintenance_list = json.load(f)
        if system in maintenance_list:
            return False
        else:
            return True

    async def refresh_user(self, user, handler, force=False):
        ret = False
        auth_state = await user.get_auth_state()
        timestamp = int(time.time()) + int(
            os.environ.get("UNITY_REFRESH_THRESHOLD", "600")
        )
        if force or timestamp >= int(auth_state.get("exp", timestamp)):
            try:
                refresh_timer = handler.statsd.timer("login.refresh").start()
                refresh_token_save = auth_state.get("refresh_token", None)
                self.log.debug(
                    f"Refresh {user.name} authentication. Rest time: {timestamp}"
                )
                if not refresh_token_save:
                    self.log.debug(f"Auth state has no refresh token {auth_state}")
                    return False
                http_client = self.http_client()
                params = {
                    "refresh_token": auth_state.get("refresh_token"),
                    "grant_type": "refresh_token",
                    "scope": " ".join(self.scope),
                }

                headers = self._get_headers()
                try:
                    token_resp_json = await self._get_token(
                        http_client, headers, params
                    )
                except HTTPClientError:
                    self.log.exception("Could not receive new access token.")
                    return False

                user_data_resp_json = await self._get_user_data(
                    http_client, token_resp_json
                )

                if callable(self.username_key):
                    name = self.username_key(user_data_resp_json)
                else:
                    name = user_data_resp_json.get(self.username_key)
                    if not name:
                        self.log.error(
                            "OAuth user contains no key %s: %s",
                            self.username_key,
                            user_data_resp_json,
                        )
                        return

                    if not token_resp_json.get("refresh_token", None):
                        token_resp_json["refresh_token"] = refresh_token_save
                    authentication = {
                        "auth_state": self._create_auth_state(
                            token_resp_json, user_data_resp_json
                        )
                    }
                    ret = await self.run_post_auth_hook(handler, authentication)
                refresh_timer.stop(send=True)
                handler.statsd.timing("login.refresh.time", refresh_timer.ms)
            except:
                self.log.exception(
                    "Refresh of user's {name} access token failed".format(
                        name=user.name
                    )
                )
                ret = False
        else:
            ret = True
        return ret


async def post_auth_hook(authenticator, handler, authentication):
    http_client = authenticator.http_client()
    access_token = authentication["auth_state"]["access_token"]
    url = os.environ.get("TOKENINFO_URL")
    headers = {
        "Accept": "application/json",
        "User-Agent": "JupyterHub",
        "Authorization": f"Bearer {access_token}",
    }
    req = HTTPRequest(url, method="GET", headers=headers)
    resp = await http_client.fetch(req)
    resp_json = json.loads(resp.body.decode("utf8", "replace"))
    authentication["auth_state"]["exp"] = resp_json.get("exp")
    authentication["auth_state"]["last_login"] = datetime.now().strftime(
        "%H:%M:%S %Y-%m-%d"
    )

    used_authenticator = (
        authentication["auth_state"]
        .get("oauth_user", {})
        .get("used_authenticator_attr", "unknown")
    )
    hpc_infos_via_unity = str(
        len(
            authentication["auth_state"]
            .get("oauth_user", {})
            .get("hpc_infos_attribute", [])
        )
        > 0
    ).lower()
    handler.statsd.incr(f"login.authenticator.{used_authenticator}")
    handler.statsd.incr(f"login.hpc_infos_via_unity.{hpc_infos_via_unity}")

    username = authentication.get("name", "unknown")
    admin = authentication.get("admin", False)
    vo_active, vo_available = get_vos(
        authentication["auth_state"], username, admin=admin
    )
    authentication["auth_state"]["vo_active"] = vo_active
    authentication["auth_state"]["vo_available"] = vo_available

    if not hpc_infos_via_unity:
        hpc_list = get_hpc_accounts_via_ssh(username, authenticator.log)
        if hpc_list:
            authentication["auth_state"]["oauth_user"]["hpc_infos_attribute"] = hpc_list

    default_partitions = get_default_partitions()
    to_add = []
    hpc_list = (
        authentication.get("auth_state", {})
        .get("oauth_user", {})
        .get("hpc_infos_attribute", [])
    )
    if type(hpc_list) == str:
        hpc_list = [hpc_list]
    elif type(hpc_list) == list and len(hpc_list) > 0 and len(hpc_list[0]) == 1:
        hpc_list = ["".join(hpc_list)]
    for entry in hpc_list:
        try:
            partition = re.search("[^,]+,([^,]+),[^,]+,[^,]+", entry).groups()[0]
        except:
            authenticator.log.info(
                f"----- {username} - Failed to check for defaults partitions: {entry} ---- {hpc_list}"
            )
            continue
        if partition in default_partitions.keys():
            for value in default_partitions[partition]:
                to_add.append(
                    entry.replace(
                        f",{partition},",
                        ",{},".format(value),
                    )
                )
    hpc_list.extend(to_add)
    if hpc_list:
        authentication["auth_state"]["oauth_user"]["hpc_infos_attribute"] = hpc_list

    return authentication


class BackendLogoutHandler(LogoutHandler):
    async def _shutdown_servers(self, user):
        self.log.debug("Shutdown Servers -- not")
        pass

    async def default_handle_logout(self):
        uuidcode = uuid.uuid4().hex
        stopall = str(self.get_argument("stopall", "false", True)).lower()
        backend_logout_url = os.environ.get("BACKEND_URL_LOGOUT", "")
        user = self.current_user
        if user:
            self.log.info(
                "uuidcode={uuidcode} - action=logout username={username}".format(
                    uuidcode=uuidcode, username=user.name
                )
            )
            logout_all_devices = (
                str(
                    self.get_argument(
                        self.app.logout_on_all_devices_argname,
                        self.app.logout_on_all_devices,
                        True,
                    )
                ).lower()
                == "true"
            )
            if user.authenticator.enable_auth_state:
                auth_state = await user.get_auth_state()
                if auth_state:
                    if backend_logout_url:
                        if backend_logout_url[-1] == "/":
                            url = f"{backend_logout_url}{stopall}"
                        else:
                            url = f"{backend_logout_url}/{stopall}"

                        headers = {
                            "uuidcode": uuidcode,
                            "accesstoken": auth_state["access_token"],
                        }
                        if os.environ.get("BACKEND_SECRET", None):
                            headers["Backendsecret"] = os.environ.get("BACKEND_SECRET")

                        if stopall == "true":
                            """ Stop all Services for this username """
                            headers["username"] = user.name
                        if logout_all_devices and (
                            stopall == "true" or not user.active
                        ):
                            """ Only revoke refresh token if we logout from all devices and stop all services """
                            headers["refreshtoken"] = auth_state["refresh_token"]
                        with closing(requests.post(url, headers=headers, json={})) as r:
                            if r.status_code != 204:
                                self.log.warning(
                                    f"uuidcode={uuidcode} - Could not logout user in backend"
                                )
                                self.log.warning(r.status_code)
                                self.log.warning(r.text)

                    auth_state["access_token"] = ""
                    auth_state["exp"] = "0"
                    if logout_all_devices and (stopall == "true" or not user.active):
                        """ Delete tokens """
                        auth_state["refresh_token"] = ""

                    if self.app.strict_session_ids:
                        if logout_all_devices:
                            """ Delete all session_ids """
                            auth_state["session_ids"] = []
                        else:
                            """ Delete current session_id """
                            current_session_id = self.get_session_cookie()
                            self.log.debug(
                                "uuidcode={uuidcode} - Remove session id {id}".format(
                                    uuidcode=uuidcode, id=current_session_id
                                )
                            )
                            if current_session_id in auth_state.get("session_ids", []):
                                auth_state["session_ids"].remove(current_session_id)

                    if stopall == "true":
                        spawner_names = copy.deepcopy(list(user.spawners.keys()))
                        for name in spawner_names:
                            await self.proxy.delete_user(user, name)
                            try:
                                await user.stop(name)
                            except:
                                pass

                    await user.save_auth_state(auth_state)
            self._backend_logout_cleanup(user.name)
