from jupyterhub.handlers.base import BaseHandler


class ToSHandler(BaseHandler):
    async def get(self):
        user = self.current_user
        html = self.render_template("tos.html", user=user)
        self.finish(html)


class ImprintHandler(BaseHandler):
    async def get(self):
        user = self.current_user
        html = self.render_template("imprint.html", user=user)
        self.finish(html)


class DPSHandler(BaseHandler):
    async def get(self):
        user = self.current_user
        html = self.render_template("dps.html", user=user)
        self.finish(html)
