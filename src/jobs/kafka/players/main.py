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

    async def get_data(self, url: str, params: dict) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=self.headers) as resp:
                if not resp.ok:
                    error_message = (
                        f"response status {resp.status} "
                        f"response body: {await resp.text()}"
                    )
                    logger.error(error_message)
                    raise ValueError(error_message)
                data = await resp.json()
                return data

    async def main(self):
        logger.info(f"starting: {self.__class__.__name__}")

        unique_ids = deque(maxlen=1_000_000)
        last_day = datetime.now().date()
        max_id = 0

        params = {
            "limit": APPCONFIG.BATCH_SIZE,
            "player_id": max_id,
            "greater_than": 1,
        }
        url = f"{APPCONFIG.ENDPOINT}/v2/player/"
        while True:
            if self.message_queue.qsize() > int(self.message_queue.maxsize / 2):
                await asyncio.sleep(1)
                continue

            today = datetime.now().date()

            if today != last_day:
                logger.info("new day, resetting")
                last_day = datetime.now().date()
                unique_ids.clear()
                params["player_id"] = 0

            logger.info(f"fetching players to scrape {max_id=}")

            try:
                players = await self.get_data(url=url, params=params)
            except Exception as error:
                logger.error(f"An error occurred: {type(error)} - {str(error)}")
                await asyncio.sleep(5)
                continue

            logger.info(f"fetched {len(players)} players")

            if len(players) < APPCONFIG.BATCH_SIZE:
                logger.info(f"Received {len(players)}")
                continue

            asyncio.ensure_future(self.add_data_to_queue(players, unique_ids))

            players_max = max([p.get("id") for p in players])
            max_id = players_max if players_max > max_id else max_id
            params["player_id"] = max_id


async def retry(f) -> None:
    class_name = f.__self__.__class__.__name__
    method_name = f.__name__
    while True:
        try:
            logger.info(f"starting: {class_name}.{method_name}")
            await f()
        except Exception as e:
            logger.error(f"{class_name}.{method_name} - {e}")
            await asyncio.sleep(15)


async def async_main():
    message_queue = Queue(maxsize=10_000)
    data_fetcher = DataFetcher(message_queue)
    kafka_producer = KafkaProducer("player", message_queue)

    asyncio.ensure_future(data_fetcher.main())
    asyncio.ensure_future(kafka_producer.start())


def get_players_to_scrape():
    asyncio.ensure_future(async_main())
