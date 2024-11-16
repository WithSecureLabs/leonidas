import logging.config

import click
from flask import Flask
from flask_restx import Api

from .utils import Config

# Configure logger for events, to go into stdout for accessing through primary container (easy on kubectl logs)
# separating them from Flask console output (root logger) which go to a file, to be picked up by the sidecar container
#   - This does not affect AWS Python code, Jinja template does not use Python logging but just print()
try:
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "eventFmt":{
                    "format":"%(message)s"
                }
            },
            "handlers": {
                "consoleHandler":{
                    "class": "logging.StreamHandler",
                    "formatter": "eventFmt",
                },
                "fileHandler":{
                    "class": "logging.FileHandler",
                    "filename": "/var/log/leonidas-flask.log",
                }
            },
            "root": {"level": "INFO", "handlers": ["fileHandler"]},

            "loggers": {
                "events": {
                    "level": "INFO",
                    "handlers": ["consoleHandler"],
                    "propagate": False,
                }
            },
        }
    )
except:
    pass

def secho(text, file=None, nl=None, err=None, color=None, **styles):
    pass

def echo(text, file=None, nl=None, err=None, color=None, **styles):
    pass

click.echo = echo
click.secho = secho
# This needed to hide Flask's startup message and keep stdout clean from messages 
# that aren't events, and therefore jq-friendly
# https://stackoverflow.com/questions/14888799/disable-console-messages-in-flask-server

app = Flask(__name__)
app.config.from_object(Config)
api = Api(
    app,
    version="2.0",
    title="Leonidas",
    description="An API for executing attacker actions within AWS and Kubernetes",
)
