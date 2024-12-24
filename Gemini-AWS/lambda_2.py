import google.generativeai as genai
from PIL import Image
import requests
import json
import base64
import os
import io


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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BUCKET_URL = os.getenv("BUCKET_URL")
if not GEMINI_API_KEY or not BUCKET_URL:
    raise ValueError("Environment variables GEMINI_API_KEY and BUCKET_URL must be set.")


class References:
    def __init__(self) -> None:
        self.messages = ["Possible labels:"]
        self.ready = False

    def load_image(self, img_src):
        r = requests.get(img_src, stream=True)
        if r.status_code == 200:
            img = Image.open(io.BytesIO(r.content))
            return img

    def create_message(self):
        try:
            if self.ready:
                print('References created successfully.')
                # return the reference if it is already loaded
                return self.messages
            
            # adding real images as class_0
            for i in range(1,12):
                src = f"{BUCKET_URL}{i}.jpg"
                self.messages.append(self.load_image(src))
            self.messages.append('label: class_0')

            # adding AI Generated images as class_1
            for i in range(12,23):
                src = f"{BUCKET_URL}{i}.jpg"
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


def handle_input(base64_string_):
    try:
        aux_path = '/tmp/tmp.jpg'
        with open(aux_path, "wb") as f:
            f.write(base64.b64decode(base64_string_))

        INPUT_MESSAGE[1] = Image.open(aux_path)
        print(INPUT_MESSAGE)
        return INPUT_MESSAGE[1]
    except Exception as e:
        print("Unable to load Image:",e)
        return None

def prompt():
    return CONTEXT_MESSAGE + INPUT_MESSAGE

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

def gemini_classifier():  
    CONTEXT_MESSAGE = context.create_message()
    try:
        print(classification_model)
        response = classification_model.generate_content(
            contents=prompt()
        )
        print(response)
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


def lambda_handler(event, context):
    try:
        # Validate input
        body = json.loads(event.get('body', '{}'))
        image = body.get('image')
        if not image:
            raise ValueError("Missing 'image' in request body.")

        # Process the input image
        if handle_input(image) is None:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Invalid or unsupported image format."})
            }

        # Run classification
        result = gemini_classifier()
        if result is None:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Classification failed."})
            }

        # Return successful response
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result)
        }
    except Exception as e:
        # Handle uncaught exceptions
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Internal server error: {str(e)}"})
        }