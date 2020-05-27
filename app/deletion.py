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



def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

class DeletionHandler(Resource):
    def delete(self):
        """
        Headers
            Intern-Authorization
            uuidcode
            email
        """
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("uuidcode={} - Delete Account".format(uuidcode))
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
            basefolder = config.get('basefolder', '<no basefolder defined>')
            userfolder = os.path.join(basefolder, email)
            
            user_id = utils_db.get_user_id(app.log,
                                           uuidcode,
                                           app.database,
                                           email)
            
            servernames = utils_db.get_all_user_container_names(app.log,
                                                                uuidcode,
                                                                app.database,
                                                                user_id)
            for servername in servernames:            
                results = jlab_utils.get_slave_infos(app.log,
                                                     uuidcode,
                                                     app.database,
                                                     servername,
                                                     email)
                if len(results) > 0:
                    user_id, slave_id, slave_hostname, containername, running_no = results
                else:
                    app.log.warning("uuidcode={} - {} not in database".format(uuidcode, servername))
                    continue;
            
                url = app.urls.get('dockerspawner', {}).get('url_jlab_hostname', '<no_url_found>').replace('<hostname>', slave_hostname)
                headers = {"Intern-Authorization": utils_file_loads.get_j4j_dockerspawner_token(),
                           "uuidcode": uuidcode,
                           "containername": containername}
                try:
                    with closing(requests.delete(url,
                                                 headers=headers,
                                                 verify=False)) as r:
                        if r.status_code != 202:
                            app.log.error("uuidcode={} - DockerSpawner delete failed: {} {}".format(uuidcode, r.text, r.status_code))
                except:
                    app.log.exception("uuidcode={} - Could not call DockerSpawner {}".format(uuidcode, slave_hostname))
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
            # end for loop all containers are stopped
            utils_db.delete_account(app.log,
                                    uuidcode,
                                    app.database,
                                    user_id)
            try:
                #shutil.rmtree(userfolder)
                app.log.error("uuidcode={} - Account deletion. Please remove {} from the disk.".format(uuidcode, userfolder))
                # remove user quota from xfs_quota
                jlab_output = "{}".format(uuidcode)
                jlab_delete_path = config.get('jlab_delete', '<no_jlab_delete_defined>')
                app.log.debug("uuidcode={} - Write {} to {}.deletion".format(uuidcode, jlab_output, os.path.join(jlab_delete_path, email)))
                with open('{}.deletion'.format(os.path.join(jlab_delete_path, email)), 'w') as f:
                    f.write(jlab_output)
            except:
                app.log.exception("uuidcode={} - Could not delete the users directories".format(uuidcode))
            
        except:
            app.log.exception("Deletion.delete failed. Bugfix required")
            return "", 500
        return '', 204


    def get(self):
        """
        Headers
            Intern-Authorization
            uuidcode
            email
        """
        try:
            # Track actions through different webservices.
            uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
            app.log.info("uuidcode={} - Get Deletion information".format(uuidcode))
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
            basefolder = config.get('basefolder', '<no basefolder defined>')
            userfolder = os.path.join(basefolder, email)
            workfolder = os.path.join(userfolder, "work")
            projectfolder = os.path.join(userfolder, "Projects", "MyProjects")
            totalfiles = 0
            totalsize = 0
            for root, dirs, files in os.walk(workfolder):  # @UnusedVariable
                if root.endswith(".hpc_mount") or \
                root.endswith(".hpc_mount/.upload") or \
                root.endswith(".davfs2") or \
                root.endswith(".davfs2/cache") or \
                root.endswith(".davfs2/cache/b2drop.eudat.eu-remote.php-webdav+home-jovyan-B2DROP+jovyan") or \
                root.endswith(".davfs2/certs") or \
                root.endswith(".davfs2/certs/private") or \
                root.endswith(".ipynb_checkpoints"):
                    continue
                else:
                    totalfiles += len(files)
                for file in files:
                    filepath = os.path.join(root, file)
                    totalsize += os.path.getsize(filepath)
            for root, dirs, files in os.walk(projectfolder):  # @UnusedVariable
                totalfiles += len(files)
                for file in files:
                    filepath = os.path.join(root, file)
                    totalsize += os.path.getsize(filepath)
            totalsize = sizeof_fmt(totalsize)
        except:
            app.log.exception("Deletion.get failed. Bugfix required")
            return "", 500
        return '{}:{}'.format(totalfiles, totalsize), 200