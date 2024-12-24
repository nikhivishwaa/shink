import google.generativeai as genai
from PIL import Image
import requests
import json
import cgi
import os
import io


BASE_PATH = os.path.dirname(os.path.abspath(__file__))

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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY",'')

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
            print(e)
            self.ready = False


def create_input_message(image):
    try:
        messages = ["Input images:"]
        image_data = io.BytesIO(image)
        img = Image.open(image_data)
        messages.append(img)
        messages.append('Please correctly classify all provided input images.')
        print('Input Image Added Successfully.')

        return messages

    except Exception as e:
        print(e)

context = References()
context.create_message()


def prompt(image):
    context_images_message = context.create_message()
    input_images_message = create_input_message(image=image)

    context_images_message += input_images_message
    return context_images_message
    

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




def get_formdata(body, headers):
    fp = io.BytesIO(body.encode('utf-8'))
    pdict = cgi.parse_header(headers['Content-Type'])[1]
    if 'boundary' in pdict:
        pdict['boundary'] = pdict['boundary'].encode('utf-8')
    pdict['CONTENT-LENGTH'] = len(body)
    form_data = cgi.parse_multipart(fp, pdict)
    return form_data

def gemini_classifier(image):
    response = classification_model.generate_content(
        contents=prompt(image=image)
    )
    response_json = json.loads(response.text)
    print(response_json)
    result = response_json['output'][-1]
    del result['image_id']
    result['class'] = 'Real' if result['label'].endswith('0') else 'AI Generated'
    result['model'] = 'gemini flash 2.0'
    del result['label']

    return result

def lambda_handler(event, context):
    data = get_formdata(event['body'], event['headers'])
    try:
        image = io.BytesIO(data['image'][0])
    except Exception as e:
        res = {
            "statusCode": 400,
            "body": json.dumps({"error": "image is not found inside the form data"})
        }

    try:
        result = gemini_classifier(image)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(result)
        }
    except Exception as e:
        res = {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }