FROM python:3.9-slim-buster

COPY requirements/common.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
WORKDIR /app
COPY . .

CMD python run.py
