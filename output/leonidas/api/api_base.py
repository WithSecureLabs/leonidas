from flask import Flask
from flask_restx import Api
from .utils import Config

app = Flask(__name__)
app.config.from_object(Config)
api = Api(
    app,
    version="1.0",
    title="Leonidas",
    description="An API for executing attacker actions within AWS",
)
