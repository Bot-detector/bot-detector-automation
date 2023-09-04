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

    async def start(self):
        producer = AIOKafkaProducer(
            bootstrap_servers=[APPCONFIG.KAFKA_HOST],
            value_serializer=lambda x: json.dumps(x).encode(),
        )
        await producer.start()

        try:
            while True:
                message: Player = await self.message_queue.get()
                await producer.send(
                    self.kafka_topic, key=message.name.encode(), value=message.dict()
                )
                self.message_queue.task_done()

                qsize = self.message_queue.qsize()
                if qsize % 1000 == 0:
                    logger.info(f"{qsize=}")
        except Exception as e:
            logger.error(e)
        finally:
            await producer.flush()
            await producer.stop()


class DataFetcher:
    def __init__(self, message_queue: Queue):
        self.message_queue = message_queue
        self.headers = {"token": APPCONFIG.API_TOKEN}
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def handle_aiohttp_error(self, response: ClientResponse):
        if response.status != 200:
            logger.error(
                f"response status {response.status}"
                f"response body: {await response.text()}"
            )
            raise Exception("error fetching players")

    async def add_data_to_queue(self, players: List[dict], unique_ids: List[int]):
        today = datetime.now().date()
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

            qsize = self.message_queue.qsize()
            if qsize % 1000 == 0:
                logger.info(f"{qsize=} {len(unique_ids)=}")

    async def get_data(self):
        page = 1
        unique_ids = deque(maxlen=10_000_000)
        last_day = datetime.now().date()

        while True:
            if self.message_queue.qsize() > int(self.message_queue.maxsize / 2):
                await asyncio.sleep(1)
                continue

            url = f"{APPCONFIG.ENDPOINT}/v1/scraper/players/{page}/{APPCONFIG.BATCH_SIZE}/{APPCONFIG.API_TOKEN}"
            # url = f"{APPCONFIG.ENDPOINT}/v2/players/"
            params = {"page": page, "page_size": APPCONFIG.BATCH_SIZE}
            headers = {"token": APPCONFIG.API_TOKEN}
            
            logger.info(f"fetching players to scrape {page=}")

            today = datetime.now().date()

            if today != last_day:
                last_day = datetime.now().date()
                unique_ids.clear()
                page = 1

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

            page += 1


async def async_main():
    message_queue = Queue(maxsize=10_000)
    data_fetcher = DataFetcher(message_queue)
    kafka_producer = KafkaProducer("player", message_queue)

    asyncio.ensure_future(data_fetcher.get_data())
    asyncio.ensure_future(kafka_producer.start())


def get_players_to_scrape():
    asyncio.ensure_future(async_main())
