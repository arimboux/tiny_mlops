import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

import aiohttp
from kafka import KafkaConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataProcessingService:
    def __init__(self, bootstrap_servers: list, topics: str, concurrent_limit: int = 5):
        self.consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            group_id="data_processing_group",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )

        # Create semaphores for each task type
        self.semaphores = {
            "remove-background-start": asyncio.Semaphore(concurrent_limit),
            "replace-background-start": asyncio.Semaphore(concurrent_limit),
            "upscale-start": asyncio.Semaphore(concurrent_limit),
        }

        self.topic_handlers = {
            "remove-background-start": self.remove_background,
            "replace-background-start": self.replace_background,
            "upscale-start": self.upscale,
        }

        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def setup(self):
        self.session = aiohttp.ClientSession()

    async def cleanup(self):
        if self.session:
            await self.session.close()
        self.consumer.close()
        self.executor.shutdown()

    async def remove_background(self, message):
        async with self.semaphores["remove-background-start"]:
            logger.info("Calling remove background")
            await self.call_external_api(
                "http://localhost:8000/remove-background", {"image_url": message}
            )

    async def replace_background(self, message):
        async with self.semaphores["replace-background-start"]:
            logger.info("Calling replace background")
            await self.call_external_api(
                "http://localhost:8000/replace-background",
                {
                    "image_url": message,
                    "prompt": "marble surface",
                },
            )

    async def upscale(self, message):
        async with self.semaphores["upscale-start"]:
            logger.info("Calling upscale")
            await self.call_external_api(
                "http://localhost:8000/upscale-image",
                {
                    "image_url": message,
                },
            )

    async def call_external_api(self, url: str, data: Dict):
        try:
            async with self.session.post(url, json=data) as response:
                await response.text()
                if response.status >= 400:
                    logger.error(f"API call failed with status {response.status}")
                    raise Exception(f"API call failed: {response.status}")
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            raise

    async def process_message(self, message):
        logger.info(f"Processing message from topic {message.topic}: {message.value}")

        handler = self.topic_handlers.get(message.topic)
        if handler:
            try:
                await handler(message.value)
            except Exception as e:
                logger.error(f"Handler error for topic {message.topic}: {str(e)}")
        else:
            logger.warning(f"No handler defined for topic: {message.topic}")

    async def consume(self):
        try:
            message_batch = []
            while True:
                messages = await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    lambda: list(self.consumer.poll(timeout_ms=1000).values()),
                )

                for partition_messages in messages:
                    for message in partition_messages:
                        message_batch.append(message)

                if message_batch:
                    await asyncio.gather(
                        *[self.process_message(message) for message in message_batch]
                    )
                    message_batch = []

                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Consumer error: {str(e)}")

    async def run(self):
        logger.info("Starting data processing service...")
        await self.setup()
        try:
            await self.consume()
        finally:
            await self.cleanup()


if __name__ == "__main__":
    service = DataProcessingService(
        bootstrap_servers=["localhost:9092"],
        topics=["remove-background-start", "replace-background-start", "upscale-start"],
        concurrent_limit=5,  # Set the concurrent limit for each task type
    )

    asyncio.run(service.run())
