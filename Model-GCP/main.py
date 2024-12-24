import tensorflow as tf
from PIL import Image
import numpy as np
from flask import jsonify
import io
import os


CLASS_NAMES = ["Real", "AI Generated"]
MODEL = None

def load_model():
    if MODEL is None:
        print("Loading Model ................")
        globals()['MODEL']= tf.keras.models.load_model("model/ai_vs_real_model-v2.h5")
        print("Done ................")

def model_classifier(img_pil):
    """
    ### Model classifier
        >> step 1: preprocessing
            -    Resize an image while maintaining aspect ratio and filling the background
                 with nearby pixel values using nearest-neighbor interpolation.
            -    Normalize the image pixel values to the range [0, 1].
            -    Expand the dimensions (create batch)

        >> step 2: Prediction
            -    Feed image batch to model for class prediction
        >> step 3: Formatted output
            -    Return the predicted class and confidence
    Args:
        image -> PIL.Image()

    Returns:
        output -> None | {}
    """

    try:
        SIZE = (224, 224)

        # Get original dimensions
        w, h = img_pil.size

        # Calculate scaling factor
        scale = min(SIZE[1] / h, SIZE[0] / w)  # Fit within target size
        new_w, new_h = int(w * scale), int(h * scale)  # New dimensions

        # Resize the image while maintaining the aspect ratio
        resized_img = img_pil.resize((new_w, new_h), Image.NEAREST)

        # Create a canvas with the target size
        canvas =img_pil.resize(SIZE, Image.NEAREST)
    
        # Calculate where to place the resized image on the canvas
        top = (SIZE[1] - new_h) // 2
        left = (SIZE[0] - new_w) // 2

        # Paste the resized image onto the canvas
        canvas.paste(resized_img, (left, top))

        # Normalizing the resized image
        image_np = np.array(canvas) / 255

        img_batch = np.expand_dims(image_np, 0)

        print("preprocessing is completed")
        
        predictions = MODEL.predict(img_batch)
        predicted_class = CLASS_NAMES[np.argmax(predictions[0])]
        confidence = round(np.max(predictions[0])*100, 2)
        
        result = {
            'class': predicted_class,
            'confidence': float(confidence),
            'model': 'shink vistro v2'
        }

        return result

    except Exception as e:
        print(f"Failed to make Prediction : {e}")
        return None


def handle_input(image):
    try:
        image_data = io.BytesIO(image)
        image_pil = Image.open(image_data)
        return image_pil

    except Exception as e:
        print("Unable to load Image:",e)
        return None


def predict(request):
    load_model()
    try:
        # getting image from files
        image = request.files.get('image')
        if image is None:
            print("image is None")
            raise ValueError("Missing 'image' in request body.")
        
        # Process the input image
        image = image.read()
        image_pil = handle_input(image)
        if image_pil is None:
            print("image cant be opened")
            res = {"error": "Invalid or unsupported image format."}
            return jsonify(res), 400

        # Run classification
        result = model_classifier(image_pil)
        if result is None:
            print("Prediction failed")
            return jsonify({"error": "Classification failed."}), 500

        return jsonify(result), 200

    except Exception as e:
        print(f"Failed to classify image: {e}")
        res = {"error": str(e)}
        return jsonify(res), 500
