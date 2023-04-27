# Use the official Python base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Update and install dependencies
#RUN apt-get update \
# && apt-get install -y portaudio19-dev ffmpeg pulseaudio \
# && apt-get clean \
# && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy pyproject.toml and poetry.lock files
COPY pyproject.toml poetry.lock ./

# Install project dependencies
RUN poetry config virtualenvs.create false \
  && poetry install --only main --no-interaction --no-ansi

CMD ["poetry", "run", "python", "main.py"]
