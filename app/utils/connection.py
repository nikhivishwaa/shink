from google.cloud import storage
import os

class Bucket:
    def __init__(self) -> None:
        self.client = storage.Client()
        self.bucket_name = os.environ["BUCKET_NAME"]
        self.bucket = self.client.bucket(self.bucket_name)

    # define function that uploads a file from the bucket
    def upload_file(self, source, destination): 
        blob = self.bucket.blob(destination)
        blob.upload_from_filename(source)

        return True