FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir pyTelegramBotAPI python-dotenv openai

CMD ["python", "main.py"]
