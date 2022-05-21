from unittest import FunctionTestCase
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import src.banbroadcaster.main_broadcaster as banbroadcaster
import src.tipoff.main_tipoff as tipoff

app = FastAPI()
origins = [
    "http://osrsbotdetector.com/",
    "https://osrsbotdetector.com/",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def output_handler(function=None):
    """Handles errors for POST routes

    Args:
        function (python functoin): python function object. Defaults to None.

    Returns:
        dictionary: {'message'}:{'error'|'ok'}
    """
    try:
        function()
    except:
        return {"message": "error"}
    return {"message": "ok"}


@app.get("/", tags=["Home"])
async def root():
    """
    Shows information regarding the relevant links to the repository API.
    Additionally shows the user how to access the route documentation.
    """
    welcome_message = {
        "message": "Welcome to the Bot Detector Plugin Automation API. Repository Link: https://github.com/Bot-detector/bot-detector-automation",
        "route documentation": "/docs",
    }
    return welcome_message


@app.post("/tipoff/tipoff-bots", tags=["Tipoff"])
async def tipoff_bots(token: str):
    """Sends a tipoff email to JaGex, requires higher-level access to send data over."""
    return output_handler(function=tipoff.tipoff_bots)


@app.post("/broadcast/broadcast-bans", tags=["Broadcast"])
async def discord_bans(
    token: str,
    Twitter: bool = True,
    Discord: bool = True,
):
    """Sends a discord and/or twitter ban output to the relevant channels."""

    if (Twitter and Discord) == False:
        return {"message": "You must select one ban output path."}

    return output_handler(
        function=banbroadcaster.broadcast_bans(Twitter=Twitter, Discord=Discord)
    )
