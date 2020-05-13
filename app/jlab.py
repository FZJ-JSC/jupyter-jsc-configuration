'''
Created on 12 Feb, 2020

@author: Tim Kreuzer
'''

from flask import request
from flask_restful import Resource
from flask import current_app as app

from app import utils_common, utils_file_loads, jlab_utils, utils_db
import os
import requests
from pathlib import Path
from contextlib import closing
import shutil

class JupyterLabHandler(Resource):
    def get(self):
        """
        Headers:
            intern-authorization
            uuidcode
            email
            servername
            
        """
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("uuidcode={} - Get JupyterLab Status".format(uuidcode))
            app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers))
    
            # Check for the J4J intern token
            utils_common.validate_auth(app.log,
                                       uuidcode,
                                       request.headers.get('intern-authorization', None))
    
            request_headers = {}
            for key, value in request.headers.items():
                if 'Token' in key: # refresh, jhub, access
                    key = key.replace('-', '_')
                request_headers[key.lower()] = value
            email = request_headers.get('email', '<no_email_submitted>')
            email = email.replace("@", "_at_")
            app.log.trace("uuidcode={} - Get User ID for email: {}".format(uuidcode, email))
            servername = request_headers.get('servername', '<no_servername_submitted>6')
            user_id = utils_db.get_user_id(app.log, uuidcode, app.database, email)
            
            
            app.log.trace("uuidcode={} - User_id: {}".format(uuidcode, user_id))
            results = utils_db.get_container_info(app.log, uuidcode, app.database, user_id, servername)
            if len(results) > 0:
                slave_id, containername = results
            else:
                app.log.error("uuidcode={} - Containerinfo is empty for: user_id: {} , servername={}".format(uuidcode, user_id, servername))
                return "unknown", 200
            
            if slave_id == 0:
                app.log.error("uuidcode={} - Could not check if container {} is running".format(uuidcode, containername))
                return "unknown", 200
            slave_hostname = utils_db.get_slave_hostname(app.log, uuidcode, app.database, slave_id)
            url = app.urls.get('dockerspawner', {}).get('url_jlab_hostname', '<no_url_found>').replace('<hostname>', slave_hostname)
            header = {
                     "Intern-Authorization": utils_file_loads.get_j4j_dockerspawner_token(),
                     "uuidcode": uuidcode,
                     "containername": containername
                     }
            with closing(requests.get(url,
                                      headers=header,
                                      verify=False)) as r:
                if r.status_code == 200:
                    app.log.trace("uuidcode={} - Answer from DockerSpawner {}: {}".format(uuidcode, slave_hostname, r.text.strip()))
                    return r.text.strip(), 200
                else:
                    app.log.error("uuidcode={} - Could not check if container {} is running. DockerSpawner answered with: {} {}".format(uuidcode, containername, r.text, r.status_code))
                    return "unknown", 200
        except:
            app.log.exception("JLab.get failed. Bugfix required")
        return '', 202

    def post(self):
        try:
            """
            Headers:
                intern-authorization
                uuidcode
            Body:
                servername
                service
                dashboard
                email
                environments
                image
                port
                jupyterhub_api_url
            """
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("uuidcode={} - Start JupyterLab".format(uuidcode))
            app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers))
            app.log.trace("uuidcode={} - Json: {}".format(uuidcode, request.json))
    
            # Check for the J4J intern token
            utils_common.validate_auth(app.log,
                                       uuidcode,
                                       request.headers.get('intern-authorization', None))
            
            request_json = {}
            for key, value in request.json.items():
                if 'Token' in key: # refresh, jhub, access
                    key = key.replace('-', '_')
                request_json[key.lower()] = value
            app.log.trace("uuidcode={} - New Json: {}".format(uuidcode, request_json))
            
            servername = request_json.get('servername')
            email = request_json.get('email')
            email = email.replace("@", "_at_")
            environments = request_json.get('environments')
            service = request_json.get('service')
            dashboard = request_json.get('dashboard')
            image = request_json.get('image')
            port = request_json.get('port')
            config = utils_file_loads.get_general_config()
            quota_config = utils_file_loads.get_quota_config()
            jupyterhub_api_url = config.get('jupyterhub_api_url')
            basefolder = config.get('basefolder', '<no basefolder defined>')
            userfolder = os.path.join(basefolder, email)
            serverfolder = Path(os.path.join(userfolder, '.{}'.format(uuidcode)))
            os.umask(0)
            user_id, set_user_quota = jlab_utils.create_user(app.log, uuidcode, app.database, quota_config, email, basefolder, userfolder)
            jlab_utils.create_server_dirs(app.log, uuidcode, app.urls, app.database, service, dashboard, user_id, email, servername, serverfolder, basefolder)
            #jlab_utils.setup_server_quota(app.log, uuidcode, quota_config, serverfolder)
            try:
                start = jlab_utils.call_slave_start(app.log,
                                                    uuidcode,
                                                    app.database,
                                                    app.urls,
                                                    userfolder,
                                                    config.get('jlab', '<no_jlab_path_defined>'),
                                                    quota_config,
                                                    set_user_quota,
                                                    user_id,
                                                    servername,
                                                    email,
                                                    environments,
                                                    image,
                                                    port,
                                                    jupyterhub_api_url)
            except:
                app.log.exception("uuidcode={} - Could not start JupyterLab".format(uuidcode))
                start = False
            if start:
                return 200
            else:
                return 501
        except:
            app.log.exception("JLab.post failed. Bugfix required")
        return 500

    def delete(self):
        """
        Headers
            Intern-Authorization
            uuidcode
            email
            servername            
        """
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("uuidcode={} - Delete Server".format(uuidcode))
            app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers))
    
            # Check for the J4J intern token
            utils_common.validate_auth(app.log,
                                       uuidcode,
                                       request.headers.get('intern-authorization', None))
            request_headers = {}
            for key, value in request.headers.items():
                if 'Token' in key: # refresh, jhub, access
                    key = key.replace('-', '_')
                request_headers[key.lower()] = value           
            
            config = utils_file_loads.get_general_config()
            email = request_headers.get('email', '<no_email_submitted>')
            email = email.replace("@", "_at_")
            servername = request_headers.get('servername', '<no_servername_submitted>')
            
            results = jlab_utils.get_slave_infos(app.log,
                                                 uuidcode,
                                                 app.database,
                                                 servername,
                                                 email)
            if len(results) > 0:
                user_id, slave_id, slave_hostname, containername, running_no = results
            else:
                app.log.warning("uuidcode={} - {} not in database".format(uuidcode, servername))
                return '', 202

            
            url = app.urls.get('dockerspawner', {}).get('url_jlab_hostname', '<no_url_found>').replace('<hostname>', slave_hostname)
            headers = {
                      "Intern-Authorization": utils_file_loads.get_j4j_dockerspawner_token(),
                      "uuidcode": uuidcode,
                      "containername": containername
                      }
            try:
                with closing(requests.delete(url,
                                             headers=headers,
                                             verify=False)) as r:
                    if r.status_code != 202:
                        app.log.error("uuidcode={} - DockerSpawner delete failed: {} {}".format(uuidcode, r.text, r.status_code))
            except:
                app.log.exception("uuidcode={} - Could not call DockerSpawner {}".format(uuidcode, slave_hostname))
            basefolder = config.get('basefolder', '<no basefolder defined>')
            userfolder = os.path.join(basefolder, email)
            serverfolder = Path(os.path.join(userfolder, '.{}'.format(containername)))
            utils_db.decrease_slave_running(app.log, uuidcode, app.database, slave_id)
            utils_db.remove_container(app.log, uuidcode, app.database, user_id, servername)
            log_dir = Path(os.path.join(config.get('jobs_path', '<no_jobs_path>'), "{}-{}".format(email, containername)))
            try:
                os.makedirs(log_dir, exist_ok=True)
                shutil.copy2(os.path.join(serverfolder, ".jupyterlabhub.log"), os.path.join(log_dir, "jupyterlabhub.log"))
            except:
                app.log.exception("uuidcode={} - Could not copy log".format(uuidcode))
            jlab_output = "{};{};{}".format(userfolder,
                                            containername,
                                            running_no == 1)
            jlab_delete_path = config.get('jlab_delete', '<no_jlab_delete_defined>')
            app.log.debug("uuidcode={} - Write {} to {}".format(uuidcode, jlab_output, os.path.join(jlab_delete_path, uuidcode)))
            with open(os.path.join(jlab_delete_path, uuidcode), 'w') as f:
                f.write(jlab_output)
                
        except:
            app.log.exception("JLabs.delete failed. Bugfix required")
            return "", 500
        return '', 202
