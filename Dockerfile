FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user

ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

COPY --chown=user requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

ENV PYTHONPATH=/app

ENV GRADIO_SERVER_NAME="0.0.0.0"

EXPOSE 7860
EXPOSE 8000