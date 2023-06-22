import asyncio
import json
from datetime import datetime

import aiokafka
import sqlalchemy
from pydantic import BaseModel

import config
from config import config

from . import queries
import logging
import sys
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)
APPCONFIG = config.AppConfig()


class Player(BaseModel):
    id: int
    name: str
    created_at: str
    updated_at: str | None
    possible_ban: int
    confirmed_ban: int
    confirmed_player: int
    label_id: int
    label_jagex: int


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


async def async_main(unique_ids: list = []):
    APPCONFIG = config.AppConfig()
    connection_string = f"mysql+pymysql://{APPCONFIG.SERVER_LOGIN}:{APPCONFIG.SERVER_PASSWORD}@{APPCONFIG.SERVER_ADDRESS}/{APPCONFIG.DATABASE}"

    # Execute the SQL query in batches of size 10,000
    batch_size: int = 5000
    offset: int = 0
    today = datetime.now().strftime("%Y-%m-%d")

    # indent hell
    while True:
        try:
            logger.info("Creating database engine")
            # Create an engine and establish the connection
            engine = sqlalchemy.create_engine(connection_string)
            with engine.connect() as connection:
                while True:
                    # Construct the SQL query with the batch size and offset
                    batch_sql: str = (
                        f"{queries.sql} LIMIT {batch_size} OFFSET {offset};"
                    )

                    # Create a SQLAlchemy text object from the batch SQL query
                    statement = sqlalchemy.text(batch_sql)

                    # Execute the batch SQL query
                    result = connection.execute(statement)

                    # Fetch the column names from the result
                    column_names = result.keys()
                    result = result.fetchall()

                    # Iterate over the result set and convert rows to dictionaries
                    rows = []
                    for row in result:
                        row = dict(zip(column_names, row))

                        if row["created_at"]:
                            row["created_at"] = row["created_at"].strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )

                        if row["updated_at"]:
                            if row["updated_at"].strftime("%Y-%m-%d") == today:
                                continue
                            row["updated_at"] = row["updated_at"].strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )

                        row = Player(**row)

                        if row.id not in unique_ids:
                            rows.append(row)
                            # Add unique IDs to the list
                            unique_ids.append(row.id)

                    if not rows:
                        continue

                    logger.debug(f"{len(unique_ids)=}, {offset=}")

                    # Send rows to Kafka
                    await send_rows_to_kafka(rows, kafka_topic="player")

                    # Increment the offset for the next batch
                    offset += batch_size

        except OperationalError as e:
            logger.error(f"exception {str(e)}")

            # reset offset
            offset = 0
            await asyncio.sleep(60)
            


def get_players_to_scrape():
    asyncio.ensure_future(async_main())
