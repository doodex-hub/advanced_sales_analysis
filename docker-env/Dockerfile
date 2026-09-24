# Diinstansiasi ulang untuk project migrasi 19.0->20.0 (2026-09-24), menggantikan Dockerfile 19.0
# (FROM odoo:19.0, masih ada di git: `git show migration/19.0:docker-env/Dockerfile`).
#
# TIDAK ADA image resmi odoo:20.0 di Docker Hub (knowledge/version-diffs/19-to-20.md, dicek terakhir
# 2026-09-22 oleh project pos-margin-sale). Jadi Odoo 20.0 dijalankan FROM SOURCE: checkout lokal
# D:\Kuncoro\doodex\repo\odoo20 (+ enterprise20) di-bind-mount read-only saat runtime, BUKAN di-copy
# ke image. Dockerfile ini disalin dari pos-margin-sale-migration-20/docker-env/Dockerfile.20
# (sudah terbukti jalan untuk G1/Tour test 20.0) supaya layer cache Docker bisa dipakai ulang.
#
# Python 3.12 karena odoo20/requirements.txt mem-pin paket ke `python_version >= '3.12'`.
# wkhtmltopdf sengaja tidak dipasang (modul tidak punya report PDF).
FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpq-dev \
    libffi-dev \
    postgresql-client \
    fonts-dejavu-core \
    fonts-freefont-ttf \
    fonts-font-awesome \
    fonts-roboto-unhinted \
    gsfonts \
    node-less \
    npm \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt = salinan persis odoo20/requirements.txt (build context tidak bisa menjangkau
# folder di luar docker-env/).
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Chrome headless + websocket-client untuk HttpCase.browser_js (tests/test_qa_browser.py).
RUN apt-get update && apt-get install -y --no-install-recommends gnupg \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir websocket-client

RUN useradd -m -d /home/odoo -s /bin/bash odoo
RUN mkdir -p /var/log/odoo /var/lib/odoo && chown odoo:odoo /var/log/odoo /var/lib/odoo

USER odoo
