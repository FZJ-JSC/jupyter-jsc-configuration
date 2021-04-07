import os

from tornado import web

from jupyterhub.apihandlers.base import APIHandler
from jupyterhub.utils import auth_decorator


@auth_decorator
def secret_authenticated(self):
    """Decorator for method authenticated only by Authorization token header
    (no cookies)
    """
    auth = self.request.headers.get("Authorization")
    if not auth:
        raise web.HTTPError(403)
    if not auth.startswith("token "):
        raise web.HTTPError(403)
    secret = auth.split()[1]
    if secret != os.environ.get("AUTH_SECRET"):
        raise web.HTTPError(403)


class HPCUpdateHandler(APIHandler):
    @secret_authenticated
    async def post(self, username):
        user = self.find_user(username)
        if user is None:
            self.set_status(404)
            return
        auth_state = await user.get_auth_state()
        if auth_state and auth_state.get("oauth_user", {}).get(
            "hpc_infos_attribute", []
        ):
            # User is logged in
            body = self.get_json_body()
            if body:
                auth_state["oauth_user"]["hpc_infos_attribute"] = body
            else:
                auth_state["oauth_user"]["hpc_infos_attribute"] = []
        self.set_status(200)
        return
