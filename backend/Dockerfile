FROM python:3.12-slim
WORKDIR /srv
COPY backend/requirements.txt /srv/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend /srv/backend
COPY data /srv/data
WORKDIR /srv/backend
EXPOSE 5050
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-5050}"]
