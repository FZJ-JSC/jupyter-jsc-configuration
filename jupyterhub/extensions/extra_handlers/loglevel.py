import logging
import os

from tornado import web

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
        return
