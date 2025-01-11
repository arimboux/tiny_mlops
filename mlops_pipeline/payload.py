from pydantic import BaseModel

class ImageRequest(BaseModel):
    image_url: str

class ProcessImages(BaseModel):
    images: list[str]
