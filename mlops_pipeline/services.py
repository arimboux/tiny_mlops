import fal_client
from fastapi import HTTPException
from mlops_pipeline.payload import ImageRequest
import asyncio
from typing import Any


async def process_image_with_model(
    image_url: str, model_endpoint: str, additional_args: dict = None
) -> dict[str, Any]:
    logs = []

    def on_queue_update(update):
        nonlocal logs
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                logs.append({"message": log["message"]})

    arguments = {"image_url": image_url}
    if additional_args:
        arguments.update(additional_args)

    # Make fal_client.subscribe non-blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: fal_client.subscribe(
            model_endpoint,
            arguments=arguments,
            with_logs=True,
            on_queue_update=on_queue_update,
        ),
    )

    return {"result": result, "logs": logs}


async def remove_background(request: ImageRequest) -> dict[str, str]:
    try:
        result = await process_image_with_model(request.image_url, "fal-ai/birefnet/v2")
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def replace_background(request: ImageRequest) -> dict[str, str]:
    try:
        result = await process_image_with_model(
            request.image_url,
            "fal-ai/bria/background/replace",
            {"prompt": "marble surface"},
        )
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def upscale_image(request: ImageRequest) -> dict[str, str]:
    try:
        result = await process_image_with_model(request.image_url, "fal-ai/aura-sr")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
