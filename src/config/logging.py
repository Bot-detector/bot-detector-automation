import logging
import sys
import json

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

handlers = [
    # file_handler, 
    stream_handler
]

logging.basicConfig(level=logging.DEBUG, handlers=handlers)

logging.getLogger("mysql.connector.connection").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
logging.getLogger("requests_oauthlib").setLevel(logging.WARNING)
logging.getLogger("oauthlib").setLevel(logging.WARNING)
logging.getLogger("discord.webhook.sync").setLevel(logging.WARNING)
logging.getLogger("aiokafka").setLevel(logging.WARNING)
