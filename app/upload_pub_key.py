'''
Created on 12 Feb, 2020

@author: Tim Kreuzer
'''

from flask import request
from flask_restful import Resource
from flask import current_app as app

from app import utils_common, upload_pub_key_utils

class JupyterLabHandler(Resource):
    """
       TODO Need mount for /etc/j4j/j4j_hdfcloud (users data!) to get public key
    """
    def post(self):
        """
        Headers:
            Jupyter_API_TOKEN
            uuidcode
        JSON:
            System
            Account
            service_prefix
            apiurl
        """
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("uuidcode={} - Start JupyterLab".format(uuidcode))
            app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers.to_list()))
            app.log.trace("uuidcode={} - Json: {}".format(uuidcode, request.json))
    
            # Check for the J4J intern token
            utils_common.validate_api_token(app.log,
                                            uuidcode,
                                            app.urls,
                                            request.headers.get('Jupyter_api_token', None))
    
            request_headers = {}
            for key, value in request.headers.items():
                if 'Token' in key: # refresh, jhub, access
                    key = key.replace('-', '_')
                request_headers[key.lower()] = value
            request_json = {}
            for key, value in request.json.items():
                if 'Token' in key: # refresh, jhub, access
                    key = key.replace('-', '_')
                request_json[key.lower()] = value
            app.log.trace("uuidcode={} - New Headers: {}".format(uuidcode, request_headers))
            app.log.trace("uuidcode={} - New Json: {}".format(uuidcode, request_json))
            
            system = request_json.get('system', '<no_system>')
            uid = request_json.get('account', '<no_account>')
            service_prefix = request_json.get('service_prefix', '<no_service_prefix>')
            api_url = request_json.get('apiurl', '<no_apiurl>')
            jhub_token = request_json.get('jupyter_api_token', '<no_token>')
            code = upload_pub_key_utils.upload_pub_key(app.log, uuidcode, system, uid, service_prefix, api_url, jhub_token)
            return "", code            
        except:
            app.log.exception("Could not upload Public Key. Bugfix required")
            return "", 500
