from jupyterhub.handlers.pages import SpawnHandler

from jupyterhub.utils import url_path_join
from jupyterhub.utils import maybe_future

from tornado import web

class DirectSpawnHandler(SpawnHandler):
    @web.authenticated
    async def get(self, for_user=None, server_name=''):
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

        if spawner.ready:
            self.log.warning( "%s is already running" % (spawner._log_name) )
            # raise web.HTTPError(400, "%s is already running" % (spawner._log_name))
        elif spawner.pending:
            self.log.warning( "%s is pending %s" % (spawner._log_name, spawner.pending) )
            # raise web.HTTPError(
            #     400, "%s is pending %s" % (spawner._log_name, spawner.pending)
            # )
        else:
            options = spawner.orm_spawner.user_options
            self.log.info(options)
            if not options:
                options = {}
                for _key, _value in self.request.query_arguments.items():
                    if _key in ["service", "system", "account", "project", "partition", "reservation"]:
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

            # Update vo to current one
            auth_state = await user.get_auth_state()
            options["vo_active_input"] = auth_state["vo_active"]

            try:
                if not options:
                    raise web.HTTPError(404, "Servername %s is unknown and required arguments were not passed. Please use at least the following arguments: [service, system, account, project, partition]" % (server_name) )
                try:
                    await self.spawn_single_user(user, server_name=server_name, options=options)
                except web.HTTPError:
                    del user.spawners[server_name]
                    await self.spawn_single_user(user, server_name=server_name, options=options)
            except Exception as e:
                self.log.exception(
                    "Failed to spawn single-user server with form"
                )
                spawner_options_form = await user.spawner.get_options_form()
                form = await self._render_form(
                    for_user=user, spawner_options_form=spawner_options_form, message=str(e)
                )
                self.finish(form)
                return
            if current_user is user:
                self.set_login_cookie(user)
        next_url = self.get_next_url(
            user,
            default=url_path_join(
                self.hub.base_url, "spawn-pending", user.escaped_name, server_name
            ),
        )
        self.redirect(next_url)
