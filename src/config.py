import os
import json
import logging
import sys

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(), verbose=True)

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TIPOFF = os.getenv("EMAIL_TIPOFF")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_SERVER = os.getenv("SMTP_SERVER")
JMOD_TAG = os.getenv("JMOD_TAG")

SERVER_LOGIN = os.getenv("SERVER_LOGIN")
SERVER_PASSWORD = os.getenv("SERVER_PASSWORD")
SERVER_ADDRESS = os.getenv("SERVER_ADDRESS")
DATABASE = os.getenv("DATABASE")

GRAVEYARD_WEBHOOK = os.getenv("GRAVEYARD_WEBHOOK")
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")

# setup logging
file_handler = logging.FileHandler(filename="./error.log", mode="a")
stream_handler = logging.StreamHandler(sys.stdout)
# # log formatting
formatter = logging.Formatter(
    json.dumps(
        {
            "ts": "%(asctime)s",
            "name": "%(name)s",
            "function": "%(funcName)s",
            "level": "%(levelname)s",
            "msg": "%(message)s",
        }
    )
)


file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

handlers = [file_handler, stream_handler]

logging.basicConfig(level=logging.DEBUG, handlers=handlers)

logging.getLogger("mysql.connector.connection").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib").setLevel(logging.WARNING)
logging.getLogger("oauthlib").setLevel(logging.WARNING)