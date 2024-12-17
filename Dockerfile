FROM python:3.10-slim

RUN mkdir /home/app

WORKDIR /home/app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY app/ .

EXPOSE 8080

CMD [ "uvicorn", "main:app", "--reload", "--host 0.0.0.0" ]