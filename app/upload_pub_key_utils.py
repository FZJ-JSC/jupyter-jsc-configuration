import requests
import json
import urllib3
from time import sleep
from contextlib import closing
from app import utils_file_loads

def upload_pub_key(app_logger, uuidcode, system, uid, service_prefix, api_url, jhub_token):
    try:        
        api_url = 'https://jupyter-jsc.fz-juelich.de/' + '/'.join(api_url.split(':')[2].split('/')[1:])
        email = list(filter(None, service_prefix.split('/')))[-2]
        workdir = "/etc/j4j/j4j_hdfcloud/{}/work".format(email.replace('@', '_at_'))
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        itoken = utils_file_loads.get_jhub_token()
        with open('{}/.hpc_mount/id_rsa.pub'.format(workdir), 'r') as file:
            pubkey = file.read().rstrip()
        pubkey = 'no-pty,no-port-forwarding ' + ' '.join(pubkey.split(' ')[:2])
        url = api_url + '/token/' + '/'.join(list(filter(None, service_prefix.split('/')))[-2:])
        tokens = {}
        app_logger.debug("uuidcode={} - Get accesstoken".format(uuidcode))
        # Initial call to print 0% progress
        try:
            with closing(requests.get(url,
                                      headers={'Internal-Authorization': itoken,
                                               'Authorization': 'token {}'.format(jhub_token),
                                               'renew': 'True',
                                               'accounts': 'True'},
                                      verify=False)) as r:
                if r.status_code != 201:
                    app_logger.error("uuidcode={} - Could not get accesstoken from JupyterHub: {} {}".format(uuidcode, r.text, r.status_code))
                    return 500
                else:
                    tokens = json.loads(r.text)
        except:
            app_logger.exception("uuidcode={} - Could not get accesstoken from JupyterHub.".format(uuidcode))
            return 500            
        user_accs = {}
        for line in tokens.get('oauth_user', {}).get('hpc_infos_attribute', []):
            account, system_partition, project = line.split(',')[:3]
            if '_' in system_partition:
                system = system_partition.split('_')[0]
            else:
                system = system_partition
            if system.lower() not in user_accs.keys():
                user_accs[system.lower()] = {}
            if account.lower() not in user_accs[system.lower()].keys():
                user_accs[system.lower()][account.lower()] = []
            if project.lower() not in user_accs[system.lower()][account.lower()]:
                user_accs[system.lower()][account.lower()].append(project.lower())
        group = None
        hpc_url = None

        if 'jureca' in user_accs.keys() and uid in user_accs.get('jureca').keys():
            if len(user_accs.get('jureca').get(uid)) > 0:
                group = sorted(user_accs.get('jureca').get(uid))[0]
                hpc_url = "https://zam2125.zam.kfa-juelich.de:9112/FZJ_JURECA/rest/core/jobs"
        if 'juwels' in user_accs.keys() and uid in user_accs.get('juwels').keys() and hpc_url == None:
            if len(user_accs.get('juwels').get(uid)) > 0:
                group = sorted(user_accs.get('juwels').get(uid))[0]
                hpc_url = "https://zam2125.zam.kfa-juelich.de:9112/JUWELS/rest/core/jobs"
        if 'juron' in user_accs.keys() and uid in user_accs.get('juron').keys() and hpc_url == None:
            if len(user_accs.get('juron').get(uid)) > 0:
                group = sorted(user_accs.get('juron').get(uid))[0]
                hpc_url = "https://zam2125.zam.kfa-juelich.de:9112/JURON/rest/core/jobs"
        if hpc_url == None:
            app_logger.debug("uuidcode={} - We don't know any of the Users HPC Accounts -> Cancel {}".format(uuidcode, tokens.get('oauth_user', {})))
            return 501

        app_logger.debug("uuidcode={} - Use system: {}, account: {}, project: {}".format(uuidcode, hpc_url, uid, group))

        headers = { 'Accept': 'application/json',
                    'X-UNICORE-User-Preferences': 'uid:{},group:{}'.format(uid, group),
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer {}'.format(tokens.get('accesstoken')) }
        unicore_job = {
                       "ApplicationName": "Jupyter4JSC HPC Mount",
                       "haveClientStageIn": "true",
                       "Executable": "bash .upload.sh",
                       "Environment":
                           {
                               "UC_PREFER_INTERACTIVE_EXECUTION": "true"
                           }
                      }

        inputs = []
        inputs.append( { "To": ".pub.key", "Data": pubkey } )
        inputs.append( { "To": ".upload.sh", "Data": "#!/bin/bash\necho \"#### Jupyter@JSC mount public key\" >> ${HOME}/../judac/.ssh/authorized_keys\ncat .pub.key >> ${HOME}/../judac/.ssh/authorized_keys\necho -e \"\n#### Jupyter@JSC mount public key end\" >> ${HOME}/../judac/.ssh/authorized_keys\necho \".end\" > .end" } )

        # Submit UNICORE Job
        try:
            with closing(requests.post(hpc_url, headers=headers, json=unicore_job, verify=False)) as r:
                if r.status_code != 201:
                    app_logger.error("uuidcode={} - Could not submit UNICORE job: {} {}".format(uuidcode, r.status_code, r.text))
                    return 500
                else:
                    kernelurl = r.headers['Location']
                    headers['X-UNICORE-SecuritySession'] = r.headers['X-UNICORE-SecuritySession']
        except:
            app_logger.exception("uuidcode={} - Could not submit UNICORE job".format(uuidcode))
            return 500

        try:
            # Get workingDirectory of Job
            with closing(requests.get(kernelurl, headers=headers, verify=False)) as r:
                if r.status_code != 200:
                    app_logger.error("uuidcode={} - Could not get working directory: {} {}".format(uuidcode, r.status_code, r.text))
                    return 500
                else:
                    properties_json = json.loads(r.text)
        except:
            app_logger.exception("uuidcode={} - Could not get working directory".format(uuidcode))
            return 500
        # Upload files to Job
        headers['Content-Type'] = "application/octet-stream"
        for inp in inputs:
            try:
                with closing(requests.put(properties_json['_links']['workingDirectory']['href']+"/files/"+inp.get('To'), headers=headers, data=inp.get('Data'), verify=False)) as r:
                    if r.status_code != 204:
                        app_logger.error("uuidcode={} - Could not upload input files: {} {}".format(uuidcode, r.status_code, r.text))
                        return 500
            except:
                app_logger.exception("uuidcode={} - Could not upload input files.".format(uuidcode))
                return 500
        headers['Content-Type'] = "application/json"


        # Start Job
        try:
            with closing(requests.post(properties_json['_links']['action:start']['href'], headers=headers, data="{}", verify=False)) as r:
                if r.status_code != 200:
                    app_logger.error("uuidcode={} - Could not start job: {} {}".format(uuidcode, r.status_code, r.text))
                    return 500
        except:
            app_logger.exception("uuidcode={} - Could not start job".format(uuidcode))
            return 500
            
        # Get FileDirectory
        try:
            with closing(requests.get(properties_json['_links']['workingDirectory']['href'], headers=headers, verify=False)) as r:
                if r.status_code != 200:
                    app_logger.error("uuidcode={} - Could not get file directory: {} {}".format(uuidcode, r.status_code, r.text))
                    return 500
                else:
                    fileDir = json.loads(r.text)['_links']['files']['href']
        except:
            app_logger.exception("uuidcode={} - Could not get file directory".format(uuidcode))
            return 500
        finished = False
        count = 0
        while (not finished) and (count<30):
            try:
                with closing(requests.get(fileDir, headers=headers, verify=False)) as r:
                    if r.status_code != 200:
                        app_logger.error("uuidcode={} - Could not load file directory information: {} {}".format(uuidcode, r.status_code, r.text))
                        return 500
                    else:
                        childs = json.loads(r.text).get('children', [])
                        if '.end' in childs or '/.end' in childs:
                            finished = True
                        else:
                            count += 1
                            sleep(3)
            except:
                app_logger.exception("uuidcode={} - Could not load file directory information.".format(uuidcode))
                return 500
        try:
            with closing(requests.delete(kernelurl, headers=headers, verify=False)) as r:
                if r.status_code > 399:
                    app_logger.error("uuidcode={} - Could not delete UNICORE Job: {} {}".format(uuidcode, r.status_code, r.text))
                    return 500
        except:
            app_logger.exception("uuidcode={} - Could not delete UNICORE Job".format(uuidcode))
            return 500
        return 201
    except:
        app_logger.exception("Could not upload Public Key. Bugfix required")
        return 500
