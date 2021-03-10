import os
import uuid


from datetime import datetime
from tornado.httpclient import HTTPClientError, HTTPRequest
from oauthenticator.generic import GenericOAuthenticator
import time
from contextlib import closing
import requests
import json
import re
from subprocess import Popen, PIPE


from traitlets import Unicode
from jupyterhub.handlers.login import LogoutHandler
from jupyterhub.jupyterjsc.utils.vo import get_vos


def get_hpc_accounts_via_ssh(username, log=None):
    ssh_key = os.environ.get("GET_HPC_ACCOUNTS_SSH_KEY")
    ssh_user = os.environ.get("GET_HPC_ACCOUNTS_SSH_USER")
    ssh_host = os.environ.get("GET_HPC_ACCOUNTS_SSH_HOST")
    if username.endswith("@fz-juelich.de"):
        username = username[:-len("@fz-juelich.de")]
    cmd = ["/usr/bin/ssh", "-oLogLevel=ERROR", "-oStrictHostKeyChecking=no", "-oUserKnownHostsFile=/dev/null", "-i", f"{ssh_key}", f"{ssh_user}@{ssh_host}", f",{username}"]
    p = Popen(cmd, stderr=PIPE, stdout=PIPE)
    outb, errb = p.communicate(timeout=int(os.environ.get("GET_HPC_ACCOUNTS_SSH_TIMEOUT", "3")))
    out = outb.decode("utf-8")
    # err = errb.decode("utf-8")
    return_code = p.returncode
    list_out = []
    try:
        if return_code == 0 and out:
            list_out = out.split()
            default_partitions = {
                "juwels": "juwels_devel",
                "juwels_gpus": "juwels_develgpus",
                "jusuf_gpus": "jusuf_develgpus",
                "deep_cpu": "deep_ml-gpu"
            }
            to_add = []
            for entry in list_out:
                partition = re.search("[^,]+,([^,]+),[^,]+,[^,]+", entry).groups()[0]
                if partition in default_partitions.keys():
                    to_add.append(entry.replace(f",{partition},", ",{},".format(default_partitions[partition])))
            list_out.extend(to_add)
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
        tic = time.time()
        ret = False
        auth_state = await user.get_auth_state()
        timestamp = int(time.time()) + int(os.environ.get("UNITY_REFRESH_THRESHOLD", "600")) 
        if force or timestamp >= int(auth_state.get('exp', timestamp)):
            try:
                http_client = self.http_client()

                params = {
                    "refresh_token": auth_state.get("refresh_token"),
                    "grant_type": "refresh_token",
                    "scope": ' '.join(self.scope)
                }
 
                headers = self._get_headers()
                try:
                    token_resp_json = await self._get_token(http_client, headers, params)
                except HTTPClientError:
                    self.log.exception("Could not receive new access token.")
                    return False

                user_data_resp_json = await self._get_user_data(http_client, token_resp_json)

                if callable(self.username_key):
                    name = self.username_key(user_data_resp_json)
                else:
                    name = user_data_resp_json.get(self.username_key)
                    if not name:
                        self.log.error(
                            "OAuth user contains no key %s: %s", self.username_key, user_data_resp_json
                        )
                        return

                    authentication = {
                        "auth_state": self._create_auth_state(token_resp_json, user_data_resp_json)
                    }
                    ret = await self.run_post_auth_hook(handler, authentication)
            except:
                self.log.exception("Refresh of user's {name} access token failed".format(name=user.name))
                ret = False
        else:
            self.log.debug("No refresh required. {} seconds left".format(int(auth_state.get('exp')) - tic))
            ret = True
        toc = time.time()
        self.log.debug("Used time to refresh auth: {}".format(toc-tic))
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
    resp_json = json.loads(resp.body.decode('utf8', 'replace'))
    authentication["auth_state"]["exp"] = resp_json.get('exp')
    authentication["auth_state"]["last_login"] = datetime.now().strftime("%H:%M:%S %Y-%m-%d")

    username = authentication.get("name", "unknown")
    admin = authentication.get("admin", False)
    vo_active, vo_available = get_vos(authentication["auth_state"], username, admin=admin)
    authentication["auth_state"]["vo_active"] = vo_active
    authentication["auth_state"]["vo_available"] = vo_available

    hpc_list = get_hpc_accounts_via_ssh(username, authenticator.log)
    if hpc_list:
        authentication["auth_state"]["oauth_user"]["hpc_infos_attribute"] = hpc_list

    return authentication


class BackendLogoutHandler(LogoutHandler):
    async def _shutdown_servers(self, user):
        # If we want to stop servers at logout we will do this in the backend.
        # Any stopped Jobs will notify JupyterHub via UNICORE/X notification
        # endpoint. Therefore we ensure two things: Anything will be stopped
        # by the Backend. JupyterHub get's informed.
        pass

    async def default_handle_logout(self):
        uuidcode = uuid.uuid4().hex
        stopall = str(self.get_argument("stopall", "false", True)).lower()
        backend_logout_url = os.environ.get("BACKEND_URL_LOGOUT", "")
        user = self.current_user
        if user:
            self.log.info("uuidcode={uuidcode} - action=logout username={username}".format(uuidcode=uuidcode, username=user.name))
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
                    
                        if stopall == "true":
                            ''' Stop all Services for this username '''
                            headers["username"] = user.name
                        if logout_all_devices and (stopall == "true" or not user.active):
                            ''' Only revoke refresh token if we logout from all devices and stop all services '''
                            headers['refreshtoken'] = auth_state["refresh_token"]
                        
                        self.log.info(url)
                        self.log.info(headers)
                        with closing(requests.post(url, headers=headers, json={})) as r:
                            if r.status_code != 204:
                                self.log.warning(f"uuidcode={uuidcode} - Could not logout user in backend")
                                self.log.warning(r.status_code)
                                self.log.warning(r.text)
        
                    auth_state["access_token"] = ""
                    auth_state["exp"] = "0"                    
                    if logout_all_devices and (stopall == "true" or not user.active):
                        ''' Delete tokens '''
                        auth_state["refresh_token"] = ""

                    if self.app.strict_session_ids:
                        if logout_all_devices:
                            ''' Delete all session_ids '''
                            auth_state['session_ids'] = []    
                        else:
                            ''' Delete current session_id '''
                            current_session_id = self.get_session_cookie()
                            self.log.debug("uuidcode={uuidcode} - Remove session id {id}".format(uuidcode=uuidcode, id=current_session_id))
                            if current_session_id in auth_state.get('session_ids', []):
                                auth_state['session_ids'].remove(current_session_id)
                    await user.save_auth_state(auth_state)
            self._backend_logout_cleanup(user.name)
