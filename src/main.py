import logging

from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from jobs.banbroadcaster.main import broadcast_bans
from jobs.kafka.players.main import get_players_to_scrape
from jobs.tipoff.main import tipoff_bots
import asyncio

logger = logging.getLogger(__name__)

executors = {"default": ProcessPoolExecutor()}

scheduler = BackgroundScheduler(daemon=False, executors=executors)


async def main():
    logger.debug("Starting Main")
    scheduler.start()

    # Broadcast bans to #bot-graveyard on Discord, send total bans tweet, and send bans breakdowns tweets
    scheduler.add_job(
        broadcast_bans,
        "cron",
        hour=20,
        minute=5,
        misfire_grace_time=60,
    )

    # Send next tipoff batch to Jagex
    scheduler.add_job(
        tipoff_bots,
        "cron",
        hour=9,
        minute=45,
        misfire_grace_time=60,
    )

    get_players_to_scrape()
    # broadcaster.broadcast_bans()
    # tip_off.tipoff_bots()
    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
