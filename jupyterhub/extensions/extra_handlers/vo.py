import json
import logging
import os

from tornado import web

from jupyterhub.apihandlers.base import APIHandler
from jupyterhub.handlers.base import BaseHandler
from jupyterhub.jupyterjsc.utils.vo import get_vos
from jupyterhub.utils import token_authenticated


class VOHandler(BaseHandler):
    @web.authenticated
    async def get(self):
        user = self.current_user
        auth_state = await user.get_auth_state()
        vo_active, vo_available = get_vos(
            auth_state, user.name, user.admin, auth_state["vo_active"]
        )
        auth_state["vo_active"] = vo_active
        auth_state["vo_available"] = vo_available
        await user.save_auth_state(auth_state)
        vo_details_file = os.environ.get("VO_CONFIG_PATH")
        with open(vo_details_file, "r") as f:
            vo_details_config = json.load(f)
        vo_details = {}
        for vo_name in auth_state.get("vo_available", []):
            vo_details[vo_name] = (
                vo_details_config.get(vo_name, {})
                .get("description", "No description available")
            )
        vo_active = auth_state.get("vo_active", "")
        html = await self.render_template(
            "vo_info.html",
            auth_state=auth_state,
            user=user,
            vo_active=vo_active,
            vo_details=vo_details,
        )
        self.finish(html)


class VOAPIHandler(APIHandler):
    @web.authenticated
    async def post(self, group):
        user = self.current_user
        # user = self.get_current_user_token()
        state = await user.get_auth_state()
        if group in state.get("vo_available", []):
            state["vo_active"] = group
            await user.save_auth_state(state)
        else:
            self.log.debug(
                "{} not part of list {}".format(group, state.get("vo_available", []))
            )
            self.set_status(403)
            return
        self.set_status(204)
        return


class VOTokenAPIHandler(APIHandler):
    @token_authenticated
    async def post(self, group):
        user = self.get_current_user_token()
        state = await user.get_auth_state()
        if group in state.get("vo_available", []):
            state["vo_active"] = group
            await user.save_auth_state(state)
        else:
            self.log.debug(
                "{} not part of list {}".format(group, state.get("vo_available", []))
            )
            self.set_status(403)
            return
        self.set_status(204)
        return
