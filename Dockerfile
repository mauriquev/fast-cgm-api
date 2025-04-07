FROM python:3.12-alpine
WORKDIR /app
RUN apk update && apk upgrade xz-libs && rm -rf /var/cache/apk/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip
COPY main.py models.py database.py ./
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]