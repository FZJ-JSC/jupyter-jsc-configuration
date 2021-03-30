import json
import os
from contextlib import closing

import pyunicore.client as unicore_client
import requests


def get_access_token():
    remote_node = os.getenv("REMOTE_NODE")
    remote_hub_port = os.getenv("REMOTE_HUB_PORT")
    hub_api_url = f"http://{remote_node}:{remote_hub_port}/hub/api/user"
    headers = {"Authorization": "token {}".format(os.getenv("JUPYTERHUB_API_TOKEN"))}
    with closing(requests.get(hub_api_url, headers=headers)) as r:
        if r.status_code == 200:
            resp = json.loads(r.content.decode("utf-8"))
        else:
            raise Exception(
                "Could not receive access token: {} {}".format(
                    r.status_code, r.content.decode("utf-8")
                )
            )
    return resp["auth_state"]["access_token"]


def get_mount_command(access_token):
    _auth = "https://uftp.fz-juelich.de:9112/UFTP_Auth/rest/auth/"
    _tr = unicore_client.Transport(access_token)
    _info = _tr.get(url=_auth)
    _uid = _info["JUDAC"]["uid"]
    remote_base_dir = "/p/home/jusers/%s" % _uid

    # authenticate
    _req = {
        "persistent": "true",
        "serverPath": "%s/___UFTP___MULTI___FILE___SESSION___MODE___" % remote_base_dir,
    }
    _reply = _tr.post(url=_auth + "/JUDAC", json=_req).json()
    uftp_pwd = _reply["secret"]
    uftp_host = _reply["serverHost"]
    uftp_port = _reply["serverPort"]
    return f"curlftpfs -s -o uid=1094,gid=100,ftp_method=singlecwd,enable_epsv,user=anonymous:{uftp_pwd} {uftp_host}:{uftp_port}"


if __name__ == "__main__":
    access_token = get_access_token()
    mount_cmd = get_mount_command(access_token)
    print(mount_cmd)
