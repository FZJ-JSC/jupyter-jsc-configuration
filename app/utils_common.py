'''
Created on Feb 12, 2020

@author: Tim Kreuzer
'''

from flask import abort

import requests
from contextlib import closing
from app.utils_file_loads import get_j4j_dockermaster_token, get_jhub_token

def validate_api_token(app_logger, uuidcode, app_urls, jupyter_api_token):
    token_url = app_urls.get('hub', {}).get('url_token', '<no_token_url>')
    jhub_internal_token = get_jhub_token()
    headers = {
              "Intern-Authorization": jhub_internal_token,
              "uuidcode": uuidcode,
              "Authorization": "token {}".format(jupyter_api_token)
              }
    try:
        with closing(requests.get(token_url, headers=headers, verify=False)) as r:
            if r.status_code != 200 and r.status_code != 201:
                app_logger.error("uuidcode={} - Could not validate Jupyter-API-Token".format(uuidcode))
                abort(401)
            else:
                return
    except:
        app_logger.exception("uuidcode={} - Could not validate Jupyter-API-Token".format(uuidcode))
        abort(401)

def validate_auth(app_logger, uuidcode, intern_authorization):
    if not intern_authorization == None:
        token = get_j4j_dockermaster_token()
        if intern_authorization == token:
            app_logger.debug("uuidcode={} - intern-authorization validated".format(uuidcode))
            return
    app_logger.warning("uuidcode={} - Could not validate Intern-Authorization".format(uuidcode))
    abort(401)

def remove_secret(json_dict):
    if type(json_dict) != dict:
        return json_dict
    secret_dict = {}
    for key, value in json_dict.items():
        if type(value) == dict:
            secret_dict[key] = remove_secret(value)
        elif key.lower() in ["authorization", "accesstoken", "refreshtoken", "jhubtoken", "intern-authorization"]:
            secret_dict[key] = '<secret>'
        else:
            secret_dict[key] = value
    return secret_dict
