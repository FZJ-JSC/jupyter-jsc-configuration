import logging
import os
import traceback

from jsonformatter import JsonFormatter
from logging.handlers import MemoryHandler, SMTPHandler, SysLogHandler


# Need to overwrite __deepcopy__  and manually copy all 
# # attributes that get installed on handler outside
# or JupyterHub to accept the handlers in the `extra_log_handlers` 
# parameter. See https://github.com/jupyterhub/jupyterhub/issues/2708.

class SafeToCopyFileHandler(logging.FileHandler):
    def __init__(self, filename):
        self.__filename = filename
        super().__init__(filename)

    def __deepcopy__(self, memodict={}):
        result = type(self)(filename=self.__filename)
        result.setLevel(self.level)
        result.setFormatter(self.formatter)
        return result


class SafeToCopySMTPHandler(SMTPHandler):
    def __init__(self, mailhost, fromaddr, toaddrs, subject):
        self.__mailhost = mailhost
        self.__fromaddr = fromaddr
        self.__toaddrs = toaddrs
        self.__subject = subject
        super().__init__(mailhost=mailhost, fromaddr=fromaddr,
                         toaddrs=toaddrs, subject=subject)

    def __deepcopy__(self, memodict={}):
        result = type(self)(mailhost=self.__mailhost, fromaddr=self.__fromaddr,
                            toaddrs=self.__toaddrs, subject=self.__subject)
        result.setLevel(self.level)
        result.setFormatter(self.formatter)
        return result


class SafeToCopySysLogHandler(SysLogHandler):
    def __init__(self, address, socktype):
        self.__address = address
        self.__socktype = socktype
        super().__init__(address=address, socktype=socktype)

    def __deepcopy__(self, memodict={}):
        result = type(self)(address=self.__address, socktype=self.__socktype)
        result.setLevel(self.level)
        result.setFormatter(self.formatter)
        return result


class SafeToCopyMemoryHandler(MemoryHandler):
    def __init__(self, capacity, target, flushLevel):
        self.__capacity = capacity
        self.__target = target
        self.__flushLevel = flushLevel
        super().__init__(capacity, target=target, flushLevel=flushLevel)

    def __deepcopy__(self, memodict={}):
        result = type(self)(capacity=self.__capacity, 
                            target=self.__target, flushLevel=self.__flushLevel)
        result.setLevel(self.level)
        result.setFormatter(self.formatter)
        return result


class ExtraFormatter(logging.Formatter):
    def format(self, record):
        dummy = logging.LogRecord(None, None, None, None, None, None, None)
        extra_txt = ""
        for k, v in record.__dict__.items():
            if k not in dummy.__dict__:
                extra_txt += " --- {}={}".format(k, v)
        message = super().format(record)
        return message + extra_txt
        

STRING_FORMAT = """{
        "asctime":         "asctime",
        "levelno":         "levelno",
        "levelname":       "levelname",
        "logger":          "name",
        "file":            "pathname",
        "line":            "lineno",
        "function":        "funcName",
        "Message":         "message"
    }"""

STRING_FORMAT_SIMPLE = "%(asctime)s levelno=%(levelno)s levelname=%(levelname)s logger=%(name)s file=%(pathname)s line=%(lineno)d function=%(funcName)s : %(message)s"
STRING_FORMAT_METRIC = "%(asctime)s;%(message)s"


def get_level(loglevel):
    if loglevel in ["NOTSET", "0"]:
        return 0
    elif loglevel in ["TRACE", "5"]:
        return 5
    elif loglevel in ["DEBUG", "10"]:
        return 10
    elif loglevel in ["INFO", "20"]:
        return 20
    elif loglevel in ["WARNING", "30"]:
        return 30
    elif loglevel in ["ERROR", "40"]:
        return 40
    elif loglevel in ["CRITICAL", "FATAL", "50"]:
        return 50
    else:
        return 20


def create_extra_handlers():
    handlers = []

    jsonFormatter = JsonFormatter(
        STRING_FORMAT, mix_extra=True, mix_extra_position="tail"
    )
    simpleFormatter = ExtraFormatter(STRING_FORMAT_SIMPLE)
    metricFormatter = ExtraFormatter(STRING_FORMAT_METRIC, "%Y_%m_%d-%H_%M_%S")

    if os.environ.get("LOGGING_METRICS_ENABLED", "false").lower() in ["true", "1"]:
        metric_logger = logging.getLogger('Metrics')
        metric_logger.setLevel(20)

        from datetime import datetime
        now = datetime.now()
        current_time = now.strftime("%Y_%m_%d-%H_%M_%S")
        metric_filename = "{}-{}".format(os.environ.get(
            "LOGGING_METRICS_LOGFILE", "/mnt/logs/metrics.log"
        ), current_time)

        metric_filehandler = SafeToCopyFileHandler(metric_filename)
        metric_filehandler.setFormatter(metricFormatter)
        metric_filehandler.setLevel(20)
        metric_logger.addHandler(metric_filehandler)

    if os.environ.get("LOGGING_STREAM_ENABLED", "false").lower() in ["true", "1"]:
        hub_logger = logging.getLogger('JupyterHub')
        consolehandler = hub_logger.handlers[0]

        formatter_value = os.environ.get(
            "LOGGING_STREAM_FORMATTER", "simple").lower()
        if formatter_value == "json":
            consolehandler.setFormatter(jsonFormatter)
        else:
            consolehandler.setFormatter(simpleFormatter)

        loglevel_value = os.environ.get("LOGGING_STREAM_LOGLEVEL", "INFO").upper()
        level = get_level(loglevel_value)
        consolehandler.setLevel(level)
    else:
        hub_logger = logging.getLogger('JupyterHub')
        consolehandler = hub_logger.handlers[0]

        hub_logger.removeHandler(consolehandler)

    if os.environ.get("LOGGING_FILE_ENABLED", "false").lower() in ["true", "1"]:
        filename = "{}-{}".format(os.environ.get(
            "LOGGING_FILE_LOGFILE", "/mnt/logs/jupyterhub.log"
        ), current_time)

        filehandler = SafeToCopyFileHandler(filename)
        formatter_value = os.environ.get(
            "LOGGING_FILE_FORMATTER", "simple").lower()

        if formatter_value == "json":
            filehandler.setFormatter(jsonFormatter)
        else:
            filehandler.setFormatter(simpleFormatter)

        loglevel_value = os.environ.get(
            "LOGGING_FILE_LOGLEVEL", "INFO").upper()
        level = get_level(loglevel_value)
        filehandler.setLevel(level)
        handlers.append(filehandler)

    if os.environ.get("LOGGING_MAIL_ENABLED", "false").lower() in ["true", "1"]:
        # Who should receive the emails if an error or an exception occures?
        mail_env = os.environ.get("LOGGING_MAIL_RECEIVER", "")
        if mail_env:
            mail = mail_env.split()
        else:
            mail = []

        mailhandler = SafeToCopySMTPHandler(
            mailhost=os.environ.get("LOGGING_MAIL_HOST"),
            fromaddr=os.environ.get("LOGGING_MAIL_FROM"),
            toaddrs=mail,
            subject=os.environ.get("LOGGING_MAIL_SUBJECT"),
        )

        formatter_value = os.environ.get(
            "LOGGING_MAIL_FORMATTER", "simple").lower()
        if formatter_value == "json":
            mailhandler.setFormatter(jsonFormatter)
        else:
            mailhandler.setFormatter(simpleFormatter)

        loglevel_value = os.environ.get(
            "LOGGING_MAIL_LOGLEVEL", "ERROR").upper()
        level = get_level(loglevel_value)
        mailhandler.setLevel(level)
        handlers.append(mailhandler)

    if os.environ.get("LOGGING_SYSLOG_ENABLED", "false").lower() in ["true", "1"]:
        import socket

        host = os.environ.get("LOGGING_SYSLOG_HOST", "localhost")
        try:
            port = int(os.environ.get("LOGGING_SYSLOG_PORT", "514"))
        except:
            print(
                "Use default syslog port: 514 - {}".format(
                    traceback.format_exc())
            )
            port = 514
        protocol_value = os.environ.get(
            "LOGGING_SYSLOG_PROTOCOL", "udp").lower()
        if protocol_value == "udp":
            protocol = socket.SOCK_DGRAM
        elif protocol_value == "tcp":
            protocol = socket.SOCK_STREAM
        else:
            print(
                "Unknown option for protocol: {}. Allowed arguments: [tcp, udp]. Use default: udp".format(
                    protocol_value
                )
            )
            protocol = socket.SOCK_DGRAM
        sysloghandler = SafeToCopySysLogHandler(
            address=(host, port), socktype=protocol)
        formatter_value = os.environ.get(
            "LOGGING_SYSLOG_FORMATTER", "json").lower()
        if formatter_value == "json":
            sysloghandler.setFormatter(jsonFormatter)
        else:
            sysloghandler.setFormatter(simpleFormatter)
        loglevel_value = os.environ.get(
            "LOGGING_SYSLOG_LOGLEVEL", "INFO").upper()
        level = get_level(loglevel_value)
        sysloghandler.setLevel(level)

        if os.environ.get("LOGGING_SYSLOG_MEMORY_ENABLED", "false").lower() in [
            "true",
            "1",
        ]:
            try:
                capacity = int(
                    os.environ.get("LOGGING_SYSLOG_MEMORY_CAPACITY", "100")
                )
            except:
                print(
                    "Use default syslog memory capacity: 100 - {}".format(
                        traceback.format_exc()
                    )
                )
                capacity = 100
            flushlevel_value = os.environ.get(
                "LOGGING_SYSLOG_MEMORY_FLUSHLEVEL", "ERROR"
            )
            flushlevel = get_level(flushlevel_value)
            memorysysloghandler = SafeToCopyMemoryHandler(
                capacity, target=sysloghandler, flushLevel=flushlevel
            )
            handlers.append(memorysysloghandler)
        else:
            handlers.append(sysloghandler)

    return handlers
