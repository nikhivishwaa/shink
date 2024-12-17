# way to upload the image : endpoint
# predict the image class i.e. Real or AI Generated
# show the result

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import numpy as np
import tensorflow as tf
from helper import preprocess_image

app = FastAPI()

origins = [
    "http://0.0.0.0:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL = tf.keras.models.load_model("saved_models/2/ai_vs_real_model-v2.h5")

CLASS_NAMES = ["Real", "AI Generated"]

@app.get("/ping")
async def ping():
    return "Hello, I am alive"


@app.post("/predict")
async def predict(
    file: UploadFile = File(...)
):
    image = preprocess_image(await file.read())
    img_batch = np.expand_dims(image, 0)
    
    predictions = MODEL.predict(img_batch)

    predicted_class = CLASS_NAMES[np.argmax(predictions[0])]
    confidence = np.max(predictions[0])
    return {
        'class': predicted_class,
        'confidence': float(confidence),
        'model': 'v2'
    }

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8080)