FROM python:3.10-slim-buster

ENV TZ=Europe/Helsinki

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENV MOOD_PSY_BOT_TOKEN=$MOOD_PSY_BOT_TOKEN
ENV PYTHONPATH=/code/

CMD ["python", "/code/main.py"]
