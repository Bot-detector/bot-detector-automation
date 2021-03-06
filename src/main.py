import logging

from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone

import banbroadcaster.main_broadcaster
import tipoff.main_tipoff

logger = logging.getLogger(__name__)

executors = {"default": ProcessPoolExecutor()}

scheduler = BackgroundScheduler(daemon=False, executors=executors)

if __name__ == "__main__":
    logger.info("Starting Main")
    scheduler.start()

    # Broadcast bans to #bot-graveyard on Discord, send total bans tweet, and send bans breakdowns tweets
    scheduler.add_job(
        banbroadcaster.main_broadcaster.broadcast_bans,
        "cron",
        hour=20,
        minute=5,
        misfire_grace_time=60,
    )

    # Send next tipoff batch to Jagex
    scheduler.add_job(
        tipoff.main_tipoff.tipoff_bots,
        "cron",
        hour=20,
        minute=45,
        misfire_grace_time=60,
    )

    while True:
        pass
