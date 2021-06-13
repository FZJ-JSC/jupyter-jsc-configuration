from urllib.parse import urlencode

from tornado import web

from jupyterhub import orm
from jupyterhub.handlers.pages import SpawnHandler
from jupyterhub.utils import maybe_future
from jupyterhub.utils import url_path_join


class DirectSpawnHandler(SpawnHandler):
    @web.authenticated
    async def get(self, for_user=None, server_name=""):
        """GET spawns with user-specified options"""
        user = current_user = self.current_user
        if for_user is not None and for_user != user.name:
            if not user.admin:
                raise web.HTTPError(
                    403, "Only admins can spawn on behalf of other users"
                )
            user = self.find_user(for_user)
            if user is None:
                raise web.HTTPError(404, "No such user: %s" % for_user)

        spawner = user.spawners[server_name]
        options = spawner.orm_spawner.user_options
        if not options:
            options = {}
            for _key, _value in self.request.query_arguments.items():
                if _key in [
                    "service",
                    "system",
                    "account",
                    "project",
                    "partition",
                    "reservation",
                ]:
                    key = f"{_key}_input"
                elif _key in ["Runtime", "Nodes", "GPUS"]:
                    key = f"resource_{_key}"
                else:
                    self.log.warning(f"Unknown argument key {_key}")
                    continue
                value = [v.decode("utf-8") for v in _value]
                if value[0].lower() == "none":
                    continue
                options[key] = value

        default = url_path_join(
            self.hub.base_url, "spawn", user.escaped_name, server_name
        )

        if options:
            auth_state = await user.get_auth_state()
            options["vo_active_input"] = auth_state.get("vo_active", "default")
            query_args = urlencode(options)
            default = f"{default}?{query_args}"

        next_url = self.get_next_url(user, default=default)
        self.redirect(next_url)
        return
