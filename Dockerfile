FROM python:3.10-alpine

RUN mkdir /home/app

WORKDIR /home/app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

# RUN pip install numpy pillow fastapi uvicorn python-multipart opencv-python tensorflow

COPY app/ .

EXPOSE 8080

CMD [ "uvicorn", "main:app", "--reload", "--host 0.0.0.0" ]