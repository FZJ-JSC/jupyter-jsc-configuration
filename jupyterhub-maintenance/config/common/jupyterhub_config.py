import logging
import os

c = get_config()
c.JupyterHub.log_level = logging.DEBUG
c.JupyterHub.log_format = "%(asctime)s,%(msecs).03d, Levelno=%(levelno)s, Level=%(levelname)s, Logger=%(name)s, File=%(filename)s, Line=%(lineno)d, %(message)s"

# c.JupyterHub.last_activity_interval = 60
c.JupyterHub.hub_ip = "0.0.0.0"

hcip = os.environ.get("JUPYTERHUB_CONNECT_IP")
c.JupyterHub.hub_connect_ip = f"{hcip}"

# c.JupyterHub.template_paths = ["/mnt/data/templates"]
c.JupyterHub.data_files_path = os.environ.get("DATA_FILES_PATH")
c.JupyterHub.default_url = "/hub/home"
c.JupyterHub.jinja_environment_options = {
    "extensions": [
        "jinja2.ext.do",
        "jinja2.ext.loopcontrols",
        "jinja2_ansible_filters.AnsibleCoreFiltersExtension",
    ]
}

import uuid

c.JupyterHub.cookie_secret_file = "{}".format(uuid.uuid4().hex)
