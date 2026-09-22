# Tampa Maids Cleaning — production image.
# No dependencies to install: the whole app is Python standard library.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    DATA_DIR=/var/data \
    TRUST_PROXY=1 \
    FORCE_HTTPS=1

WORKDIR /app
COPY . /app

# /var/data must be a mounted persistent disk, or the database is wiped on
# every deploy. See DEPLOY.md.
RUN mkdir -p /var/data

EXPOSE 8000

# Create the owner account on first boot (no demo data), then serve.
CMD ["sh", "-c", "python3 server/seed.py && exec python3 server/app.py"]
