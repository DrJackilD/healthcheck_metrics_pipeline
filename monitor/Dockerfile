FROM python:3.9-slim-buster

COPY requirements/common.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
WORKDIR /app
COPY run.py .
COPY ./monitor /app/monitor
COPY ./init /app/init
COPY schedule.yaml /app/schedule.yaml

CMD python run.py
