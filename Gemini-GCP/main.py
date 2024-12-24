import google.generativeai as genai
from PIL import Image
import requests
import json
import os
import io
from flask import jsonify

CLASSIFIER_SYSTEM_PROMPT = """You are a Image Moderator.

Your task is to classify images as class_0 and class_1. where AI Generated Image is labeled as class_1 and Real Image is labeled as class_0

Provide your output as a JSON object using this format:

{
    "number_of_labeled_images": <integer>,
    "output": [
        {
            "image_id": <image id, integer, starts at 0>,
            "confidence": <number between 0.0 and 100.0, the higher the more confident, float>,
            "label": <label of the correct class, string>
        }, 
        ...
    ]
}

## Guidelines

- ALWAYS produce valid JSON.
- Generate ONLY a single prediction per input image.
- The `number_of_labeled_images` MUST be the same as the number of input images.

This is an example of a valid output:
```
{
  "number_of_labeled_images": 5,
  "output": [
      {
        "image_id": 0,
        "confidence": 100.0,
        "correct_label": "class_0"
      },
      {
        "image_id": 1,
        "confidence": 90.0,
        "correct_label": "class_1"
      },
      {
        "image_id": 2,
        "confidence": 45.0,
        "correct_label": "class_1"
      },
      {
        "image_id": 3,
        "confidence": 87.6,
        "correct_label": "class_0"
      },
      {
        "image_id": 4,
        "confidence": 65.9,
        "correct_label": "class_0"
      }
  ]
}
```
""".strip()


BASE_PATH = os.path.dirname(os.path.abspath(__file__))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FALLBACK_URL = os.getenv("FALLBACK_URL")

if not GEMINI_API_KEY or not FALLBACK_URL:
    raise ValueError("Environment variables GEMINI_API_KEY and FALLBACK_URL must be set.")

class References:
    def __init__(self) -> None:
        self.messages = ["Possible labels:"]
        self.ready = False

    def load_image(self, img_src):
        img = Image.open(img_src)
        return img

    def create_message(self):
        try:
            if self.ready:
                # return the reference if it is already loaded
                print("Reference already exist")
                return self.messages
            
            # adding real images as class_0
            REAL_BASE_PATH = f'{BASE_PATH}/images/0/'
            for fname in os.listdir(REAL_BASE_PATH):
                src = f"{REAL_BASE_PATH}{fname}"
                self.messages.append(self.load_image(src))
            self.messages.append('label: class_0')

            # adding AI Generated images as class_1
            AI_GEN_BASE_PATH = f'{BASE_PATH}/images/1/'
            for fname in os.listdir(AI_GEN_BASE_PATH):
                src = f"{AI_GEN_BASE_PATH}{fname}"
                self.messages.append(self.load_image(src))
            self.messages.append('label: class_1')
            self.ready = True
            print('References created successfully.')

            return self.messages

        except Exception as e:
            print(f"Failed to create reference : {e}")
            self.ready = False



context = References()
CONTEXT_MESSAGE = context.create_message()
INPUT_MESSAGE = ["Input images:", None, 'Please correctly classify provided input images.']

def handle_input(image):
    try:
        message = INPUT_MESSAGE.copy()
        image_data = io.BytesIO(image)
        message[1] = Image.open(image_data)
        print('Input Image Added Successfully.')
        return message

    except Exception as e:
        print("Unable to load Image:",e)
        return None

def prompt(input_message):
    return CONTEXT_MESSAGE + input_message
    

genai.configure(api_key=GEMINI_API_KEY)

generation_config = {
  "temperature": 1,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}
classification_model = genai.GenerativeModel(
    "gemini-2.0-flash-exp", 
    system_instruction=CLASSIFIER_SYSTEM_PROMPT, 
    generation_config=generation_config
)

def gemini_classifier(input_message):  
    CONTEXT_MESSAGE = context.create_message()
    try:
        response = classification_model.generate_content(
            contents=prompt(input_message)
        )
        response_json = json.loads(response.text)
        print(response_json)
        result = response_json['output'][-1]
        del result['image_id']
        result['class'] = 'Real' if result['label'].endswith('0') else 'AI Generated'
        result['model'] = 'gemini flash 2.0'
        del result['label']

        return result
    except Exception as e:
        print(f"Gemini Connection error: {e}")
        return None

def fallback_option(image_data, mimetype):
    try:
        r = requests.post(
            FALLBACK_URL,
            files={'image': ('image.jpg', io.BytesIO(image_data), mimetype)}
        )
        if r.status_code == 200:
            result = json.loads(r.text)
            print(f"Fallback Triggered : {result}")
            return result
    except Exception as e:
        print(f"Failed to fallback to external service: {e}")
        return None        

def classification(request):
    try:
        image = request.files.get('image')
        if image is None:
            raise ValueError("Missing 'image' in request body.")
        
        # Process the input image
        image_data = image.read()
        input_message = handle_input(image_data)
        if input_message is None:
            res = {"error": "Invalid or unsupported image format."}
            return jsonify(res), 400

        # Run classification
        result = gemini_classifier(input_message)
        if result is None:
            result = fallback_option(image_data, image.mimetype)
            if result:
                return jsonify(result), 200
            else:
                return jsonify({"error": "Classification failed."}), 500

        return jsonify(result), 200

    except Exception as e:
        print(f"Failed to classify image: {e}")
        res = {"error": str(e)}
        return jsonify(res), 500