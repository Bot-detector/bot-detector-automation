import asyncio
import json
import logging
from asyncio import Queue
from datetime import datetime
from time import time
from typing import Any

import aiohttp
from aiokafka import AIOKafkaProducer

from config import config

from .models import Player

logger = logging.getLogger(__name__)
APPCONFIG = config.AppConfig()


async def kafka_producer():
    producer = AIOKafkaProducer(
        bootstrap_servers=[APPCONFIG.KAFKA_HOST],
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    await producer.start()
    return producer


async def send_messages(topic: str, producer: AIOKafkaProducer, send_queue: Queue):
    last_interval = time()
    messages_sent = 0

    while True:
        if send_queue.empty():
            await asyncio.sleep(1)
        message: Player = await send_queue.get()
        await producer.send(topic, value=message.dict())
        send_queue.task_done()

        messages_sent += 1

        if messages_sent >= 1000:
            current_time = time()
            elapsed_time = current_time - last_interval
            speed = messages_sent / elapsed_time
            logger.info(
                f"processed {messages_sent} in {elapsed_time:.2f} seconds, {speed:.2f} msg/sec"
            )

            last_interval = time()
            messages_sent = 0


def is_today(updated_at: str):
    if updated_at is None:
        return False
    today = datetime.now().date()
    date = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%S").date()
    return date == today


async def parse_data(players: list[dict]):
    players: list[Player] = [Player(**player) for player in players]
    players = [
        player
        for player in players
        if len(player.name) < 13 and is_today(player.updated_at)
    ]
    return players


async def get_request(
    url: str, params: dict, headers: dict = {}
) -> tuple[list[dict], Any]:
    data = None
    error = None
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.ok:
                data = await resp.json()
            else:
                error = {
                    "status": resp.status,
                    "body": await resp.text(),
                    "url": url,
                    "params": params,
                }
                logger.error(error)
    return data, error


async def get_data(receive_queue: Queue):
    last_day = datetime.now().date()
    max_id = 0
    params = {
        "limit": APPCONFIG.BATCH_SIZE,
        "player_id": max_id,
        "greater_than": 1,
    }
    headers = {"token": APPCONFIG.API_TOKEN}
    url = f"{APPCONFIG.ENDPOINT}/v2/player/"

    while True:
        today = datetime.now().date()
        players, error = await get_request(url=url, params=params, headers=headers)

        if error is not None:
            sleep_time = 30
            logger.info(f"sleeping {sleep_time}")
            await asyncio.sleep(sleep_time)
            continue

        players = await parse_data(players=players)
        logger.info({"reeived": len(players), "max_id": {params.get("player_id")}})

        await asyncio.gather(*[receive_queue.put(item=p) for p in players])

        if len(players) < APPCONFIG.BATCH_SIZE:
            logger.info(f"Received {len(players)}, sleeping.")
            await asyncio.sleep(300)

        max_id = max([p.id for p in players])

        if max_id > params["player_id"]:
            params["player_id"] = max_id

        if today == last_day:
            params["player_id"] = 0


async def main():
    send_queue = Queue()
    receive_queue = Queue()
    producer = await kafka_producer()

    asyncio.create_task(get_data(receive_queue=receive_queue))
    asyncio.create_task(
        send_messages(topic="player", producer=producer, send_queue=send_queue)
    )

    while True:
        if receive_queue.empty():
            await asyncio.sleep(1)

        message = await receive_queue.get()
        await send_queue.put(message)
        receive_queue.task_done()


def get_players_to_scrape():
    asyncio.ensure_future(main())
