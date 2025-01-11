import asyncio
import json
import logging

from fastapi import FastAPI, HTTPException

from mlops_pipeline.payload import ImageRequest, ProcessImages
from mlops_pipeline.producer import KafkaProducerAsync
from mlops_pipeline.services import remove_background, replace_background, upscale_image

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)
logging.getLogger(__name__).setLevel(logging.INFO)

app = FastAPI()

producer = KafkaProducerAsync(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


@app.post("/remove-background")
async def remove_background_endpoint(request: ImageRequest):
    logger.info("remove background")
    try:
        result = await remove_background(request)
        await producer.send_async(
            "replace-background-start", result["result"]["image"]["url"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/replace-background")
async def replace_background_endpoint(request: ImageRequest):
    logger.info("replace background")
    try:
        result = await replace_background(request)
        await producer.send_async("upscale-start", result["result"]["images"][0]["url"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upscale-image")
async def upscale_image_endpoint(request: ImageRequest):
    logger.info("upscale image")
    try:
        result = await upscale_image(request)
        logger.info(result["result"]["image"]["url"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process-image")
async def process_image(request: ProcessImages):
    try:
        tasks = [
            producer.send_async("remove-background-start", image)
            for image in request.images
        ]

        await asyncio.gather(*tasks)

        return {
            "status": "success",
            "message": f"Successfully queued {len(request.images)} images",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
