FROM python:3.10-alpine

EXPOSE 8000

RUN mkdir /home/app

WORKDIR /home/app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY app/ .

CMD [ "uvicorn", "main:app", "--reload", "--host 0.0.0.0" ]