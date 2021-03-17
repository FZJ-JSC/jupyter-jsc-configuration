import json
import os
import uuid
from contextlib import closing

import jwt
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate

from jupyterhub.apihandlers.base import APIHandler
from jupyterhub.orm import Spawner
from jupyterhub.utils import url_path_join


class UNICORENotificationAPIHandler(APIHandler):
    def verify_unicore(self, uuidcode, kernelurl, auth, unicore_config):
        system = ""
        cert_url = ""
        cert_path = ""
        cert = ""

        for isystem, infos in unicore_config.items():
            if type(infos) != dict:
                continue
            if kernelurl.startswith(infos.get("base_url", "...")):
                system = isystem
                cert_url = url_path_join(infos.get("base_url"), "certificate")
                cert_path = infos.get("certificate", False)
                break
        if system != "":
            with closing(
                requests.get(
                    cert_url, headers={"accept": "text/plain"}, verify=cert_path
                )
            ) as r:
                cert = r.content
        else:
            raise Exception(
                "Could not find any systems for the url: {}".format(kernelurl)
            )

        bearer = auth.split()[1]
        cert_obj = load_pem_x509_certificate(cert, default_backend())
        # jwt_dic = jwt.decode(bearer, cert_obj.public_key(), options={'verify_exp': False})
        jwt_dic = jwt.decode(bearer, cert_obj.public_key())

    async def post(self, username, server_name=""):
        uuidcode = uuid.uuid4().hex
        self.log.debug(
            "uuidcode={} - UX Handler for username={} servername={}".format(
                uuidcode, username, server_name
            )
        )
        user = self.find_user(username)
        if not user:
            self.set_status(404)
            self.write("User with name {} not found".format(username))
            self.flush()
            return
        data = self.request.body.decode("utf8")
        jdata = json.loads(data)
        kernelurl = jdata.get("href", "")
        header = self.request.headers
        auth = header.get("Authorization", None)
        if not auth:
            self.log.error("UNICORE/X Notification call without Auth header")
            self.set_status(401)
            self.write("No Authorization Header found")
            self.flush()
            return

        unicore_config_path = os.environ.get("UNICORE_CONFIG_PATH", None)
        if not unicore_config_path:
            raise Exception("Please define environment variable UNICORE_CONFIG_PATH")
        with open(unicore_config_path, "r") as f:
            unicore_config = json.load(f)

        try:
            self.verify_unicore(uuidcode, kernelurl, auth, unicore_config)
        except:
            self.log.exception(
                "uuidcode={} - Could not verify token {} with public key for UNICORE/X".format(
                    uuidcode, auth
                )
            )
            self.set_status(401)
            return

        self.log.debug(f"U/X Notification: {jdata}")

        if jdata.get("status", "") == "RUNNING":
            # do nothing. We're expecting it to run
            self.set_status(204)
            return
        elif jdata.get("status", "") in ["SUCCESSFUL", "FAILED", "DONE"]:
            force = False
            auth_state = await user.get_auth_state()
            if auth_state and not auth_state["access_token"]:
                """If there's no access_token in auth_state we have to get one"""
                force = True
            await self.refresh_auth(user, force)
            err_msg = jdata.get("statusMessage", "")
            if err_msg == "Job was aborted by the user.":
                # do nothing. We've killed this job via Jupyter-jsc and therefore know this status already
                self.set_status(202)
                return
            self.log.info(
                "uuidcode={} - Job is finished. Stop it via JupyterHub.".format(
                    uuidcode
                )
            )
            try:
                try:
                    uuidlen = server_name.split("_")[0]
                    strlen = len(uuidlen) + int(uuidlen) + 2
                    start_uuid = server_name.split("_")[1]
                    server_name = server_name[strlen:]
                except:
                    start_uuid = None
                    self.log.exception(
                        "uuidcode={} - Looks like servername {} has no uuid in it".format(
                            uuidcode, server_name
                        )
                    )
                db_spawner = (
                    user.db.query(Spawner)
                    .filter(Spawner.name == server_name)
                    .filter(Spawner.user_id == user.orm_user.id)
                    .first()
                )
                if db_spawner:
                    user.db.refresh(db_spawner)
                    user.spawners[server_name].load_state(db_spawner.state)
                if start_uuid:
                    self.log.info(db_spawner.state.get("start_uuid", ""))
                    self.log.info(start_uuid)
                    if db_spawner.state.get("start_uuid", "") != start_uuid:
                        self.log.info(
                            "uuidcode={} - That's not the uuid this server was started with. So we ignore this U/X notification, because it's for an already stopped server.".format(
                                uuidcode
                            )
                        )
                        self.set_status(200)
                        return

                user_msg = err_msg
                for err_message_key, err_message_mapped in unicore_config.get(
                    "error_mapping", {}
                ).items():
                    if err_msg.startswith(err_message_key):
                        user_msg = err_message_mapped
                if user_msg == err_msg:
                    self.log.error(f"No specific user msg for: {user_msg}")

                cancelled = await user.spawners[server_name]._cancel(user_msg, err_msg)
                if not cancelled:
                    await user.stop(server_name)

                self.set_status(202)
            except:
                self.log.exception(
                    "UID={} - uuidcode={} Could not cancel the spawner: {}".format(
                        user.name, uuidcode, server_name
                    )
                )
                self.set_status(501)
                self.write(
                    "Could not stop Server. Please look into the logs with the uuidcode: uuidcode={}".format(
                        uuidcode
                    )
                )
                self.flush()
        else:
            self.log.error(
                "uuidcode={} UX Handler: Unknown status. Insert reaction to this status: {}".format(
                    uuidcode, jdata
                )
            )
        return
