# Project description

This project aims to build a small-scale MLOps pipeline that receive a batch of images and run them into an image processing pipeline using external APIs. It should use Kafka as a dataflow and event manager to guide the pipeline steps.

It exposes an API endpoint `process_image` receiving a list of images and sending their URL into a Kafka broker. A consumer `pipeline.py` will read these events and trigger a call to an endpoint lauching the image processing step. Once this step is done, it sends back an event to the broker with the modified image (here an URL the modified image) so the consumer (`pipeline.py`) can decide which are the next steps.

## Local Development Setup

### Prerequisites
- Docker and docker compose
- Python 3.9+
- Poetry

### Building and Running Locally

I struggled with bundling everything into one docker container so I fallback to launching the 3 parts independently.

1. Create poetry environment:
```bash
poetry install
```

2. Launch the kafka broker:
```bash
docker compose up
```

The kafka broker should be running and accessible through port 9092

3. Launch the consumer (pipeline.py):
```bash
poetry shell
python mlops_pipeline/pipeline.py 
```

4. Export your fal_api key into FAL_KEY:
```bash
export FAL_KEY=XXX
```


4. Launch uvicorn server to expose the API endpoint on port 8000 (app.py):
```bash
poetry run uvicorn mlops_pipeline.app:app --host "0.0.0.0" --port 8000
```

5. You should now be able to request the process_image endpoint with:
```bash
curl -X POST 'http://localhost:8000/process-image' \
-H 'Content-Type: application/json' \
-d '{
    "images": [
        "https://i.ibb.co/RNKnqMh/algea.jpg",
        "https://i.ibb.co/0cCYDLF/burger.jpg",
        "https://i.ibb.co/WckBR2q/cake.jpg",
        "https://i.ibb.co/tbKz4MR/chicken.jpg",
        "https://i.ibb.co/TPyrZ9h/chorizzo.jpg",
        "https://i.ibb.co/ZmgW665/coffee.jpg",
        "https://i.ibb.co/ZN0gX1q/fries.jpg",
        "https://i.ibb.co/XD0V1Yh/nuggets.jpg",
        "https://i.ibb.co/ssyh7fF/panini.jpg",
        "https://i.ibb.co/m6PD5Fg/pasta.jpg",
        "https://i.ibb.co/1TQ74mB/sashimi.jpg",
        "https://i.ibb.co/frsXCb3/shrimps.jpg",
        "https://i.ibb.co/XSkGXnw/sushi.jpg",
        "https://i.ibb.co/VVDBKVh/tiramisu.jpg"
    ]
}'
```

This will return a response indicating that the images are being processed. When finishing the last processing step (upscale) you will get a log with a link to check the image result.

###  Checking concurency

For now you can check concurrency by looking at the server logs that shows that multiple API calls are made concurently.

```bash
INFO:mlops_pipeline.app:remove background
INFO:mlops_pipeline.app:remove background
INFO:mlops_pipeline.app:remove background
INFO:mlops_pipeline.app:remove background
INFO:mlops_pipeline.app:remove background
INFO:     127.0.0.1:49620 - "POST /remove-background HTTP/1.1" 200 OK
INFO:mlops_pipeline.app:remove background
INFO:     127.0.0.1:49630 - "POST /remove-background HTTP/1.1" 200 OK
INFO:mlops_pipeline.app:remove background
INFO:     127.0.0.1:49626 - "POST /remove-background HTTP/1.1" 200 OK
```
 5 remove background tasks are launched together, once one is finised, a new one is launched.

 ###  Checking events handling

You can check the `pipeline.py` logs to verify events handling

 ###  TODO


- [ ] Bundled everything into a single docker container
- [ ] Improve logging
- [ ] Improve error management
- [ ] Add tests

