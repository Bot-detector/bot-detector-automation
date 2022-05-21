from fastapi import FastAPI

app = FastAPI()


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


@app.get("/status", tags=["Health"])
async def status(token: str):
    """
    Outputs a general access and usage status for the API.
    This can be useful to determine if a route has been delayed by a period of time, or if the routes are alive and healthy.
    """
    return {"message": "#TBD"}


@app.post("/tipoff/tipoff-bots", tags=["Tipoff"])
async def tipoff_bots(token: str):
    """
    Sends a tipoff email to JaGex, requires higher-level access to send data over.
    """
    return {"message": "#TBD"}


@app.post("/broadcast/tweet_bans", tags=["Broadcast", "Twitter"])
async def tweet_bans(token: str):
    """
    Tweets out bans to the official twitter: @Osrsbotdetector.
    """
    return {"message": "#TBD"}


@app.post("/broadcast/discord_bans", tags=["Broadcast", "Discord"])
async def discord_bans(token: str):
    """
    Sends a discord ban update into the relevant channel.
    """
    return {"message": "#TBD"}
