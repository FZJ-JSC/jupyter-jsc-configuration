'''
Created on Feb 12, 2020

@author: Tim Kreuzer
'''

import json

def get_j4j_dockermaster_token():
    with open('/etc/j4j/j4j_mount/j4j_token/dockermaster.token', 'r') as f:
        token = f.read().rstrip()
    return token

def get_j4j_dockerspawner_token():
    with open('/etc/j4j/j4j_mount/j4j_token/dockerspawner.token', 'r') as f:
        token = f.read().rstrip()
    return token

def get_quota_config():
    with open('/etc/j4j/j4j_mount/j4j_docker/master/quota.json', 'r') as f:
        ret = json.load(f)
    return ret

def get_general_config():
    with open('/etc/j4j/j4j_mount/j4j_docker/master/config.json', 'r') as f:
        ret = json.load(f)
    return ret


## only for upload_pub_key
def get_jhub_token():
    with open('/etc/j4j/j4j_mount/j4j_token/jhub.token', 'r') as f:
        token = f.read().rstrip()
    return token

