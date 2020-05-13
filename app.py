'''
Created on Feb 12, 2020

@author: Tim Kreuzer
'''

import logging.config
import socket
import json
import os

from logging.handlers import SMTPHandler
from flask import Flask
from flask_restful import Api

from app.jlab import JupyterLabHandler
from app.health import HealthHandler

# Who should receive the emails if an error or an exception occures?
with open('/etc/j4j/j4j_mount/j4j_common/mail_receiver.json') as f:
    mail = json.load(f)

logger = logging.getLogger('J4J_DockerMaster')
# In trace will be sensitive information like tokens
logging.addLevelName(9, "TRACE")
def trace_func(self, message, *args, **kws):
    if self.isEnabledFor(9):
        # Yes, logger takes its '*args' as 'args'.
        self._log(9, message, args, **kws)
logging.Logger.trace = trace_func
mail_handler = SMTPHandler(
    mailhost='mail.fz-juelich.de',
    fromaddr='jupyter.jsc@fz-juelich.de',
    toaddrs=mail.get('receiver'),
    subject='J4J_DockerMaster Error'
)
mail_handler.setLevel(logging.ERROR)
mail_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))

# Override logging.config.file_config, so that the logfilename will be send to the parser, each time the logging.conf will be updated
def j4j_file_config(fname, defaults=None, disable_existing_loggers=True):
    if not defaults:
        defaults={'logfilename': '/etc/j4j/j4j_mount/j4j_docker/master/logs/{}_{}_o.log'.format(socket.gethostname(), os.getpid())}
    import configparser
    if isinstance(fname, configparser.RawConfigParser):
        cp = fname
    else:
        cp = configparser.ConfigParser(defaults)
        if hasattr(fname, 'readline'):
            cp.read_file(fname)
        else:
            cp.read(fname)
    formatters = logging.config._create_formatters(cp)
    # critical section
    logging._acquireLock()
    try:
        logging._handlers.clear()
        del logging._handlerList[:]
        # Handlers add themselves to logging._handlers
        handlers = logging.config._install_handlers(cp, formatters)
        logging.config._install_loggers(cp, handlers, disable_existing_loggers)
    finally:
        logging._releaseLock()

logging.config.fileConfig = j4j_file_config
logging.config.fileConfig('/etc/j4j/j4j_mount/j4j_docker/master/logging.conf')

# Add database and urls to the FlaskApp. If we change one of these, we have to restart the processes.
class FlaskApp(Flask):
    log = None
    with open('/etc/j4j/j4j_mount/j4j_common/urls.json') as f:
        urls = json.load(f)
    with open('/etc/j4j/j4j_mount/j4j_docker/master/database.json', 'r') as f:
        database = json.load(f)
    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger('J4J_DockerMaster')
        super(FlaskApp, self).__init__(*args, **kwargs)

# Start application, add mail_handler
application = FlaskApp(__name__)
if not application.debug:
    application.log.addHandler(mail_handler)
logger.info("Start FlaskApp")
api = Api(application)

# Add endpoints
api.add_resource(JupyterLabHandler, '/jlab')
api.add_resource(HealthHandler, '/health')

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=9007)
