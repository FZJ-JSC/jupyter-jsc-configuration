import logging
import os
import traceback


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

class ExtraFormatter(logging.Formatter):
    def format(self, record):
        dummy = logging.LogRecord(None, None, None, None, None, None, None)
        extra_txt = ""
        for k, v in record.__dict__.items():
            if k not in dummy.__dict__:
                extra_txt += " --- {}={}".format(k, v)
        message = super().format(record)
        return message + extra_txt

STRING_FORMAT_METRIC = "%(asctime)s;%(message)s"


def waitForLoggingReceiver():
    # Wait for Logging Receiver to run
    import logging
    import socket
    import time

    for i in range(1, 10):
        a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        b_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        location = ("127.0.0.1", logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        location_b = ("127.0.0.1", 56712)
        result_of_check = a_socket.connect_ex(location)
        result_of_check_b = b_socket.connect_ex(location_b)
        if result_of_check == 0:
            if result_of_check_b == 0:
                break
        if i == 9:
            raise Exception("LoggingReceiver not coming up")
        time.sleep(0.5)

def create_extra_handlers():
    handlers = []

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


    # Remove default StreamHandler
    hub_logger = logging.getLogger('JupyterHub')
    consolehandler = hub_logger.handlers[0]
    hub_logger.removeHandler(consolehandler)

    # In trace will be sensitive information like tokens
    logging.addLevelName(5, "TRACE")

    def trace_func(self, message, *args, **kws):
        if self.isEnabledFor(5):
            # Yes, logger takes its '*args' as 'args'.
            self._log(5, message, args, **kws)

    logging.Logger.trace = trace_func
    hub_logger.setLevel(5)
    sockethandler = logging.handlers.SocketHandler(
        "127.0.0.1", logging.handlers.DEFAULT_TCP_LOGGING_PORT
    )
    sockethandler.setLevel(5)
    hub_logger.addHandler(sockethandler)

    waitForLoggingReceiver()

    return []
