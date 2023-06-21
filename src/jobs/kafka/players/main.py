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


async def async_main():
    APPCONFIG = config.AppConfig()
    connection_string = f"mysql+pymysql://{APPCONFIG.SERVER_LOGIN}:{APPCONFIG.SERVER_PASSWORD}@{APPCONFIG.SERVER_ADDRESS}/{APPCONFIG.DATABASE}"

    # Create an engine
    engine = sqlalchemy.create_engine(connection_string)

    # Execute the SQL query in batches of size 10,000
    batch_size: int = 5000
    offset: int = 0
    unique_ids = []
    today = datetime.now().strftime("%Y-%m-%d")

    with engine.connect() as connection:
        while True:
            # Construct the SQL query with the batch size and offset
            batch_sql: str = f"{queries.sql} LIMIT {batch_size} OFFSET {offset};"

            # Create a SQLAlchemy text object from the batch SQL query
            statement = sqlalchemy.text(batch_sql)

            # Execute the batch SQL query and fetch all rows
            result = connection.execute(statement)

            # Fetch the column names from the result
            column_names = result.keys()

            # Convert rows to dictionaries
            rows = [dict(zip(column_names, row)) for row in result.fetchall()]

            # If no more rows are fetched, break out of the loop
            if len(rows) == 0:
                await asyncio.sleep(300)
                continue

            if datetime.now().strftime("%Y-%m-%d") > today:
                logger.debug("new day")
                today = datetime.now().strftime("%Y-%m-%d")
                unique_ids = []

            _rows = list()
            for row in rows:
                # parse datetime to string
                if row["created_at"]:
                    row["created_at"] = row["created_at"].strftime("%Y-%m-%d %H:%M:%S")

                # parse datetime to string
                if row["updated_at"]:
                    # ignore players that we have updated
                    
                    if row["updated_at"].strftime("%Y-%m-%d") == today:
                        continue
                    row["updated_at"] = row["updated_at"].strftime("%Y-%m-%d %H:%M:%S")

                row = Player(**row)

                if row.id not in unique_ids:
                    _rows.append(row)
                    unique_ids.append(row.id)
                    # Add unique IDs to the list

            logger.debug(f"{len(unique_ids)=}, {offset=}")

            # Send rows to Kafka
            await send_rows_to_kafka(_rows, kafka_topic="player")

            # Increment the offset for the next batch
            offset += batch_size


def get_players_to_scrape():
    asyncio.ensure_future(async_main())
