import logging
import os
import sys

path = os.environ.get("JUPYTER_JSC_PATH")
sys.path.insert(1, path)

c = get_config()
c.JupyterHub.log_level = logging.DEBUG
c.JupyterHub.log_format = "%(asctime)s,%(msecs).03d, Levelno=%(levelno)s, Level=%(levelname)s, Logger=%(name)s, File=%(filename)s, Line=%(lineno)d, %(message)s"

c.JupyterHub.last_activity_interval = 60
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_port = 8001
c.JupyterHub.port = 8000

hcip = os.environ.get("JUPYTERHUB_CONNECT_IP")
c.JupyterHub.hub_connect_ip = f"{hcip}"

c.JupyterHub.shutdown_on_logout = True
c.JupyterHub.init_spawners_timeout = 100
c.JupyterHub.cleanup_proxy = False
c.ConfigurableHTTPProxy.should_start = False
proxy_url = os.environ.get("PROXY_URL")
c.ConfigurableHTTPProxy.api_url = f"{proxy_url}"

c.JupyterHub.statsd_host = "graphite210419"

c.JupyterHub.strict_session_ids = True
c.JupyterHub.logout_on_all_devices = False
c.JupyterHub.logout_on_all_devices_argname = "alldevices"

db_host = os.environ.get("JUPYTERHUB_DB_HOST")
db_port = os.environ.get("JUPYTERHUB_DB_PORT")
db_user = os.environ.get("JUPYTERHUB_DB_USER")
db_password = os.environ.get("JUPYTERHUB_DB_PASSWD")
db_database = os.environ.get("JUPYTERHUB_DB_DATABASE")
c.JupyterHub.db_url = (
    f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}"
)

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

from authenticator import unity
from unicorespawner import functions
from jupyterhub.spawner import BackendSpawner

c.JupyterHub.allow_named_servers = True
c.JupyterHub.spawner_class = BackendSpawner

backend_url_port = os.environ.get("BACKEND_URL_PORT")
c.BackendSpawner.request_port_url = backend_url_port

backend_url_job = os.environ.get("BACKEND_URL_JOB")
c.BackendSpawner.backend_url = backend_url_job

backend_spawner_ip = os.environ.get("BACKEND_SPAWNER_IP")
c.BackendSpawner.backend_spawner_ip = backend_spawner_ip

c.BackendSpawner.http_timeout = 43200
c.BackendSpawner.poll_interval = 0
c.BackendSpawner.cancel_progress_activation = 25

c.BackendSpawner.options_from_query = functions.options_from_query
c.BackendSpawner.options_from_form = functions.options_from_form
c.BackendSpawner.options_form = functions.options_form


c.JupyterHub.tornado_settings = {"slow_spawn_timeout": 0, "version_hash": ""}

c.JupyterHub.cookie_secret_file = os.environ.get("COOKIE_SECRET_PATH")


c.JupyterHub.authenticator_class = unity.UnityOAuthenticator
c.UnityOAuthenticator.extra_authorize_params = dict(
    (x, y)
    for x, y in (
        element.split("=")
        for element in os.environ.get("EXTRA_AUTHORIZE_PARAMS").split(",")
    )
)
c.UnityOAuthenticator.extra_authorize_params_allowed_arguments = dict(
    uy_select_authn=["jupyterhdfaaiAuthn.hdf", "jupyterldapAuthn.password"]
)
c.UnityOAuthenticator.enable_auth_state = True
c.UnityOAuthenticator.client_id = os.environ.get("CLIENT_ID")
c.UnityOAuthenticator.client_secret = os.environ.get("CLIENT_SECRET")
c.UnityOAuthenticator.oauth_callback_url = os.environ.get("CALLBACK_URL")
c.UnityOAuthenticator.authorize_url = os.environ.get("AUTHORIZE_URL")
c.UnityOAuthenticator.token_url = os.environ.get("TOKEN_URL")
c.UnityOAuthenticator.tokeninfo_url = os.environ.get("TOKENINFO_URL")
c.UnityOAuthenticator.userdata_url = os.environ.get("USERDATA_URL")
c.UnityOAuthenticator.username_key = "username_attr"
c.UnityOAuthenticator.scope = os.environ.get("SCOPE").split(";")
c.UnityOAuthenticator.admin_users = set(os.environ.get("ADMIN_USERS").split(";"))
c.UnityOAuthenticator.post_auth_hook = unity.post_auth_hook

## We use JupyterHub-idle-culler ( https://pypi.org/project/jupyterhub-idle-culler/ ) to remove unused JupyterLabs
c.JupyterHub.services = []
if os.environ.get("IDLE_CULLER_ENABLED", "false").lower() in ["true", "1"]:
    cull_cmd = [
        "python3",
        "-m",
        "jupyterhub_idle_culler",
        "--url=http://localhost:8001/hub/api",
        "--timeout=86400",
        "--cull-every=300",
        "--concurrency=5",
    ]
    c.JupyterHub.services.append(
        {
            "name": "cull-idle",
            "admin": True,
            "command": cull_cmd,
        }
    )

from extra_handlers import (
    setuptunnel,
    unicorenotification,
    twoFA,
    direct,
    projects,
    vo,
    refresh_hpc_accounts,
    sites,
)
from jupyterhub.handlers import pages

c.JupyterHub.extra_handlers = [
    (
        r"/api/tunneling/([^/]+)/([^/]+)/([^/]+)/([^/]+)/([^/]+)",
        setuptunnel.SetupTunnelAPIHandler,
    ),
    (r"/api/vo/([^/]+)", vo.VOAPIHandler),
    (r"/api/votoken/([^/]+)", vo.VOTokenAPIHandler),
    (
        r"/api/unicorenotification/([^/]+)",
        unicorenotification.UNICORENotificationAPIHandler,
    ),
    (
        r"/api/unicorenotification/([^/]+)/([^/]+)",
        unicorenotification.UNICORENotificationAPIHandler,
    ),
    (
        r"/api/unicorenotification/([^/]+)/",
        unicorenotification.UNICORENotificationAPIHandler,
    ),
    (
        r"/api/unicorenotification/([^/]+)/([^/]+)/",
        unicorenotification.UNICORENotificationAPIHandler,
    ),
    (r"/api/2FA", twoFA.TwoFAAPIHandler),
    (r"/api/project_shares/([^/]+)/([^/]+)/([^/]+)", projects.ProjectSharesAPIHandler),
    (r"/api/project_shares/([^/]+)/([^/]+)", projects.ProjectSharesAPIHandler),
    (r"/api/project_shares/([^/]+)", projects.ProjectSharesAPIHandler),
    (r"/api/project_shares", projects.ProjectSharesAPIHandler),
    (r"/api/projects/([^/]+)/([^/]+)/([^/]+)", projects.ProjectsAPIHandler),
    (r"/api/projects/([^/]+)/([^/]+)", projects.ProjectsAPIHandler),
    (r"/api/projects/([^/]+)", projects.ProjectsAPIHandler),
    (r"/api/projects", projects.ProjectsAPIHandler),
    (r"/api/refreshhpc/([^/]+)", refresh_hpc_accounts.HPCUpdateHandler),
    (r"/direct/([^/]+)/([^/]+)", direct.DirectSpawnHandler),
    (r"/groups", vo.VOHandler),
    (r"/terms", sites.ToSHandler),
    (r"/imprint", sites.ImprintHandler),
    (r"/privacy", sites.DPSHandler),
    (r"/2FA", twoFA.TwoFAHandler),
    (r"/2FA/([^/]+)", twoFA.TwoFACodeHandler),
    (r"/signout", unity.BackendLogoutHandler),
    (r"/start", pages.HomeHandler),
]
