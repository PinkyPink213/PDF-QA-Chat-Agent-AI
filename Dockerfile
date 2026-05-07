FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set working directory
WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip

COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

RUN pip install --no-cache-dir gradio

EXPOSE 7860

ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["sh", "-c", "python3 gradio_app.py"]