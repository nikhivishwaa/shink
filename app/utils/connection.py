from google.cloud import storage
from PIL import Image
import os
import io
from dotenv import load_dotenv

load_dotenv()

class Secrets:
    def __init__(self):
        self.BUCKET_NAME = os.getenv("BUCKET_NAME",'')
        self.PROJECT_ID = os.getenv("PROJECT_ID",'')
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY",'')
        self.FOLDER_NAME = os.getenv("FOLDER_NAME",'')

secrets = Secrets()


class Bucket:
    def __init__(self) -> None:
        self.client = storage.Client(project=secrets.PROJECT_ID)
        self.bucket = self.client.get_bucket(secrets.BUCKET_NAME)

    def load_image(self, blob):
        image_data = blob.download_as_bytes()
        image = Image.open(io.BytesIO(image_data))
        return image

class References:
    def __init__(self) -> None:
        self._bucket = Bucket()
        self.messages = ["Possible labels:"]
        self.ready = False

    def create_message(self):
        try:
            if self.ready:
                # return the reference if it is already loaded
                return self.messages
            
            # adding real images as class_0
            blobs = self._bucket.list_blobs(prefix=secrets.FOLDER_NAME+'/0/')
            for blob in blobs:
                if blob.path.endswith('.jpg'):
                    self.messages.append(self.load_image(blob))
            self.messages.append('label: class_0')

            # adding AI Generated images as class_1
            blobs = self._bucket.list_blobs(prefix=secrets.FOLDER_NAME+'/1/')
            for blob in blobs:
                if blob.path.endswith('.jpg'):
                    self.messages.append(self.load_image(blob))
            self.messages.append('label: class_1')
            self.ready = True
            print('References created successfully.')

            return self.messages

        except Exception as e:
            print(e)
            self.ready = False

class Input:
    def __init__(self) -> None:
        self.messages = ["Input images:"]
        self.ready = False

    def create_message(self,image):
        try: 
            img = Image.open(io.BytesIO(image))
            self.messages.append(img)
            self.messages.append('Please correctly classify all provided input images.')
            self.ready = True
            print('Input Image Added Successfully.')

            return self.messages

        except Exception as e:
            self.ready = False

context = References()
context.create_message()