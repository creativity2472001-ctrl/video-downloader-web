FROM python:3.11-slim

# تثبيت FFmpeg و Node.js (ضروري ليوتيوب)
RUN apt-get update && apt-get install -y ffmpeg nodejs npm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
