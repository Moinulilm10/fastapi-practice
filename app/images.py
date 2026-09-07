"""Module for configuring the ImageKit client."""

import os

from dotenv import load_dotenv
from imagekitio import ImageKit

load_dotenv()

image_kit = ImageKit(
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
    # public_key=os.getenv("IMAGEKIT_PUBLIC_KEY"),
    # url_endpoint=os.getenv("IMAGEKIT_URL"),
)
