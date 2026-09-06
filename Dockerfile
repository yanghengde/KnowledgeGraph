FROM node:22-bookworm-slim AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# msodbcsql18 keeps the Camstar SQL Server source connection usable in the image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl unixodbc \
    && curl -fsSLo /tmp/packages-microsoft-prod.deb \
        https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && rm /tmp/packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY . .
COPY --from=frontend-build /build/web/static/react /app/web/static/react

RUN mkdir -p /app/data /app/logs \
    && useradd --create-home --uid 10001 camstar \
    && chown -R camstar:camstar /app

USER camstar

EXPOSE 5050

CMD ["python", "-m", "uvicorn", "web.server:app", "--host", "0.0.0.0", "--port", "5050", "--workers", "1"]
