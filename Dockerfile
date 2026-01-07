FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY telegram_whisper_bot.py .

# Create non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Environment variables with defaults
ENV TMP_PATH=/tmp/whisper_bot
ENV WHISPER_MODEL=base
ENV WHISPER_THREADS=4

# Run the bot
CMD ["python", "telegram_whisper_bot.py"]
