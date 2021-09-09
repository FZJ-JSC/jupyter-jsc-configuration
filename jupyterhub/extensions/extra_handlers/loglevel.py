import copy
import logging
import json
import urllib
import os
import socket
import struct

from tornado import web
from tornado.httpclient import HTTPRequest, HTTPClientError

from jupyterhub.apihandlers.base import APIHandler


class LoggerJHubAPIHandler(APIHandler):
    default_handler_configs = {
        "stream": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "level": 20,
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "simple",
            "level": 20,
            "filename": "tests/receiver.log",
            "when": "midnight",
            "backupCount": 7,
        },
        "mail": {
            "class": "logging.handlers.SMTPHandler",
            "formatter": "simple",
            "level": 20,
            "mailhost": "",
            "fromaddr": "",
            "toaddrs": [],
            "subject": "",
        },
        "syslog": {
            "class": "logging.handlers.SysLogHandler",
            "formatter": "json",
            "level": 20,
            "address": ["127.0.0.1", 514],
            "socktype": "ext://socket.SOCK_DGRAM",
        },
    }

    def validate_config(self, config, formatter=""):
        if "handlers" not in config:
            config["handlers"] = {}
        if "loggers" not in config:
            config["loggers"] = {"Receiver": {"handlers": [], "propagate": True}}
        elif "Receiver" not in config["loggers"]:
            config["loggers"]["Receiver"] = {"handlers": [], "propagate": True}
        elif "handlers" not in config["loggers"]["Receiver"]:
            config["loggers"]["Receiver"]["handlers"] = []
        if formatter and formatter not in config["formatters"]:
            raise Exception(f"Unknown formatter {formatter}")

    def store_and_send(self, config, config_file):
        to_save = json.dumps(config, indent=4, sort_keys=True)
        to_send = to_save.encode("utf-8")
        with open(config_file, "w") as f:
            f.write(to_save)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 56712))
        s.send(struct.pack(">L", len(to_send)))
        s.send(to_send)
        s.close()

    @web.authenticated
    async def get(self, handler=''):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return
      
        if handler == "test":
            self.log.trace("Trace")
            self.log.debug("Debug")
            self.log.info("Info")
            self.log.warning("Warning")
            self.log.error("Error")
            self.log.critical("Critical")
            self.set_status(200)
        else:
            try:
                self.log.trace(
                    "Get Logger",
                    extra={"handler": handler, "class": self.__class__.__name__},
                )
                config_file = os.environ.get("LOGGING_CONFIG_FILE")
                with open(config_file, "r") as f:
                    config = json.load(f)
                log_info = {}
                active_handlers = (
                    config.get("loggers", {}).get("Receiver", {}).get("handlers", [])
                )
                if handler:
                    log_info = copy.deepcopy(config.get("handlers", {}).get(handler, {}))
                    log_info["enabled"] = handler in active_handlers
                else:
                    for _handler, infos in config.get("handlers", {}).items():
                        log_info[_handler] = copy.deepcopy(infos)
                        log_info[_handler]["enabled"] = _handler in active_handlers
                self.write(json.dumps(log_info))
                self.set_status(200)
            except:
                self.log.exception("Nope")
                self.set_status(500)
        
    @web.authenticated
    async def patch(self, handler=''):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return
      
        data = self.request.body.decode("utf8")
        if type(data) != dict:
            try:
                data = json.loads(data)
            except:
                self.log.exception(
                    "Incoming data not correct",
                    extra={"class": self.__class__.__name__, "data": data},
                )
                self.set_status(400)
                return

        config_file = os.environ.get("LOGGING_CONFIG_FILE")
        with open(config_file, "r") as f:
            config = json.load(f)

        try:
            self.validate_config(config)
        except:
            self.set_status(400)
            return

        for key, value in data.items():
            if key == "enabled":
                if (
                    not value
                    and handler in config["loggers"]["Receiver"]["handlers"]
                ):
                    config["loggers"]["Receiver"]["handlers"].remove(handler)
                elif (
                    value
                    and handler not in config["loggers"]["Receiver"]["handlers"]
                ):
                    config["loggers"]["Receiver"]["handlers"].append(handler)
            else:
                config["handlers"][handler][key] = value

        self.store_and_send(config, config_file)
        self.set_status(200)

    @web.authenticated
    async def post(self, handler=''):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return
      
        data = self.request.body.decode("utf8")
        if type(data) != dict:
            try:
                data = json.loads(data)
            except:
                self.log.exception(
                    "Incoming data not correct",
                    extra={"class": self.__class__.__name__, "data": data},
                )
                self.set_status(400)
                return
        
        # We only use POST to create a new handler. We don't want previous configuration parts of
        # the same handler to be part of the new one.
        new_handler_config = copy.deepcopy(
            self.default_handler_configs.get(handler, {})
        )
        for key, value in data.items():
            new_handler_config[key] = value

        config_file = os.environ.get("LOGGING_CONFIG_FILE")
        with open(config_file, "r") as f:
            config = json.load(f)

        try:
            self.validate_config(config, new_handler_config["formatter"])
        except:
            self.set_status(400)
            return

        config["handlers"][handler] = new_handler_config
        try:
            if handler not in config.get("loggers", {}).get("Receiver", {}).get(
                "handlers", []
            ):
                config["loggers"]["Receiver"]["handlers"].append(handler)
        except:
            self.log.exception(
                "Could not add handler to list of handlers in Receiver logger"
            )
            self.set_status(400)
            return

        self.store_and_send(config, config_file)
        self.set_status(200)
    
    @web.authenticated
    async def delete(self, handler=''):
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return

        # Remove handler from list of handlers.
        # Delete handler configuration
        # To just disable handler use self.patch(...) with { "enabled": False } or { "level": 60 }
        config_file = os.environ.get("LOGGING_CONFIG_FILE")
        with open(config_file, "r") as f:
            config = json.load(f)

        if handler in config.get("handlers"):
            del config["handlers"][handler]

        if handler in config.get("loggers", {}).get("Receiver", {}).get(
            "handlers", []
        ):
            config["loggers"]["Receiver"]["handlers"].remove(handler)

        self.store_and_send(config, config_file)
        self.set_status(200)

class LoggerAPIHandler(LoggerJHubAPIHandler):
    def get_header(self):
        headers = { "Content-Type": "application/json" }
        if os.environ.get("BACKEND_SECRET", None):
            headers["Backendsecret"] = os.environ.get("BACKEND_SECRET")
        return headers

    def get_url(self, service, handler=''):
        settings = os.environ.get("LOGGING_SETTINGS_FILE", "/mnt/config/jupyterhub/config/logging/settings.json")
        with open(settings, "r") as f:
            config = json.load(f)

        if handler:
            url = config.get(service, {}).get(handler)
        else:
            url = config.get(service, {}).get("default")
        return url
        

    @web.authenticated
    async def get(self, service, handler=''):
        if service == "jhub":
            await super().get(handler)
            return

        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return

        url = self.get_url(service, handler)
        try:
            req = HTTPRequest(
                    url,
                    method="GET",
                    headers=self.get_header(),
                    connect_timeout=10,
                    request_timeout=10
                )
            resp = await user.authenticator.fetch(req)
            self.set_status(200)
            try:
                return self.write(resp)
            except TypeError:
                pass
        except HTTPClientError as e:
            self.set_status(e.code)

    @web.authenticated
    async def patch(self, service, handler=''):
        if service == "jhub":
            await super().patch(handler)
            return
        
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return

        url = self.get_url(service, handler)

        try:
            req = HTTPRequest(
                    url,
                    method="PATCH",
                    headers=self.get_header(),
                    body=self.request.body.decode("utf8"),
                    connect_timeout=10,
                    request_timeout=10
                )
            resp = await user.authenticator.fetch(req)
            self.set_status(200)
        except HTTPClientError as e:
            self.set_status(e.code)
    
    @web.authenticated
    async def post(self, service, handler=''):
        if service == "jhub":
            await super().post(handler)
            return
        
        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return

        url = self.get_url(service, handler)

        try:
            req = HTTPRequest(
                    url,
                    method="POST",
                    headers=self.get_header(),
                    body=self.request.body.decode("utf8"),
                    connect_timeout=10,
                    request_timeout=10
                )
            resp = await user.authenticator.fetch(req)
            self.set_status(200)
        except HTTPClientError as e:
            self.set_status(e.code)

    @web.authenticated
    async def delete(self, service, handler=''):
        if service == "jhub":
            await super().delete(handler)
            return

        user = self.current_user
        if not user.admin:
            self.set_status(403)
            return
        
        url = self.get_url(service, handler)

        try:
            req = HTTPRequest(
                    url,
                    method="DELETE",
                    headers=self.get_header(),
                    connect_timeout=10,
                    request_timeout=10
                )
            resp = await user.authenticator.fetch(req)
            self.set_status(200)
        except HTTPClientError as e:
            self.set_status(e.code)

