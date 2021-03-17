import json
import os
import time
from contextlib import closing

import requests


def get_reservations(log=None):
    reservations_path = os.environ.get("RESERVATIONS_PATH")
    with open(reservations_path, "r") as f:
        reservations = json.load(f)
    now = int(time.time())
    if reservations["refresh_call_at"] < now:
        # Update time for new update
        new_call_time = now + int(os.environ.get("RESERVATIONS_CACHE_TIME", "300"))
        reservations["refresh_call_at"] = new_call_time
        with open(reservations_path, "w") as f:
            json.dump(reservations, f, indent=4, sort_keys=True)

        # Call Backend to update reservations file
        url = os.environ.get("BACKEND_RESERVATIONS_URL")
        try:
            with closing(requests.get(url, headers={}, verify=False)) as r:
                if r.status_code == 200:
                    with open(reservations_path, "r") as f:
                        reservations = json.load(f)
                else:
                    if log:
                        log.error(
                            "Could not update reservations file: {} {}".format(
                                r.status_code, r.text
                            )
                        )
        except:
            if log:
                log.exception("Could not update reservations file")

    return reservations["value"]


def get_resources(log=None):
    resources_path = os.environ.get("RESOURCES_PATH")
    with open(resources_path, "r") as f:
        resources = json.load(f)
    now = int(time.time())
    if resources["refresh_call_at"] < now:
        # Update time for new update
        new_call_time = now + int(os.environ.get("RESOURCES_CACHE_TIME", "3600"))
        resources["refresh_call_at"] = new_call_time
        with open(resources_path, "w") as f:
            json.dump(resources, f, indent=4, sort_keys=True)

        # Call Backend to update resources file
        url = os.environ.get("BACKEND_RESOURCES_URL")
        try:
            with closing(requests.get(url, headers={}, verify=False)) as r:
                if r.status_code == 200:
                    with open(resources_path, "r") as f:
                        resources = json.load(f)
                else:
                    if log:
                        log.error(
                            "Could not update resources file: {} {}".format(
                                r.status_code, r.text
                            )
                        )
        except:
            if log:
                log.exception("Could not update resources file")

    return resources["value"]
