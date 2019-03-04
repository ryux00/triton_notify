import pdb
import os
import datetime
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, request, make_response
from flask_restful import Resource, Api, abort
from flask_sqlalchemy import SQLAlchemy

from models.models import db
from resources.telegram import Telegram
from resources.twitter import Twitter


app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
# TODO switch out to rds/sql after testing
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
app.app_context().push()
db.init_app(app)


# Adds RotatingFileHandler if app is not running on aws lambda
# Since labda instances are read only RotatingFileHandler won't work
# In lambda logs and print statements are added to aws cloudwatch logs
if os.environ.get("AWS_EXECUTION_ENV") == None:
    handler = RotatingFileHandler("app.log", maxBytes=10000, backupCount=3)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

api = Api(app)

MESSAGE_TYPES = ["telegram", "email", "sms", "log", "twitter"]
MESSAGE_PROVIDERS = {"telegram": Telegram, "twitter": Twitter}


class Index(Resource):
    def get(self):
        return "ok", 200


class HealthCheck(Resource):
    def get(self):
        app.logger.info(
            f"{datetime.datetime.utcnow().isoformat()} | HealthCheck done | {request.remote_addr}"
        )
        return {"status": "ok"}, 200


def check_message_type(func):
    def inner(*args, **kwargs):
        message_type = kwargs.get("message_type", "NA")
        if kwargs.get("message_type", False) and kwargs.get("message_type") in MESSAGE_TYPES:
            print(*args)
            print("deco running")
            return func(*args, **kwargs)
        else:
            abort(404, message=f"Invalid message type {message_type}")

    return inner


class Message(Resource):
    @check_message_type
    def post(self, message_type):
        if message_type not in MESSAGE_TYPES:
            app.logger.error(
                f"{datetime.datetime.utcnow().isoformat()} | Invalid message type:{message_type} | {request.remote_addr}"
            )
            abort(404, message=f"Invalid message type {message_type}")
        message_provider = MESSAGE_PROVIDERS.get(message_type)(request.json, request)
        message_status = message_provider.send_message()
        return message_status, message_status["status_code"]


api.add_resource(Index, "/")
api.add_resource(Message, "/message/<string:message_type>")
api.add_resource(HealthCheck, "/healthcheck")

if __name__ == "__main__":
    app.run()


# TODO
# Check if decorators can be used to validate token
# Create users and  tokens manually
# Function to validate tokens
# Functions to create tokens
# Functions to create/delete users
# Functions to log request numbers
# Functions to implement ratelimiting
# Queues to implement writes to db
# Email sender
# Log writer
