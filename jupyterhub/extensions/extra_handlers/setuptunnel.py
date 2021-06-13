import os
from contextlib import closing

import requests
from tornado import web
from tornado.httpclient import HTTPRequest, HTTPClientError

from jupyterhub.apihandlers.base import APIHandler
from jupyterhub.utils import token_authenticated
from jupyterhub.utils import url_path_join


class SetupTunnelAPIHandler(APIHandler):
    @token_authenticated
    async def post(self, username, servername_short, startuuidcode, hostname, port2):
        user = self.get_current_user_token()
        if not (username == user.name):
            raise web.HTTPError(403)
        servername = f"{user.name}:{servername_short}"
        self.log.info(
            f"uuidcode={startuuidcode} - Service {servername} started on {hostname}:{port2}"
        )
        backend_tunnel_url = os.environ.get("BACKEND_URL_TUNNEL")
        headers = {
            "Authorization": self.request.headers.get("Authorization", "None"),
            "startuuidcode": startuuidcode,
            "uuidcode": startuuidcode,
            "servername": servername,
            "hostname": hostname,
            "port2": port2,
        }
        if os.environ.get("BACKEND_SECRET", None):
            headers["Backendsecret"] = os.environ.get("BACKEND_SECRET")
        self.log.info(f"Call {backend_tunnel_url} with - {headers}")
        req = HTTPRequest(
            backend_tunnel_url,
            method="POST",
            body="{}",
            headers=headers,
            connect_timeout=2,
            request_timeout=2,
        )
        try:
            resp = await user.authenticator.fetch(req)
        except HTTPClientError as e:
            self.log.warning("uuidcode={} - {}".format(uuidcode, e))
            spawner = user.spawners[servername_short]
            await spawner._cancel(
                f"Could not build up Tunnel between Jupyter-JSC and {servername_short}"
            )
        else:
            if resp:
                percent = int(resp["progress"])
                spawner = user.spawners[servername_short]
                spawner.progress_dic[percent] = resp
                spawner.progress_number = percent
        self.set_header("Content-Type", "text/plain")
        self.set_status(202)
