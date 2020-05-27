'''
Created on Feb 12, 2020

@author: Tim Kreuzer
'''

import os
import shutil

import requests

from app.utils_common import remove_secret
from contextlib import closing
from pathlib import Path
from time import sleep
from app import utils_db, utils_file_loads, jlab_utils

def call_slave_start(app_logger, uuidcode, app_database, app_urls, userfolder, config, quota_config, set_user_quota, user_id, servername, email, environments, image, port, jupyterhub_api_url):
    user_running = utils_db.get_user_running(app_logger, uuidcode, app_database, user_id)
    if user_running >= config.get('user_running_limit', 10):
        app_logger.error("uuidcode={} - User has already {} JupyterLabs running (Limit: {}). Cancel start.".format(uuidcode, user_running, config.get('user_running_limit', 5)))
        try:
            # we have to sleep for 2 seconds, otherwise JupyterHub is not ready for this call
            sleep(2)
            cancel(app_logger,
                   uuidcode,
                   config.get('jupyterhub_cancel_url', '<no_jupyterhub_cancel_url_defined>'),
                   environments.get('JUPYTERHUB_API_TOKEN'),
                   "Due to heavy load on the HDF-Cloud, the access is currently limited to {} JupyterLabs per user.".format(config.get('user_running_limit', 10)),
                   email.replace("_at_", "@"),
                   servername)
        except:
            app_logger.exception("uuidcode={} - Could not cancel start.".format(uuidcode))
        return False
    next_slave_id, next_slave_hostname = utils_db.get_next_slave(app_logger, uuidcode, app_database)
    if next_slave_id == 0:
        app_logger.error("uuidcode={} - Could not find any slaves in database".format(uuidcode))
        raise Exception("No Slaves available")
    header = {
             "Intern-Authorization": utils_file_loads.get_j4j_dockerspawner_token(),
             "uuidcode": uuidcode
             }
    body = {
           "email": email,
           "environments": environments,
           "image": image,
           "port": port,
           "servername": servername,
           "jupyterhub_api_url": jupyterhub_api_url
           }
    url = app_urls.get('dockerspawner', {}).get('url_jlab_hostname', '<no_url_found>').replace('<hostname>', next_slave_hostname)
    try:
        with closing(requests.post(url,
                                   headers=header,
                                   json=body,
                                   verify=False)) as r:
            if r.status_code != 202:
                app_logger.error("uuidcode={} - DockerSpawner answered .post with {} {}".format(uuidcode, r.text, r.status_code))
                return False
    except:
        app_logger.exception("uuidcode={} - DockerSpawner post failed".format(uuidcode))
        return False
    utils_db.insert_container(app_logger, uuidcode, app_database, user_id, next_slave_id, servername)
    user_running = utils_db.get_user_running(app_logger, uuidcode, app_database, user_id)
    utils_db.increase_slave_running(app_logger, uuidcode, app_database, next_slave_id)
    jlab_output = "{};{};{};{};{};{};{};{};{}".format(userfolder,
                                                      email.replace("@", "_at_"),
                                                      uuidcode,
                                                      quota_config.get('ALL', "25g"),
                                                      quota_config.get('WORK', "10g"),
                                                      quota_config.get('PROJECTS', "10g"),
                                                      quota_config.get('HOME', "512m"),
                                                      set_user_quota,
                                                      user_running == 1)
    
    app_logger.debug("uuidcode={} - Write {} to {}".format(uuidcode, jlab_output, os.path.join(config.get('jlab', '<no_jlab_path_defined>'), uuidcode)))
    with open(os.path.join(config.get('jlab', '<no_jlab_path_defined>'), uuidcode), 'w') as f:
        f.write(jlab_output)
    return True
    

def create_server_dirs(app_logger, uuidcode, app_urls, app_database, service, dashboard, user_id, email, servername, serverfolder, basefolder):
    results = utils_db.get_container_info(app_logger, uuidcode, app_database, user_id, servername)
    app_logger.debug("uuidcode={} - Container Info: {}".format(uuidcode, results))
    if len(results) > 0:
        app_logger.debug("uuidcode={} - Server with name {} already exists. Delete it.".format(uuidcode, serverfolder))
        config = utils_file_loads.get_general_config()
        user_id, slave_id, slave_hostname, containername, running_no = jlab_utils.get_slave_infos(app_logger,
                                                                                                  uuidcode,
                                                                                                  app_database,
                                                                                                  servername,
                                                                                                  email)
        
        url = app_urls.get('dockerspawner', {}).get('url_jlab_hostname', '<no_url_found>').replace('<hostname>', slave_hostname)
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
                    app_logger.error("uuidcode={} - DockerSpawner delete failed: {} {}".format(uuidcode, r.text, r.status_code))
        except:
            app_logger.exception("uuidcode={} - Could not call DockerSpawner {}".format(uuidcode, slave_hostname))
        basefolder = config.get('basefolder', '<no basefolder defined>')
        userfolder = os.path.join(basefolder, email)
        serverfolder = Path(os.path.join(userfolder, '.{}'.format(containername)))
        utils_db.decrease_slave_running(app_logger, uuidcode, app_database, slave_id)
        utils_db.remove_container(app_logger, uuidcode, app_database, user_id, servername)
        log_dir = Path(os.path.join(config.get('jobs_path', '<no_jobs_path>'), "{}-{}".format(email, containername)))
        try:
            os.makedirs(log_dir, exist_ok=True)
            shutil.copy2(os.path.join(serverfolder, ".jupyterlabhub.log"), os.path.join(log_dir, "jupyterlabhub.log"))
        except:
            app_logger.exception("uuidcode={} - Could not copy log".format(uuidcode))
        
        jlab_output = "{};{};{}".format(userfolder,
                                        servername,
                                        running_no == 1)
        jlab_delete_path = config.get('jlab_delete', '<no_jlab_delete_defined>')
        app_logger.debug("uuidcode={} - Write {} to {}".format(uuidcode, jlab_output, os.path.join(jlab_delete_path, uuidcode)))
        with open(os.path.join(jlab_delete_path, uuidcode), 'w') as f:
            f.write(jlab_output)
            
    # Create folder for this JupyterLab
    if not serverfolder.exists():
        b2drop = Path(os.path.join(serverfolder, "B2DROP"))
        hpcmount = Path(os.path.join(serverfolder, "HPCMOUNT"))
        projects = Path(os.path.join(serverfolder, "Projects"))
        myprojects = Path(os.path.join(projects, "MyProjects"))
        sharedprojects = Path(os.path.join(projects, "SharedProjects"))
        serverfolder.mkdir()
        os.chmod(serverfolder, 0o777)
        b2drop.mkdir()
        os.chown(b2drop, 1000, 100)
        hpcmount.mkdir()
        os.chown(hpcmount, 1000, 100)
        projects.mkdir()
        os.chown(projects, 1000, 100)
        myprojects.mkdir()
        os.chown(myprojects, 1000, 100)
        sharedprojects.mkdir()
        os.chown(sharedprojects, 1000, 100)
    
    # Copy files to user home
    if service == "Dashboard":
        app_logger.debug("{} - Try to copy base_home/.config_{}.py and base_home/.start_{}.sh".format(uuidcode, dashboard.replace(" ", "_"), dashboard.replace(" ", "_")))
        base_start_sh = Path(os.path.join(basefolder, "base_home", ".start_{}.sh".format(dashboard.replace(" ", "_"))))
        base_config_py = Path(os.path.join(basefolder, "base_home", ".config_{}.py".format(dashboard.replace(" ", "_"))))
    else:
        base_config_py = Path(os.path.join(basefolder, "base_home", ".config.py"))
        base_start_sh = Path(os.path.join(basefolder, "base_home", ".start.sh"))
    user_start_sh = Path(os.path.join(serverfolder, ".start.sh"))
    shutil.copy2(base_start_sh, user_start_sh)
    os.chown(user_start_sh, 1000, 100)
    user_config_py = Path(os.path.join(serverfolder, ".config.py"))
    shutil.copy2(base_config_py, user_config_py)
    os.chown(user_config_py, 1000, 100)
    base_jovyan = Path(os.path.join(basefolder, "base_home", ".who_is_jovyan.txt"))
    user_jovyan = Path(os.path.join(serverfolder, ".who_is_jovyan.txt"))
    shutil.copy2(base_jovyan, user_jovyan)
    os.chown(user_jovyan, 1000, 100)
    base_mounthpc_sh = Path(os.path.join(basefolder, "base_home", "mount_hpc.sh"))
    user_mounthpc_sh = Path(os.path.join(serverfolder, "mount_hpc.sh"))
    shutil.copy2(base_mounthpc_sh, user_mounthpc_sh)
    os.chown(user_mounthpc_sh, 1000, 100)
    base_manageprojects_sh = Path(os.path.join(basefolder, "base_home", "manage_projects.sh"))
    user_manageprojects_sh = Path(os.path.join(serverfolder, "manage_projects.sh"))
    shutil.copy2(base_manageprojects_sh, user_manageprojects_sh)
    os.chown(user_manageprojects_sh, 1000, 100)
    base_faq_ipynb = Path(os.path.join(basefolder, "base_home", "FAQ.ipynb"))
    user_faq_ipynb = Path(os.path.join(serverfolder, "FAQ.ipynb"))
    shutil.copy2(base_faq_ipynb, user_faq_ipynb)
    os.chown(user_faq_ipynb, 1000, 100)
    

def create_user(app_logger, uuidcode, app_database, quota_config, email, basefolder, userfolder):
    user_id = utils_db.get_user_id(app_logger, uuidcode, app_database, email)
    if user_id != 0:
        return user_id, False
    utils_db.create_user(app_logger, uuidcode, app_database, email)
    user_id = utils_db.get_user_id(app_logger, uuidcode, app_database, email)
    create_base_dirs(app_logger, uuidcode, basefolder, userfolder)
    #setup_base_quota(app_logger, uuidcode, quota_config, basefolder, userfolder, email)
    return user_id, True


def create_base_dirs(app_logger, uuidcode, basefolder, userfolder):
    work = Path(os.path.join(userfolder, "work"))
    projects = Path(os.path.join(userfolder, "Projects"))
    myproject = Path(os.path.join(projects, "MyProjects"))
    sharedproject = Path(os.path.join(projects, "SharedProjects"))    
    projects_txt = Path(os.path.join(userfolder, "projects.txt"))
    share = Path(os.path.join(projects, ".share"))
    share_result = Path(os.path.join(projects, ".share_result"))
    hpc_mount = Path(os.path.join(work, ".hpc_mount"))
    base_mount_judac_sh = Path(os.path.join(basefolder, "base_home", "mount_judac.sh"))
    user_mount_judac_sh = Path(os.path.join(hpc_mount, "mount_judac.sh"))
    upload = Path(os.path.join(hpc_mount, ".upload"))
    davfs2 = Path(os.path.join(work, ".davfs2"))
    base_secrets = Path(os.path.join(basefolder, "base_home", "secrets"))
    user_secrets = Path(os.path.join(davfs2, "secrets"))
    work.mkdir(parents=True)
    projects.mkdir()
    projects_txt.touch()
    myproject.mkdir()
    sharedproject.mkdir()
    share.mkdir()
    share_result.mkdir()
    hpc_mount.mkdir()
    os.chown(hpc_mount, 1000, 100)
    shutil.copy2(base_mount_judac_sh, user_mount_judac_sh)
    os.chown(user_mount_judac_sh, 1000, 100)
    upload.mkdir()
    os.chown(upload, 1000, 100)
    davfs2.mkdir()
    os.chown(davfs2, 1000, 100)
    shutil.copy2(base_secrets, user_secrets)
    os.chown(user_secrets, 1000, 100)
    os.chmod(user_secrets, 0o600)
    
def get_slave_infos(app_logger, uuidcode, app_database, servername, email):
    user_id = utils_db.get_user_id(app_logger, uuidcode, app_database, email)
    results = utils_db.get_container_info(app_logger, uuidcode, app_database, user_id, servername)
    if len(results) > 0:
        slave_id, containername = results
    else:
        return []
    slave_hostname = utils_db.get_slave_hostname(app_logger, uuidcode, app_database, slave_id)
    running_no = utils_db.get_user_running(app_logger, uuidcode, app_database, user_id)
    return user_id, slave_id, slave_hostname, containername, running_no


def cancel(app_logger, uuidcode, app_hub_cancel_url, jhubtoken, errormsg, username, server_name):
    app_logger.debug("uuidcode={} - Send cancel to JupyterHub".format(uuidcode))
    hub_header = {"Authorization": "token {}".format(jhubtoken),
                  "uuidcode": uuidcode,
                  "Error": errormsg,
                  "Stopped": "True"}
    try:
        app_logger.info("uuidcode={} - Cancel JupyterHub Server".format(uuidcode))
        url = app_hub_cancel_url
        if ':' in server_name:
            server_name = server_name.split(':')[1]
        url = url + '/' + username
        if server_name != '':
            url = url + '/' + server_name
        with closing(requests.delete(url,
                                     headers = hub_header,
                                     verify = False,
                                     timeout = 1800)) as r:
            if r.status_code == 202:
                app_logger.trace("uuidcode={} - Cancel successful: {} {} {}".format(uuidcode, r.text, r.status_code, r.headers))
                return
            else:
                app_logger.warning("uuidcode={} - JupyterHub.cancel sent wrong status_code: {} {} {}".format(uuidcode, r.text, r.status_code, remove_secret(r.headers)))
    except requests.exceptions.ConnectTimeout:
        app_logger.exception("uuidcode={} - Timeout (1800) reached. Could not send cancel to JupyterHub".format(uuidcode))
    except:
        app_logger.exception("uuidcode={} - Could not send cancel to JupyterHub".format(uuidcode))
