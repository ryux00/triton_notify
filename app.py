import pdb
import datetime
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, request, make_response
from flask_restful import Resource, Api, abort
from flask_sqlalchemy import SQLAlchemy

from resources.telegram import Telegram

handler = RotatingFileHandler("app.log", maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
app = Flask(__name__)

app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
# db = SQLAlchemy(app)
api = Api(app)

MESSAGE_TYPES = ["telegram", "email", "sms", "log", "twitter"]
MESSAGE_PROVIDERS = {"telegram": Telegram}


class HealthCheck(Resource):
    def get(self):
        app.logger.info(
            f"HealthCheck done by {request.remote_addr} time:{datetime.datetime.utcnow().isoformat()}"
        )
        return {"status": "ok"}, 200


class Message(Resource):
    def post(self, message_type):
        if message_type not in MESSAGE_TYPES:
            app.logger.error(
                f"Invalid message type:{message_type} by {request.remote_addr} time:{datetime.datetime.utcnow().isoformat()}"
            )
            abort(404, message=f"Invalid message type {message_type}")
        message_provider = MESSAGE_PROVIDERS.get(message_type)(request.json)
        message_status = message_provider.send_message()
        return message_status, message_status["status_code"]


api.add_resource(Message, "/message/<string:message_type>")
api.add_resource(HealthCheck, "/healthcheck")

if __name__ == "__main__":
    app.run()
