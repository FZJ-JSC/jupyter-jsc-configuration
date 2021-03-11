import requests
import os
from contextlib import closing
from jupyterhub.apihandlers.base import APIHandler
from jupyterhub.utils import token_authenticated, url_path_join
from tornado import web

class SetupTunnelAPIHandler(APIHandler):
    @token_authenticated
    async def post(self, username, servername_short, startuuidcode, hostname, port2):
        user = self.get_current_user_token()
        if not (username == user.name):
            raise web.HTTPError(403)
        servername = f"{user.name}:{servername_short}"
        self.log.info(f"uuidcode={startuuidcode} - Service {servername} started on {hostname}:{port2}")
        backend_tunnel_url = os.environ.get("BACKEND_URL_TUNNEL")
        headers = {
            "Authorization": self.request.headers.get("Authorization", "None")
        }
        url = url_path_join(f"{backend_tunnel_url}/", f"{startuuidcode}/", f"{servername}/", f"{hostname}/", f"{port2}")
        self.log.info(f"Call {url} with\n{headers}")
        with closing(requests.post(url, headers=headers, verify=False)) as r:
            if r.status_code != 200:
                self.log.error(f"uuidcode={startuuidcode} - Backend Tunneling returned unexpected status_code: {r.status_code}.")
                spawner = user.spawners[servername_short]
                await spawner._cancel(f"Could not build up Tunnel between Jupyter-JSC and {servername_short}")
        data = self.get_json_body()
        if data:
            self.log.info(data)
            percent = int(data["progress"])
            spawner = user.spawners[servername_short]
            spawner.progress_dic[percent] = data
            spawner.progress_number = percent
        self.set_header('Content-Type', 'text/plain')
        self.set_status(202)