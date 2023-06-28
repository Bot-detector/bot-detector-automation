import asyncio
import json
import logging
from datetime import datetime, timedelta

import aiohttp
import aiokafka

from .models import Player
import config
from config import config

logger = logging.getLogger(__name__)
APPCONFIG = config.AppConfig()


async def send_rows_to_kafka(rows: list[Player], kafka_topic: str):
    # Create Kafka producer
    producer = aiokafka.AIOKafkaProducer(
        bootstrap_servers=[APPCONFIG.KAFKA_HOST],
        value_serializer=lambda x: json.dumps(x).encode(),
    )
    await producer.start()

    try:
        # Send rows to Kafka
        for row in rows:
            await producer.send(kafka_topic, key=row.name.encode(), value=row.dict())

    finally:
        # Wait for all messages to be sent
        await producer.flush()
        # Stop the Kafka producer
        await producer.stop()


async def get_data() -> list[Player]:
    """
    This method is used to get the players to scrape from the api.
    """
    url = (
        f"{APPCONFIG.ENDPOINT}/v1/scraper/players/0/{APPCONFIG.BATCH_SIZE}/{APPCONFIG.API_TOKEN}"
    )
    logger.info("fetching players to scrape")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                logger.error(
                    f"response status {response.status}"
                    f"response body: {await response.text()}"
                )
                raise Exception("error fetching players")
            players = await response.json()
    logger.info(f"fetched {len(players)} players")
    players = [Player(**player) for player in players]
    return players


def process_rows(result: list[Player], unique_ids: list):
    today = datetime.now().strftime("%Y-%m-%d")

    rows = []
    for row in result:
        if row.created_at:
            row.created_at
        if row["created_at"]:
            row["created_at"] = row["created_at"].strftime("%Y-%m-%d %H:%M:%S")

        if row["updated_at"]:
            if row["updated_at"].strftime("%Y-%m-%d") == today:
                continue
            row["updated_at"] = row["updated_at"].strftime("%Y-%m-%d %H:%M:%S")

        row = Player(**row)

        if row.id not in unique_ids:
            rows.append(row)
            # Add unique IDs to the list
            unique_ids.append(row.id)
    return rows, unique_ids


async def async_main():
    unique_ids: dict = {}

    logger.info("start getting data")
    _last_day = datetime.now().strftime("%Y-%m-%d")

    while True:
        # reset on new day
        today = datetime.now().strftime("%Y-%m-%d")
        if _last_day != today:
            logger.info("new day!")
            _last_day = today
            unique_ids:dict = {}

        result = await get_data()

        if not result:
            logger.info("no rows found")
            await asyncio.sleep(60)
            continue

        rows = []

        for row in result:
            # for some reason we are getting alot of duplicate id's
            _time = unique_ids.get(row.id, None)

            # if _time is none: we can scrape
            if not _time is None:
                # 
                if _time > datetime.now():
                    continue

            if not row.updated_at is None:
                _updated_at = datetime.fromisoformat(row.updated_at)
                _updated_at = _updated_at.strftime("%Y-%m-%d")
                if _updated_at == today:
                    logger.debug(f"already scraped today {row}")
                    continue

            # expirery date
            unique_ids[row.id] = datetime.now() + timedelta(minutes=5)
            rows.append(row)


        if not rows:
            logger.error(f"no unique rows")
            await asyncio.sleep(5)
            continue

        # Send rows to Kafka
        await send_rows_to_kafka(rows, kafka_topic="player")


def get_players_to_scrape():
    asyncio.ensure_future(async_main())
