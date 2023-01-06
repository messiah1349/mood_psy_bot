FROM python:3.10-slim-buster

ENV TZ=Asia/Yerevan

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENV MOOD_PSY_BOT_TOKEN=$MOOD_PSY_BOT_TOKEN
ENV PYTHONPATH=/code/

RUN python /code/db/tables.py

CMD ["python", "/code/main.py"]
