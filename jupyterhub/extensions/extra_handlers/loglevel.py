import logging
import json
import os

from tornado import web
from tornado.httpclient import HTTPRequest, HTTPClientError

from jupyterhub.apihandlers.base import APIHandler

class LogLevelAPIHandler(APIHandler):
    @web.authenticated
    async def post(self, handler, loglevel):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return
        log = logging.getLogger("JupyterHub")
        loglevel = loglevel.upper()
        if loglevel in ["NOTSET", "0"]:
            loglevel = "NOTSET"
            level = 0
        elif loglevel in ["TRACE", "5"]:
            loglevel = "TRACE"
            level = 5
        elif loglevel in ["DEBUG", "10"]:
            loglevel = "DEBUG"
            level = 10
        elif loglevel in ["INFO", "20"]:
            loglevel = "INFO"
            level = 20
        elif loglevel in ["WARNING", "30"]:
            loglevel = "WARNING"
            level = 30
        elif loglevel in ["ERROR", "40"]:
            loglevel = "ERROR"
            level = 40
        elif loglevel in ["CRITICAL", "FATAL", "50"]:
            loglevel = "CRITICAL"
            level = 50
        if handler == "root":
            log.setLevel(level)
        elif handler.lower() in ["smtp", "mail", "email"]:
            for _handler in log.handlers:
                if _handler.__class__.__name__ == "SafeToCopySMTPHandler":
                    _handler.setLevel(level)
                    os.environ["LOGGING_MAIL_LOGLEVEL"] = str(loglevel)
        elif handler == "file":
            for _handler in log.handlers:
                if _handler.__class__.__name__ == "SafeToCopyFileHandler":
                    _handler.setLevel(level)
                    os.environ["LOGGING_FILE_LOGLEVEL"] = str(loglevel)
        elif handler.lower() in ["stream", "console"]:
            for _handler in log.handlers:
                if _handler.__class__.__name__ == "StreamHandler":
                    _handler.setLevel(level)
                    os.environ["LOGGING_STREAM_LOGLEVEL"] = str(loglevel)
        elif handler.lower() in ["syslog", "splunk"]:
            for _handler in log.handlers:
                if _handler.__class__.__name__ == "SafeToCopySysLogHandler":
                    _handler.setLevel(level)
                    os.environ["LOGGING_SYSLOG_LOGLEVEL"] = str(loglevel)
        log.info(
            "LogLevel for {} switched to {}".format(handler, level),
            extra={"class": self.__class__.__name__},
        )
        self.set_status(200)
        self.finish()

    @web.authenticated
    async def get(self):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return

        loglevels = {
            "stream": os.environ["LOGGING_STREAM_LOGLEVEL"],
            "file": os.environ["LOGGING_FILE_LOGLEVEL"],
            "mail": os.environ["LOGGING_MAIL_LOGLEVEL"],
            "syslog": os.environ["LOGGING_SYSLOG_LOGLEVEL"]
        }
        return self.write(json.dumps(loglevels))


class BaseLogLevelAPIHandler(APIHandler):
    @web.authenticated
    async def post(self, handler, loglevel):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return

        if os.environ.get("BACKEND_SECRET", None):
            headers = {"Backendsecret": os.environ.get("BACKEND_SECRET")}
        loglevel_url = self.logging_url + f"/{handler}/{loglevel}"
        req = HTTPRequest(
            loglevel_url,
            method="POST",
            body="{}",
            headers=headers,
            connect_timeout=2,
            request_timeout=2
        )
        try:
            resp = await user.authenticator.fetch(req)
            self.set_status(200)
        except HTTPClientError as e:
            self.set_status(e.code)

    @web.authenticated
    async def get(self):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return

        if os.environ.get("BACKEND_SECRET", None):
            headers = {"Backendsecret": os.environ.get("BACKEND_SECRET")}
        req = HTTPRequest(
                self.logging_url,
                method="GET",
                headers=headers,
                connect_timeout=2,
                request_timeout=2
            )
        try:
            resp = await user.authenticator.fetch(req)
            self.set_status(200)
            return self.write(resp)
        except HTTPClientError as e:
            self.set_status(e.code)


class BaseLoggerAPIHandler(APIHandler):
    @web.authenticated
    async def get(self, handler):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return

        if os.environ.get("BACKEND_SECRET", None):
            headers = {"Backendsecret": os.environ.get("BACKEND_SECRET")}
        req = HTTPRequest(
                self.logging_url + f"/{handler}",
                method="GET",
                headers=headers,
                connect_timeout=10,
                request_timeout=10
            )
        try:
            resp = await user.authenticator.fetch(req)
            self.set_status(200)
            return self.write(resp)
        except HTTPClientError as e:
            self.set_status(e.code)

    @web.authenticated
    async def patch(self, handler, loglevel):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return

        if os.environ.get("BACKEND_SECRET", None):
            headers = {"Backendsecret": os.environ.get("BACKEND_SECRET")}
        req = HTTPRequest(
                self.logging_url + f"/{handler}/{loglevel}",
                method="PATCH",
                headers=headers,
                body="{}",
                connect_timeout=10,
                request_timeout=10
            )
        try:
            resp = await user.authenticator.fetch(req)
            self.set_status(200)
        except HTTPClientError as e:
            self.set_status(e.code)
    
    @web.authenticated
    async def post(self, handler, loglevel, formatter, *argv):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return

        if os.environ.get("BACKEND_SECRET", None):
            headers = {"Backendsecret": os.environ.get("BACKEND_SECRET")}
        
        if handler == "stream":
            url = self.logging_url + f"/{handler}/{loglevel}/{formatter}"
        elif handler == "file":
            url = self.logging_url + f"/{handler}/{loglevel}/{formatter}/{argv[0]}"
        elif handler == "mail":
            url = self.logging_url + f"/{handler}/{loglevel}/{formatter}/{argv[0]}/{argv[1]}/{argv[2]}/{argv[3]}"
        elif handler == "syslog":
            url = self.logging_url + f"/{handler}/{loglevel}/{formatter}/{argv[0]}/{argv[1]}/{argv[2]}/{argv[3]}/{argv[4]}/{argv[5]}"

        req = HTTPRequest(
                url,
                method="POST",
                headers=headers,
                body="{}",
                connect_timeout=10,
                request_timeout=10
            )
        try:
            resp = await user.authenticator.fetch(req)
            self.set_status(200)
        except HTTPClientError as e:
            self.set_status(e.code)

    @web.authenticated
    async def delete(self, handler):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return

        if os.environ.get("BACKEND_SECRET", None):
            headers = {"Backendsecret": os.environ.get("BACKEND_SECRET")}
        req = HTTPRequest(
                self.logging_url + f"/{handler}",
                method="DELETE",
                headers=headers,
                connect_timeout=10,
                request_timeout=10
            )
        try:
            resp = await user.authenticator.fetch(req)
            self.set_status(200)
        except HTTPClientError as e:
            self.set_status(e.code)


class BackendLogLevelAPIHandler(BaseLogLevelAPIHandler):
    logging_url = os.environ.get("BACKEND_URL_LOGLEVEL")

class BackendLoggerAPIHandler(BaseLoggerAPIHandler):
    logging_url = os.environ.get("BACKEND_URL_LOGGER")

class TunnelingLogLevelAPIHandler(BaseLogLevelAPIHandler):
    logging_url = os.environ.get("TUNNELING_URL_LOGGING")

class UserlabsMgrLogLevelAPIHandler(BaseLogLevelAPIHandler):
    logging_url = os.environ.get("USERLABSMGR_URL_LOGGING")

class JUSUFCloudLogLevelAPIHandler(BaseLogLevelAPIHandler):
    logging_url = os.environ.get("JUSUFCLOUD_URL_LOGGING")