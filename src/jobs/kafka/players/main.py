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
from asyncio import Queue
from aiohttp import ClientResponse

logger = logging.getLogger(__name__)
APPCONFIG = config.AppConfig()


async def send_rows_to_kafka(kafka_topic: str, message_queue: Queue):
    producer = aiokafka.AIOKafkaProducer(
        bootstrap_servers=[APPCONFIG.KAFKA_HOST],
        value_serializer=lambda x: json.dumps(x).encode(),
    )

    await producer.start()

    try:
        while True:
            message: Player = await message_queue.get()
            await producer.send(
                kafka_topic, key=message.name.encode(), value=message.dict()
            )
            message_queue.task_done()
            
            qsize = message_queue.qsize()
            if qsize % 1000 == 0:
                logger.info(f"{qsize=}")
    except Exception as e:
        logger.error(e)
    finally:
        await producer.flush()
        await producer.stop()


async def handle_aiohttp_error(response: ClientResponse):
    if response.status != 200:
        logger.error(
            f"response status {response.status}"
            f"response body: {await response.text()}"
        )
        raise Exception("error fetching players")


async def add_data_to_queue(players:list[dict], message_queue: Queue, unique_ids:list[int]):
    today = datetime.now().date()
    for player in players:
        player = Player(**player)
        date = datetime.strptime(player.updated_at, "%Y-%m-%dT%H:%M:%S").date()

        if date == today:
            continue

        if player.id in unique_ids:
            continue

        await message_queue.put(player)
        unique_ids.append(player.id)

        qsize = message_queue.qsize()
        if qsize % 1000 == 0:
            logger.info(f"{qsize=} {len(unique_ids)=}")
    return 

async def get_data(message_queue: Queue):
    page = 1
    unique_ids = deque(maxlen=100_000)
    headers = {"token": APPCONFIG.API_TOKEN}
    last_day = datetime.now().date()

    while True:
        if message_queue.qsize() > int(message_queue.maxsize / 2):
            await asyncio.sleep(1)
            continue

        url = f"{APPCONFIG.ENDPOINT}/v2/players?page={page}&page_size={APPCONFIG.BATCH_SIZE}"
        # url = f"{APPCONFIG.ENDPOINT}/v1/scraper/players/0/{APPCONFIG.BATCH_SIZE}/{APPCONFIG.API_TOKEN}"
        logger.info(f"fetching players to scrape {page=}")

        today = datetime.now().date()

        if today != last_day:
            last_day = datetime.now().date()
            unique_ids.clear()
            page = 1

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                await handle_aiohttp_error(response)
                players = await response.json()

        logger.info(f"fetched {len(players)} players")

        if len(players) < APPCONFIG.BATCH_SIZE:
            logger.info(f"Received {len(players)} at {page} resetting page")
            page = 1
            continue

        
        asyncio.ensure_future(add_data_to_queue(players, message_queue, unique_ids))

        page += 1


async def async_main():
    message_queue = Queue(maxsize=10_000)
    asyncio.ensure_future(get_data(message_queue))
    asyncio.ensure_future(send_rows_to_kafka("player", message_queue))


def get_players_to_scrape():
    asyncio.ensure_future(async_main())
