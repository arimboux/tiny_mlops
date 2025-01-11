import asyncio
from functools import partial

from kafka import KafkaProducer


class KafkaProducerAsync(KafkaProducer):
    def __init__(self, **configs):
        super().__init__(**configs)

    async def send_async(self, topic: str, message: str):
        loop = asyncio.get_event_loop()
        try:
            # Run the synchronous producer.send in a thread pool
            future = await loop.run_in_executor(
                None, partial(self.send, topic, message)
            )
            # Wait for the result
            await loop.run_in_executor(None, future.get, 10)
        except Exception as e:
            print(f"Error sending message: {e}")
