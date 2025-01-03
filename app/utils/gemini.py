import google.generativeai as genai
from utils.prompts import system_prompt, prompt
from utils.connection import secrets
import json


genai.configure(api_key=secrets.GEMINI_API_KEY)

generation_config = {
  "temperature": 1,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
}
classification_model = genai.GenerativeModel(
    "gemini-2.0-flash-exp", 
    system_instruction=system_prompt(), 
    generation_config=generation_config
)


async def classification(image):
    response = classification_model.generate_content(
        contents=prompt(image=image)
    )
    response_json = json.loads(response.text)
    print(response_json)
    result = response_json['output'][0]
    del result['image_id']
    result['class'] = 'Real' if result['label'].endswith('0') else 'AI Generated'
    result['model'] = 'gemini flash 2.0'
    del result['label']
    return result