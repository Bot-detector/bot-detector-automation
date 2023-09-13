import asyncio
import json
import logging
from datetime import datetime, timedelta

import aiohttp
import aiokafka
from aiokafka import AIOKafkaProducer
from aiohttp import ClientResponse, ClientConnectorError
from asyncio import Queue
from collections import deque
from typing import List

from .models import Player
from config import config

logger = logging.getLogger(__name__)
APPCONFIG = config.AppConfig()


class KafkaProducer:
    def __init__(self, kafka_topic: str, message_queue: Queue):
        self.kafka_topic = kafka_topic
        self.message_queue = message_queue

    async def send_messages(self, producer):
        while True:
            message: Player = await self.message_queue.get()
            await producer.send(
                self.kafka_topic, key=message.name.encode(), value=message.dict()
            )
            self.message_queue.task_done()

            qsize = self.message_queue.qsize()
            if qsize % 1000 == 0:
                logger.info(f"{qsize=}")

    async def start(self):
        logger.info(f"starting: {self.__class__.__name__}")
        producer = AIOKafkaProducer(
            bootstrap_servers=[APPCONFIG.KAFKA_HOST],
            value_serializer=lambda x: json.dumps(x).encode(),
        )
        await producer.start()

        try:
            await self.send_messages(producer=producer)
        except Exception as e:
            logger.error(e)
        finally:
            await producer.flush()
            await producer.stop()

        logger.info("restarting")
        # if for some reason we break the loop, just restart
        await asyncio.sleep(60)
        await self.start()


class DataFetcher:
    def __init__(self, message_queue: Queue):
        self.message_queue = message_queue
        self.headers = {"token": APPCONFIG.API_TOKEN}
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def handle_aiohttp_error(self, response: ClientResponse):
        if response.status != 200:
            logger.error(
                f"response status {response.status} "
                f"response body: {await response.text()}"
            )
            raise Exception("error fetching players")

    async def add_data_to_queue(self, players: List[dict], unique_ids: List[int]):
        today = datetime.now().date()
        added = 0
        for player in players:
            player = Player(**player)

            if len(player.name) > 13:
                continue

            if player.updated_at is not None:
                date = datetime.strptime(player.updated_at, "%Y-%m-%dT%H:%M:%S").date()
                if date == today:
                    continue

            if player.id in unique_ids:
                continue

            await self.message_queue.put(player)
            unique_ids.append(player.id)
            added += 1

            qsize = self.message_queue.qsize()
            if qsize % 1000 == 0:
                logger.info(f"{qsize=}, {len(unique_ids)=}")
        logger.info(f"{added=}")

    async def get_data(self):
        logger.info(f"starting: {self.__class__.__name__}")
        page = 1
        unique_ids = deque(maxlen=1_000_000)
        last_day = datetime.now().date()
        max_id = 1

        while True:
            if self.message_queue.qsize() > int(self.message_queue.maxsize / 2):
                await asyncio.sleep(1)
                continue

            # page = page if page <= 10 else 0  # only for scraper endpoint
            # url = f"{APPCONFIG.ENDPOINT}/v1/scraper/players/{page}/{APPCONFIG.BATCH_SIZE}/{APPCONFIG.API_TOKEN}"

            url = f"{APPCONFIG.ENDPOINT}/v2/players/"

            params = {
                "page_size": APPCONFIG.BATCH_SIZE, 
                "greater_than": max_id
            }

            headers = {"token": APPCONFIG.API_TOKEN}

            logger.info(f"fetching players to scrape {page=}, {max_id=}")

            today = datetime.now().date()

            if today != last_day:
                last_day = datetime.now().date()
                unique_ids.clear()
                page = 1
                max_id = 0

            try:
                async with self.session.get(
                    url, params=params, headers=headers
                ) as response:
                    await self.handle_aiohttp_error(response)
                    players = await response.json()
            except Exception as error:
                logger.error(f"An error occurred: {type(error)} - {str(error)}")
                await asyncio.sleep(5)  # Adjust the delay as needed
                continue

            logger.info(f"fetched {len(players)} players")

            if len(players) < APPCONFIG.BATCH_SIZE:
                logger.info(f"Received {len(players)} at {page} resetting page")
                page = 1
                continue

            asyncio.ensure_future(self.add_data_to_queue(players, unique_ids))
            
            players_max = max([p.get('id') for p in players]) 
            max_id = players_max if players_max > max_id else max_id

            page += 1


async def retry(f) -> None:
    while True:
        try:
            class_name = f.__self__.__class__.__name__
            method_name = f.__name__
            logger.info(f"starting: {class_name}.{method_name}")
            await f()
        except Exception as e:
            logger.error(f"{class_name}.{method_name} - {e}")
            pass


async def async_main():
    message_queue = Queue(maxsize=10_000)
    data_fetcher = DataFetcher(message_queue)
    kafka_producer = KafkaProducer("player", message_queue)

    asyncio.ensure_future(retry(data_fetcher.get_data))
    asyncio.ensure_future(retry(kafka_producer.start))


def get_players_to_scrape():
    asyncio.ensure_future(async_main())
