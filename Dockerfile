# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8096 \
    TZ=Asia/Taipei

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential default-libmysqlclient-dev tzdata \
 && rm -rf /var/lib/apt/lists/*

# 建議提供 requirements.txt；這行會用快取
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# 再複製程式碼
COPY . /app

EXPOSE 8096

# 讓 Python 直接能 import 專案頂層模組（app 是 flat layout）
ENV PYTHONPATH=/app

CMD ["sh", "-lc", "\
  exec gunicorn --config gunicorn.conf.py -w ${GUNICORN_WORKERS:-2} --timeout ${GUNICORN_TIMEOUT:-30} \
       -b 0.0.0.0:${PORT:-8096} wsgi:app"]
