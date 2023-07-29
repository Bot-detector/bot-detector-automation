import asyncio
import json
import logging
from datetime import datetime, timedelta

import aiohttp
import aiokafka
from aiokafka import AIOKafkaProducer
from .models import Player
import config
from config import config
from collections import deque

logger = logging.getLogger(__name__)
APPCONFIG = config.AppConfig()


async def send_rows_to_kafka(producer:AIOKafkaProducer, rows: list[Player], kafka_topic: str):
    try:
        # Send rows to Kafka
        for row in rows:
            await producer.send(kafka_topic, key=row.name.encode(), value=row.dict())
        logger.info(f"send {len(rows)} players to kafka")
    except Exception as e:
        logger.error(e)
        # Stop the Kafka producer
        await producer.stop()
    finally:
        # Wait for all messages to be sent
        await producer.flush()


async def get_data(page: int) -> list[Player]:
    """
    This method is used to get the players to scrape from the api.
    """
    url = (
        f"{APPCONFIG.ENDPOINT}/v2/players?page={page}&page_size={APPCONFIG.BATCH_SIZE}"
        # f"{APPCONFIG.ENDPOINT}/v1/scraper/players/0/{APPCONFIG.BATCH_SIZE}/{APPCONFIG.API_TOKEN}"
    )
    headers = {"token": APPCONFIG.API_TOKEN}
    logger.info("fetching players to scrape")
    async with aiohttp.ClientSession(headers=headers) as session:
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
            row["created_at"] = row["created_at"].strftime("%Y-%m-%dT%H:%M:%S")

        if row["updated_at"]:
            if row["updated_at"].strftime("%Y-%m-%d") == today:
                continue
            row["updated_at"] = row["updated_at"].strftime("%Y-%m-%dT%H:%M:%S")

        row = Player(**row)

        if row.id not in unique_ids:
            rows.append(row)
            # Add unique IDs to the list
            unique_ids.append(row.id)
    return rows, unique_ids

def batch_list(input_list, batch_size):
    for i in range(0, len(input_list), batch_size):
        yield input_list[i:i + batch_size]

async def async_main():
    unique_ids = deque(maxlen=100_000)

    logger.info("start getting data")
    last_day = datetime.now().date()
    page = 1
    # Create Kafka producer
    producer = aiokafka.AIOKafkaProducer(
        bootstrap_servers=[APPCONFIG.KAFKA_HOST],
        value_serializer=lambda x: json.dumps(x).encode(),
    )
    await producer.start()
    while True:
        # reset on new day
        today = datetime.now().date()
        if today != last_day:
            last_day = datetime.now().date()
            unique_ids = []
            page = 1

        # get data
        result = await get_data(page=page)

        if not result:
            logger.info("result is empty")
            await asyncio.sleep(60)
            continue

        rows = []

        for row in result:
            # check for duplicate id's
            if row.id in unique_ids:
                continue

            # check if already scraped for some reason
            if row.updated_at is not None:
                _updated_at = datetime.strptime(
                    row.updated_at, "%Y-%m-%dT%H:%M:%S"
                ).date()
                if _updated_at == today:
                    continue

            unique_ids.append(row.id)
            rows.append(row)

        # check if there are any rows
        if not rows:
            logger.error(f"no unique rows\nexample={row.dict()}")
            await asyncio.sleep(5)
            page += 1
            continue

        # Send rows to Kafka
        for batch in batch_list(rows.copy(), batch_size=1000):
            asyncio.ensure_future(send_rows_to_kafka(producer, batch, kafka_topic="player"))
        page += 1


def get_players_to_scrape():
    asyncio.ensure_future(async_main())
