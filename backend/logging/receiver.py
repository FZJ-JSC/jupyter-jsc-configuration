#!venv/bin/python3
# https://gist.github.com/biggers/7da64042c86f7405f488bcc9efe040f8
# https://gist.github.com/pmav99/49c01313db33f3453b22
import json
import logging.handlers
import os
import pickle
import socket
import socketserver
import struct
import sys
from logging import config

_ = socket.SOCK_DGRAM  # use it once so that it's import for logging config
_ = sys.stdout  #  use it once so that it's import for logging config
log = logging.getLogger("Receiver")


class ExtraFormatter(logging.Formatter):
    dummy = logging.LogRecord(None, None, None, None, None, None, None)
    ignored_extras = ["message", "asctime"]

    def format(self, record):
        extra_txt = ""
        for k, v in record.__dict__.items():
            if k not in self.dummy.__dict__ and k not in self.ignored_extras:
                extra_txt += " --- {}={}".format(k, v)
        message = super().format(record)
        return message + extra_txt


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        if log.handlers:
            log.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    allow_reuse_address = False

    def __init__(
        self,
        host="localhost",
        port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
        handler=LogRecordStreamHandler,
    ):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select

        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()], [], [], self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort


def setup(config_filename):
    with open(config_filename, "r") as f:
        logging_config = json.load(f)

    config.dictConfig(logging_config)
    logging.addLevelName(5, "TRACE")

    def trace_func(self, message, *args, **kws):
        if self.isEnabledFor(5):
            # Yes, logger takes its '*args' as 'args'.
            self._log(5, message, args, **kws)

    logging.Logger.trace = trace_func


def main(config_filename):
    tcpserver = LogRecordSocketReceiver(handler=LogRecordStreamHandler)
    print("About to start TCP server...")
    setup(config_filename)
    t = logging.config.listen(56712)
    t.start()
    tcpserver.serve_until_stopped()
    t.join()
    logging.config.stopListening()


if __name__ == "__main__":
    config_filename = os.environ.get("LOGGING_CONFIG_FILE", None)
    if config_filename:
        main(config_filename)
    else:
        print("LOGGING_CONFIG_FILE not set")
        print("Cancel")
