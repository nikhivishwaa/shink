from io import BytesIO
from PIL import Image
import cv2
import numpy as np


def read_file_as_image(data) -> np.ndarray:
    image = np.array(Image.open(BytesIO(data)))
    return image


def preprocess_image(image, output_size=(224, 224)):
    """
    Resize an image while maintaining aspect ratio and filling the background
    with nearby pixel values using nearest-neighbor interpolation.

    Args:
        image (bytes): byte data of image.
        output_size (tuple): Target size as (width, height).

    Returns:
        Canvas with resized image and filled background.
    """
    # Load the image
    img = read_file_as_image(data=image)
    if img is None:
        raise ValueError(f"Unable to load image from {image}")

    print(img.shape)
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Get original dimensions
    h, w, c = img.shape

    # Calculate scaling factor
    scale = min(output_size[1] / h, output_size[0] / w)  # Fit within target size
    new_w, new_h = int(w * scale), int(h * scale)  # New dimensions

    # Resize the image while maintaining the aspect ratio
    resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_NEAREST)

    # Create a blank canvas with the target size and fill it with the nearest pixels
    canvas = cv2.resize(resized_img, output_size, interpolation=cv2.INTER_NEAREST)

    # Calculate where to place the resized image on the canvas
    top = (output_size[1] - new_h) // 2
    left = (output_size[0] - new_w) // 2

    # Overlay the resized image onto the canvas
    canvas[top:top + new_h, left:left + new_w] = resized_img
    return canvas